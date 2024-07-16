from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import pandas as pd
import configparser
from bs4 import BeautifulSoup
import logging
import psycopg2
from sqlalchemy import create_engine


config = configparser.ConfigParser() # Initialize the parser
config.read('config.ini') # Read the configuration file
email = config['Credentials']['email']
password = config['Credentials']['password']
user = config['database']['user']
heslo = config['database']['password']
db_config = {
    'user': config['database']['user'],
    'password': config['database']['password'],
    'host': config['database']['host']
}

login_url = 'https://cs.boardgamearena.com/account' 
vystup = 'aktualizace/vsechny_ukoncene_hry__zdrojovy_kod_stranky2.txt'
aktualizovane_info_z_jednotlivych_her = "aktualizace/tournaments2.csv"
ukoncene_hry_akt_vse_sql = "SELECT * FROM ukoncene_hry_aktualizace"
typ_hry_vse_sql = "SELECT * FROM typ_hry"
typ_hry_aktual_table = "typ_hry_aktualizace"


driver_path = '/home/pavlina/Stažené/chromedriver-linux64/chromedriver-linux64/chromedriver'  
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.add_argument("--window-size=1920x1080")  # Set the window size
service = Service(executable_path=driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

engine = create_engine(f'postgresql+psycopg2://{user}:{heslo}@{"localhost"}:{5432}/{"bga"}') 

def nacteni_ukoncenych_her(engine, dotaz): # Establish the connection to the database
    query = dotaz
    all_games = pd.read_sql(query, engine)
    all_games.game_number = all_games.game_number.astype("int64")
    return all_games

def nacteni_typu_hry(engine, dotaz):
    query = dotaz
    all_games = pd.read_sql(query, engine)
    all_games["stul"] = all_games.url.apply(lambda x: int(x[-9:]))
    return all_games

def k_doplneni(df, tournaments):
    doplnit = [i for i in list(df.game_number) if i not in list(tournaments.stul)]
    df_vyber = df.loc[df.game_number.isin(doplnit),:]
    print(df_vyber.shape)
    return df_vyber

def initialize_webdriver(driver_path, chrome_options):
    """
    Initialize the WebDriver service and return the driver instance.
    """
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

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
    
def load_url_with_retries(driver, url, retries=3, timeout=30):
    """
    Load the URL with a specified number of retries.
    """
    for attempt in range(retries):
        try:
            logging.info(f"Attempting to load URL {url} - Attempt {attempt + 1}")
            driver.get(url)
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, 'tournament_link'))
            )
            logging.info(f"Successfully loaded URL {url}")
            return True
        except (TimeoutException, WebDriverException) as e:
            logging.warning(f"Attempt {attempt + 1} failed for URL {url}: {e}")
            time.sleep(4)
    logging.error(f"Failed to load URL {url} after {retries} attempts")
    return False

def extract_tournament_data(soup, url):
    """
    Extract tournament data from the BeautifulSoup object.
    """
    tournament_info = {'url': url, 'Tournament': 'není', 'Tournament url': 'není', 'Game Option Value': 'není'}
    
    div = soup.find('div', id='tournament_link')
    if div:
        p_tag = div.find('p')
        if p_tag:
            a_tag = p_tag.find('a', class_='bga-link')
            if a_tag:
                tournament_info['Tournament'] = a_tag.text.strip()
                tournament_info['Tournament url'] = a_tag['href'].strip()
    
    game_option_value = soup.find('span', id='gameoption_201_displayed_value')
    if game_option_value:
        tournament_info['Game Option Value'] = game_option_value.text.strip()

    return tournament_info

def scrape_urls(driver, urls):
    """
    Scrape tournament data from a list of URLs.
    """
    tournament_data = []

    for i, url in enumerate(urls):
        logging.info(f"Opening a new tab for URL {url}...")
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])

        if load_url_with_retries(driver, url):
            time.sleep(5)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'tournament_link')))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tournament_info = extract_tournament_data(soup, url)
            tournament_data.append(tournament_info)
        else:
            logging.error(f"Failed to load URL {url} after multiple attempts")
            tournament_data.append({'url': url, 'Tournament': 'není', 'Tournament url': 'není', 'Game Option Value': 'není'})

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    return tournament_data

def main(driver_path, chrome_options, login_url, email, password, urls):
    driver = initialize_webdriver(driver_path, chrome_options)
    
    try:
        login(driver, login_url, email, password)
        tournament_data = scrape_urls(driver, urls)
    finally:
        driver.quit()
        logging.info("WebDriver closed.")
    
    df_results = pd.DataFrame(tournament_data)
    df_results["Tournament url2"] = "https://boardgamearena.com" + df_results["Tournament url"]
    logging.info("Data extraction complete")
    return df_results

def update_completed_games(existing_games, df):
    df.columns = df.columns.str.lower()
    df.rename(columns={"tournament url":"tournament_url", "game option value": "game_option_value", "tournament url2":"tournament_url2"}, inplace = True)
    df["stul"] = df.url.apply(lambda x: int(x[-9:]))
    combined_games = pd.concat([df, existing_games])
    combined_games = combined_games.drop_duplicates(subset=['url'])
    print(combined_games.shape)
    combined_games.to_csv(aktualizovane_info_z_jednotlivych_her, sep = ";", index=False)
    return combined_games



def create_table(table):
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table} (
            url TEXT,
            tournament TEXT,
            tournament_url TEXT,
            game_option_value TEXT,
            tournament_url2 TEXT,
            stul TEXT
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()


def create_table_same(new_table, existing_table):
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {new_table} AS
        TABLE {existing_table};
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
            f"INSERT INTO {table} (url, tournament, tournament_url, game_option_value, tournament_url2, stul) VALUES (%s, %s, %s, %s, %s, %s)",
            (row['url'], row['tournament'], row['tournament_url'], row['game_option_value'], row['tournament_url2'], row['stul'])
        )
    conn.commit()
    cursor.close()
    conn.close()