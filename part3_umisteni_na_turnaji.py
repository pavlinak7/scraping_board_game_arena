import time
from part3funkcee import *

#####################################################################################
######################################################################################
start_time = time.time()

def main():
    output_path = "/home/pavlina/Dokumenty/IT/scraping_bga_nejnovejsi/ukoncene_hry/aktualizace/turnaje_umisteni__zdrojovy_kod_stranky2.txt"
    
    first_tournament_link = nacteni_umisteni_na_turnajich()
    
    driver = init_webdriver(driver_path, chrome_options)
    try:
        print("Opening the login page...")
        login(driver, login_url, email, password)
        
        print("Opening a new tab...")
        navigate_to_target_page(driver, target_url_umisteni_na_turnajich)

        print("Handling cookie consent banner if present...")
        handle_cookie_consent(driver)

        print("Starting to load all game records...")
        load_game_records(driver, first_tournament_link, output_path)

    finally:
        driver.quit()
        print("WebDriver closed.")

if __name__ == "__main__":
    main()
#####################################################################################
df = tutu(vystup2)

updated_games = update_completed_games(df)

######################################################################################
create_table_typ_hry(umisteni_na_turnajich_aktual_table)
load_file_to_db(umisteni_na_turnajich_aktual_table, '/home/pavlina/Dokumenty/IT/scraping_bga_nejnovejsi/ukoncene_hry/aktualizace/umisteni_na_turnajich2.csv')


end_time = time.time()
print(f"Total execution time: {end_time - start_time} seconds.")

#####################################################################################
######################################################################################