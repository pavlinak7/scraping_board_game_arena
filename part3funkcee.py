from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException
import time
import pandas as pd
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
db_config = {
    'user': config['database']['user'],
    'password': config['database']['password'],
    'host': config['database']['host']
}

login_url = 'https://cs.boardgamearena.com/account' 
prozatimni_umisteni_na_turnajich = 'zaklad/umisteni_na_turnajich.csv'
target_url_umisteni_na_turnajich = 'https://boardgamearena.com/player?id=93282695&section=recent' 
vystup2 = 'aktualizace/turnaje_umisteni__zdrojovy_kod_stranky2.txt'
aktualizovane_umisteni_na_turnajich = 'aktualizace/umisteni_na_turnajich2.csv'
umisteni_na_turnajich_aktual_table = "umisteni_na_turnajich_aktualizace"

driver_path = '/home/pavlina/Stažené/chromedriver-linux64/chromedriver-linux64/chromedriver'  
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.add_argument("--window-size=1920x1080")  # Set the window size

# Initialize the WebDriver service
service = Service(executable_path=driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)


def nacteni_umisteni_na_turnajich():
    engine = create_engine(f'postgresql+psycopg2://{user}:{heslo}@{"localhost"}:{5432}/{"bga"}')  # Establish the connection to the database
    query = "SELECT * FROM umisteni_na_turnajich"
    all_games = pd.read_sql(query, engine)
    return all_games['tournament_link'].iloc[0]

# Initialize WebDriver
def init_webdriver(driver_path, chrome_options):
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Login to the website
def login(driver, login_url, email, password):
    driver.get(login_url)
    email_field = driver.find_element(By.NAME, 'email')  
    password_field = driver.find_element(By.NAME, 'password')  
    email_field.send_keys(email)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    
    WebDriverWait(driver, 20).until(EC.url_changes(login_url))
    print("Login successful.")

# Open a new tab and navigate to the target page
def navigate_to_target_page(driver, target_url):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(target_url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    print("Target page loaded successfully.")

# Handle cookie consent banner
def handle_cookie_consent(driver):
    try:
        cookie_consent_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="dialog"] .cc-dismiss'))
        )
        cookie_consent_button.click()
        print("Cookie consent banner closed.")
    except (TimeoutException, NoSuchElementException):
        print("No cookie consent banner found or failed to close it.")

# Load all game records and save the page source when the target tournament is found
def load_game_records(driver, first_tournament_link, output_path):
    while True:
        try:
            page_source = driver.page_source
            if f'tournament?id={first_tournament_link}' in page_source:
                print(f"Tournament {first_tournament_link} found. Saving the page source...")
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.write(page_source)
                print(f'Source code saved to {output_path}')
                break

            initial_posts = len(driver.find_elements(By.CLASS_NAME, 'post'))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            see_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'board_seemore_a')))
            see_more_button.click()
            time.sleep(2)

            new_posts = len(driver.find_elements(By.CLASS_NAME, 'post'))

            if new_posts == initial_posts:
                print("No new posts loaded.")
                break

        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
            print("No more 'See more' buttons to click, an error occurred, or an element is blocking the click.")
            break

#############################################
def read_file(file_path):
    """Reads the content of a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def parse_html(html_content):
    """Parses the HTML content using BeautifulSoup."""
    return BeautifulSoup(html_content, 'html.parser')

def extract_tournament_data(soup):
    """Extracts tournament link and place information from the parsed HTML."""
    posts = soup.find_all('div', class_='post')
    tournament_data = []
    
    for post in posts:
        post_content = post.find('div', class_='postcontent')
        post_message = post_content.find('div', class_='postmessage') 
        links = post_message.find_all('a', href=True)
        if len(links) > 1:  # Ensure there is more than one link
            tournament_link = links[1]  # The second link is the tournament link
            href = tournament_link['href']
            text = post_message.get_text()
            place = text.split('at place: ')[-1] if 'at place:' in text else ''
            tournament_data.append((href, place))
    
    return tournament_data

def create_dataframe(tournament_data):
    """Creates a DataFrame from the tournament data."""
    df = pd.DataFrame(tournament_data, columns=['tournament_link', 'place'])
    df_filtered = df[df['place'] != ""]
    #df_filtered['Tournament Link'] = df_filtered['Tournament Link'].apply(lambda x: x[-6:])
    df_filtered = df_filtered.copy()
    df_filtered.loc[:, 'tournament_link'] = df_filtered['tournament_link'].apply(lambda x: x[-6:])
    return df_filtered

def tutu(file_path):
    """Main function to execute the steps."""
    html_content = read_file(file_path)
    soup = parse_html(html_content)
    tournament_data = extract_tournament_data(soup)
    df = create_dataframe(tournament_data)
    return df

def update_completed_games(df):
    engine = create_engine(f'postgresql+psycopg2://{user}:{heslo}@{"localhost"}:{5432}/{"bga"}')  # Establish the connection to the database
    query = "SELECT * FROM umisteni_na_turnajich"
    existing_games = pd.read_sql(query, engine)
    print(f"existing:{existing_games.shape}")
    print(f"new: {df.shape}")
    existing_games["tournament_link"] = existing_games["tournament_link"].astype("int64")
    df["tournament_link"] = df["tournament_link"].astype("int64")
    combined_games = pd.concat([df, existing_games])
    combined_games = combined_games.drop_duplicates(subset=['tournament_link'])
    print(f"komplet: {combined_games.shape}")
    combined_games.to_csv(aktualizovane_umisteni_na_turnajich, sep = ";", index=False)
    return combined_games




def create_table_typ_hry(table):
    # Connect to the 'bga' database
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table} (
            tournament_link TEXT,
            place VARCHAR
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def load_file_to_db(table, csv_file_path):
    # Load data from CSV file
    data = pd.read_csv(csv_file_path, sep=';')

    # Convert all columns to their appropriate Python types
    data = data.astype(object).where(pd.notnull(data), None)

    # Connect to the 'bga' database
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    # Insert data into the table using a more efficient bulk method
    for index, row in data.iterrows():
        cursor.execute(
            f"INSERT INTO {table} (tournament_link, place) VALUES (%s, %s)",
            (row['tournament_link'], row['place'])
        )
    conn.commit()
    cursor.close()
    conn.close()