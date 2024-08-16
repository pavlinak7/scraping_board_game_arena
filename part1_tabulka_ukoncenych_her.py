import time
from part1funkce import *

#################################################################################################
#################################################################################################
start_time = time.time()

#stažení zdrojového kódu stránky
try:
    engine = create_engine(f'postgresql+psycopg2://{user}:{heslo}@{"localhost"}:{5432}/{"bga"}')  # Establish the connection to the database
    target_date = get_target_date_from_db("SELECT game_date FROM ukoncene_hry", engine)
    login(driver, login_url, email, password)
    navigate_to_target_page(driver, target_url_ukoncene_hry)
    handle_cookie_consent(driver)
    if check_for_date_and_save_source(driver, target_date, vystup):
        print("Date found and source code saved.")
    else:
        print("Date not found.")
finally:
    driver.quit()
    print("WebDriver closed.")

######################################################################################
#extrakce informací ze zdrojového kódu stránky
file_content = read_file(vystup)
rows = extract_rows(file_content)
data = process_data(rows)
df = create_dataframe(data)
df = finalize_dataframe(df)
updated_games = update_completed_games(df, engine, "SELECT * FROM ukoncene_hry")

######################################################################################
#nahrání aktualizované tabulky do databáze
create_table(ukonc_hry_aktual_table)
load_csv_to_db(ukonc_hry_aktual_table, '/home/pavlina/Dokumenty/IT/portfolio/scraping_bga_nejnovejsi/ukoncene_hry/aktualizace/ukoncene_hry2.csv')


end_time = time.time()
print(f"Total execution time: {end_time - start_time} seconds.")
print("-----------------------------------------------------------------------------------------------------------")

#################################################################################################
#################################################################################################