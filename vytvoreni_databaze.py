import pandas as pd
import configparser
import psycopg2
from psycopg2 import sql
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import numpy as np

# Read the config file
config = configparser.ConfigParser()
config.read('config.ini')

# Get database configuration
db_config = {
    'user': config['database']['user'],
    'password': config['database']['password'],
    'host': config['database']['host']
}

def create_database():
    # Connect to the default database (postgres)
    conn = psycopg2.connect(dbname='postgres', **db_config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Create database if it doesn't exist
    cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'bga'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute('CREATE DATABASE bga')
    cursor.close()
    conn.close()

def create_table(table):
    # Connect to the 'bga' database
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    # Create table if it doesn't exist
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
    # Load data from CSV file
    data = pd.read_csv(csv_file_path, sep=';')

    # Connect to the 'bga' database
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    # Insert data into the table using a more efficient bulk method
    for index, row in data.iterrows():
        cursor.execute(
            f"INSERT INTO {table} (game_number, game_name, game_date, game_time, results, rank, league_numbers, game_start, url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (int(row['game_number']), row['game_name'], row['game_date'], row['game_time'], row['results'], float(row['rank']) if not pd.isnull(row['rank']) else None, 
             float(row['league_numbers']) if not pd.isnull(row['league_numbers']) else None, row['game_start'], row['url'])
        )
    conn.commit()
    cursor.close()
    conn.close()

# Run the functions
create_database()
create_table("ukoncene_hry")
print("Vytvorena tabulka ukoncene_hry")
load_csv_to_db("ukoncene_hry", '/home/pavlina/Dokumenty/IT/portfolio/scraping_bga_nejnovejsi/ukoncene_hry/zaklad/ukoncene_hry.csv')
print("Do tabulky ukoncene_hry byla importována data")

######################################################################################################################
def create_table_typ_hry(table):
    # Connect to the 'bga' database
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table} (
            url TEXT,
            tournament TEXT,
            tournament_url TEXT,
            game_option_value TEXT,
            tournament_url2 TEXT
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def load_file_to_db(table, csv_file_path):
    # Load data from CSV file
    data = pd.read_csv(csv_file_path, sep=';')

    # Connect to the 'bga' database
    conn = psycopg2.connect(dbname='bga', **db_config)
    cursor = conn.cursor()

    # Insert data into the table using a more efficient bulk method
    for index, row in data.iterrows():
        cursor.execute(
            f"INSERT INTO {table} (url, tournament, tournament_url, game_option_value, tournament_url2) VALUES (%s, %s, %s, %s, %s)",
            (row['url'], row['tournament'], row['tournament_url'], row['game_option_value'], row['tournament_url2'])
        )
    conn.commit()
    cursor.close()
    conn.close()

# Run the functions
create_table_typ_hry("typ_hry")
print("Vytvorena tabulka typ_hry")
load_file_to_db("typ_hry", '/home/pavlina/Dokumenty/IT/portfolio/scraping_bga_nejnovejsi/ukoncene_hry/zaklad/tournaments.csv')
print("Do tabulky typ_hry byla importována data")
#####################################################################################################################
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

# Run the functions
create_table_typ_hry("umisteni_na_turnajich")
print("Vytvorena tabulka umisteni_na_turnajich")
load_file_to_db("umisteni_na_turnajich", '/home/pavlina/Dokumenty/IT/portfolio/scraping_bga_nejnovejsi/ukoncene_hry/zaklad/umisteni_na_turnajich.csv')
print("Do tabulky umisteni_na_turnajich byla importována data")
print("----------------------------------------------------------------------------------------------------")
