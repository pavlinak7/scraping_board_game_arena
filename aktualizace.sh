#!/bin/bash

# 1.Úprava názvů tabulek v databázi
# Define the database credentials
DB_NAME="bga"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432" # Default PostgreSQL port

# Prompt for the password
echo "Enter the password for user $DB_USER:"
read -s DB_PASSWORD

# Export the password so psql can use it
export PGPASSWORD=$DB_PASSWORD

# Function to check if a table exists
table_exists() {
  local table=$1
  psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -tc "SELECT 1 FROM pg_tables WHERE tablename='$table';" | grep -q 1
}

# Check and drop tables if they exist
for table in typ_hry_stare ukoncene_hry_stare umisteni_na_turnajich_stare; do
  if table_exists $table; then
    echo "Dropping table $table..."
    psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c "DROP TABLE $table;"
  fi
done

# Run the SQL commands
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME <<EOF
ALTER TABLE typ_hry RENAME TO typ_hry_stare;
ALTER TABLE ukoncene_hry RENAME TO ukoncene_hry_stare;
ALTER TABLE umisteni_na_turnajich RENAME TO umisteni_na_turnajich_stare;
ALTER TABLE typ_hry_aktualizace RENAME TO typ_hry;
ALTER TABLE ukoncene_hry_aktualizace RENAME TO ukoncene_hry;
ALTER TABLE umisteni_na_turnajich_aktualizace RENAME TO umisteni_na_turnajich;
EOF

# Unset the password variable
unset PGPASSWORD

echo "tabulky přejmenovány"


# 2. Přesunutí všeho ze "základ" do "stare"
mkdir -p stare
# Check if the directory "stare" is not empty
if [ "$(ls -A stare)" ]; then
    # Remove all files and subdirectories within "stare"
    rm -rf stare/*
fi
mv zaklad/* stare/
echo "Základ přesunut"


# 3. Move everything from folder aktualizace to folder zaklad
cp -r aktualizace/* zaklad/
echo "nejaktulnější soubory přesunuty"



# 4. Rename the files in folder zaklad to remove "2"
for file in zaklad/*2.*; do
    # Use parameter expansion to remove the "2" from the filename
    new_file="${file/2./.}"
    mv "$file" "$new_file"
done

echo "soubory přejmenovány"
echo "HOTOVO"

