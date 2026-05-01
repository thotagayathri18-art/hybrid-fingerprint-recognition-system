import shutil
import os

source = input("Enter fingerprint image path: ")
name = input("Enter new database name, example suspect_001.bmp: ")

database_folder = "database"

if not os.path.exists(database_folder):
    os.makedirs(database_folder)

destination = os.path.join(database_folder, name)

shutil.copy(source, destination)

print("Fingerprint enrolled successfully!")
print("Saved as:", destination)