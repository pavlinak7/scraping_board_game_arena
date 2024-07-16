import time
import logging
from part2funkce import *

#####################################################################################
######################################################################################
start_time = time.time()

#stažení dat k jednotlivým hrám
df = nacteni_ukoncenych_her(engine, ukoncene_hry_akt_vse_sql)
tournaments = nacteni_typu_hry(engine, typ_hry_vse_sql)
doplnit = k_doplneni(df, tournaments)

logging.basicConfig(level=logging.INFO)

if doplnit.empty:
    create_table_same("typ_hry_aktualizace", "typ_hry")
    print("Vytvořena kopie tabulky 'typ_hry'")
else:
    df_results = main(driver_path, chrome_options, login_url, email, password, doplnit.url)
    updated_games = update_completed_games(tournaments, df_results)
    create_table(typ_hry_aktual_table)
    load_csv_to_db(typ_hry_aktual_table, '/home/pavlina/Dokumenty/IT/scraping_bga_nejnovejsi/ukoncene_hry/aktualizace/tournaments2.csv')
    print("Vytvořena tabulka 'typ_hry_aktualizace'")


end_time = time.time()
print(f"Total execution time: {end_time - start_time} seconds.")
print("-----------------------------------------------------------------------------------------------------------")

#####################################################################################
######################################################################################