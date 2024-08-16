from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import pandas as pd
from datetime import datetime, timedelta
import configparser
from bs4 import BeautifulSoup
import psycopg2
from sqlalchemy import create_engine



config = configparser.ConfigParser() # Initialize the parser
config.read('config.ini') # Read the configuration file
email = config['Credentials']['email']
password = config['Credentials']['password']
user = config['database']['user']
heslo = config['database']['password']

login_url = 'https://cs.boardgamearena.com/account' 
target_url_ukoncene_hry = 'https://boardgamearena.com/gamestats?player=93282695&opponent_id=0&finished=1' 
vystup = 'aktualizace/vsechny_ukoncene_hry__zdrojovy_kod_stranky2.txt'
aktualizovany_seznam_ukoncenych_her = "aktualizace/ukoncene_hry2.csv"
ukoncene_hry_vse_sql = "SELECT game_date FROM ukoncene_hry"
ukonc_hry_aktual_table = "ukoncene_hry_aktualizace"


driver_path = '/home/pavlina/Stažené/chromedriver-linux64/chromedriver-linux64/chromedriver'  
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.add_argument("--window-size=1920x1080")  # Set the window size
service = Service(executable_path=driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)


def get_target_date_from_db(dotaz, engine):
    print("Reading target date from PostgreSQL database...")
 
    #engine = create_engine(f'postgresql+psycopg2://{user}:{heslo}@{"localhost"}:{5432}/{"bga"}')
    query = dotaz
    df = pd.read_sql(query, engine)
    
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    most_recent_date = df['game_date'].max()
    target_date = (most_recent_date - timedelta(days=1)).strftime('%m/%d/%Y')
    print(f"Target date determined: {target_date}")
    return target_date


def login(driver, login_url, email, password):
    print("Logging in...")

    driver.get(login_url)
    email_field = driver.find_element(By.NAME, 'email')  
    password_field = driver.find_element(By.NAME, 'password')  
    email_field.send_keys(email)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    WebDriverWait(driver, 20).until(EC.url_changes(login_url))

    print("Login successful.")


def navigate_to_target_page(driver, target_url_ukoncene_hry):
    print("Navigating to target page...")

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(target_url_ukoncene_hry)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    print("Reached target page.")


def handle_cookie_consent(driver):
    print("Handling cookie consent if present...")
    try:
        cookie_consent_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="dialog"] .cc-dismiss'))
        )
        cookie_consent_button.click()
        print("Cookie consent handled.")
    except (TimeoutException, NoSuchElementException):
        print("No cookie consent dialog present.")


# def check_for_date_and_save_source(driver, target_date, vystup):
#     print("Checking for target date on the page...")
#     while True:
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         try:
#             see_more_button = WebDriverWait(driver, 10).until(
#                 EC.element_to_be_clickable((By.ID, 'see_more_tables'))
#             )
#             see_more_button.click()
#             time.sleep(2)
#             WebDriverWait(driver, 10).until(
#                 EC.presence_of_all_elements_located((By.XPATH, '//table//tr'))
#             )
#             rows = driver.find_elements(By.XPATH, '//table//tr')
#             for row in rows:
#                 if target_date in row.text:
#                     with open(vystup, 'w', encoding='utf-8') as file:
#                         file.write(driver.page_source)
#                     print("Source code saved.")
#                     return True
#         except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
#             print("Encountered an issue while scrolling or clicking 'see more'.")
#             break
#     return False 

def check_for_date_and_save_source(driver, target_date, vystup):
    def date_in_page(date, timeout=30):
        end_time = time.time() + timeout
        while time.time() < end_time:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                see_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, 'see_more_tables'))
                )
                see_more_button.click()
                time.sleep(5)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//table//tr'))
                )
                rows = driver.find_elements(By.XPATH, '//table//tr')
                for row in rows:
                    if date in row.text:
                        with open(vystup, 'w', encoding='utf-8') as file:
                            file.write(driver.page_source)
                        print("Source code saved.")
                        return True
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                print("Encountered an issue while scrolling or clicking 'see more'.")
                return False
        return False
    
    print("Checking for target date on the page...")
    
    # Try to find the target date within the specified timeout
    if date_in_page(target_date):
        return True

    # If not found, adjust the date to target_date - 1 day and try again
    print("Target date not found. Trying the previous day...")
    previous_date = (datetime.strptime(target_date, '%m/%d/%Y') - timedelta(days=1)).strftime('%m/%d/%Y')
    if date_in_page(previous_date):
        return True
    
    return False

######################################################################################
#extracting    

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_rows(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.find_all('tr')

def extract_info(row):
    game_info = row.find('a', class_='table_name gamename')
    game_number = game_info['href'].split('=')[-1] if game_info else 'N/A'
    game_name = game_info.text.strip() if game_info else 'N/A'
    
    game_number2_tag = row.find('a', class_='bga-link smalltext')
    game_number2 = game_number2_tag.text.strip() if game_number2_tag else 'N/A'
    
    game_date_divs = row.find_all('div', class_='smalltext')
    game_date = game_date_divs[0].text.strip() if len(game_date_divs) > 0 else 'N/A'
    game_time = game_date_divs[1].text.strip() if len(game_date_divs) > 1 else 'N/A'
    player_results = []
    for player_entry in row.find_all('div', class_='simple-score-entry'):
        rank_tag = player_entry.find('div', class_='gamerank')
        name_tag = player_entry.find('div', class_='name')
        score_tag = player_entry.find('div', class_='score')
        
        rank = rank_tag.text.strip() if rank_tag else 'N/A'
        name = name_tag.text.strip() if name_tag else 'N/A'
        score = score_tag.text.strip() if score_tag else 'N/A'
        
        player_results.append((rank, name, score))

    rank_div = row.find('span', class_='gamerank_value')
    rank = rank_div.text.strip() if rank_div else 'N/A'
    
    league_numbers = [div.text.strip() for div in row.find_all('div', class_='arena_label')]

    return {
        'game_info': (game_number, game_name, game_number2, game_date, game_time),
        'player_results': player_results,
        'rank': rank,
        'league_numbers': league_numbers
    }

def process_data(rows):
    data = []
    for row in rows:
        extracted_info = extract_info(row)
        game_number, game_name, game_number2, game_date, game_time = extracted_info['game_info']
        results = extracted_info['player_results']
        results_str = ', '.join([f"{rank}-{name}-{score}" for rank, name, score in results])
        rank = extracted_info['rank']
        league_numbers = extracted_info['league_numbers']
        league_numbers_str = ', '.join(league_numbers)
        data.append([game_number, game_name, game_date, game_time, results_str, rank, league_numbers_str])
    return data

def create_dataframe(data):
    df = pd.DataFrame(data, columns=['game_number', 'game_name', 'game_date', 'game_time', 'results', 'rank', 'league_numbers'])
    df['game_time'] = df['game_time'].apply(lambda x: int(x[:-3]))
    df['game_time'] = df['game_time'] / 60
    return df

def replace_dates(date_str):
    if "ago" in date_str:
        return datetime.now().strftime("%m/%d/%Y") + ' at 00:00'
    if "today" in date_str:
        return datetime.now().strftime("%m/%d/%Y") + date_str[5:]
    elif "yesterday" in date_str:
        return (datetime.now() - timedelta(days=1)).strftime("%m/%d/%Y") + date_str[9:]
    return date_str

def finalize_dataframe(df):
    df['game_date'] = df['game_date'].apply(replace_dates)
    df['game_date'] = pd.to_datetime(df['game_date'], format='%m/%d/%Y at %H:%M')
    df['game_time'] = pd.to_timedelta(df['game_time'], unit='h')
    df['game_start'] = df['game_date'] - df['game_time']
    df["url"] = "https://boardgamearena.com/table?table=" + df.game_number.astype(str)
    return df

def update_completed_games(df, engine, query):
    existing_games = pd.read_sql(query, engine)
    #print(existing_games.head())
    existing_games.game_number = existing_games.game_number.astype("int64")

    df.game_number = df.game_number.astype("int64")

    combined_games = pd.concat([df, existing_games])
    combined_games = combined_games.drop_duplicates(subset=['game_number'])

    combined_games.to_csv(aktualizovany_seznam_ukoncenych_her, sep=";", index=False)
    return combined_games

###################################################################################

# Get database configuration
db_config = {
    'user': config['database']['user'],
    'password': config['database']['password'],
    'host': config['database']['host']
}


def create_table(table):
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table} (
            game_number BIGINT,
            game_name TEXT,
            game_date TIMESTAMP,
            game_time TEXT,
            results TEXT,
            rank FLOAT,
            league_numbers FLOAT,
            game_start TIMESTAMP,
            url TEXT
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def load_csv_to_db(table, csv_file_path):
    data = pd.read_csv(csv_file_path, sep=';')

    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    for index, row in data.iterrows():
        cursor.execute(
            f"INSERT INTO {table} (game_number, game_name, game_date, game_time, results, rank, league_numbers, game_start, url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (int(row['game_number']), row['game_name'], row['game_date'], row['game_time'], row['results'], float(row['rank']) if not pd.isnull(row['rank']) else None, 
             float(row['league_numbers']) if not pd.isnull(row['league_numbers']) else None, row['game_start'], row['url'])
        )
    conn.commit()
    cursor.close()
    conn.close()