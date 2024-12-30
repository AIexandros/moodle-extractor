import pandas as pd
import os
import time
import shutil
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from evaluation_table_creator import create_evaluation_table, prepare_evaluation_data, generate_three_column_table
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Anmeldedaten aus Umgebungsvariablen beziehen
username = os.getenv("MOODLE_USERNAME")
password = os.getenv("MOODLE_PASSWORD")

# Ordner für die Teilnehmerlisten erstellen
output_dir = "moodle_participants_lists"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Datei mit Professorendaten laden
professor_info_path = "faculty_information.csv"
professor_data = pd.read_csv(professor_info_path)

# Setup für Selenium WebDriver
def setup_driver():
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Moodle-Login durchführen
def moodle_login(driver, username, password):
    moodle_url = "https://moodle.hs-hannover.de/login/index.php"
    driver.get(moodle_url)
    time.sleep(3)  # Warten, bis die Seite geladen ist

    # Eingabefelder finden und ausfüllen
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "loginbtn").click()
    time.sleep(5)  # Warten, bis die Seite nach Login geladen ist

# Klick-Utility mit Fallback auf JavaScript und erweiterten Wartezeiten
def safe_click(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", element)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(element))
        element.click()
    except Exception as e:
        print(f"JavaScript-Klick wird verwendet, da regulärer Klick fehlschlug: {e}")
        driver.execute_script("arguments[0].click();", element)

# Teilnehmerlisten für einen Kurs verarbeiten
def process_course(row):
    driver = setup_driver()
    moodle_login(driver, username, password)
    moodle_link = row['Moodle-Link']
    enrolment_key = row['Einschreibeschluessel']
    course_name = row['Name der Vorlesung']

    print(f"\nVerarbeite Kurs: {course_name}")
    driver.get(moodle_link)
    time.sleep(5)

    try:
        # Einschreibeschlüssel eingeben
        enrolment_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password' and contains(@id, 'enrolpassword')]"))
        )
        enrolment_field.send_keys(enrolment_key)
        enrolment_field.send_keys(Keys.RETURN)
        time.sleep(5)
    except Exception as e:
        print(f"Kein Einschreibeschlüssel erforderlich oder bereits eingeschrieben für {course_name}. Fehler: {e}")

    try:
        # Teilnehmer-Link klicken
        participants_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Teilnehmer')]"))
        )
        driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", participants_button)
        safe_click(driver, participants_button)
        time.sleep(5)

        # Prüfen und auf "Alle Nutzer*innen auswählen" klicken
        try:
            select_all_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "checkall"))
            )
            safe_click(driver, select_all_button)
        except Exception:
            # Fallback auf Checkbox "select-all-participants"
            select_all_checkbox = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "select-all-participants"))
            )
            safe_click(driver, select_all_checkbox)

        # CSV-Option auswählen
        download_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//option[contains(@value, 'bulkchange.php?operation=download_participants') and contains(., 'Komma separierte Werte')]"))
        )
        driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", download_option)
        safe_click(driver, download_option)
        time.sleep(5)

        print(f"Teilnehmerliste für {course_name} wurde heruntergeladen.")

    except Exception as e:
        print(f"Fehler beim Zugriff auf die Teilnehmerliste für {course_name}: {e}")
    finally:
        driver.quit()

    return None  # Wir verschieben und benennen Dateien später

# Nachträgliche Benennung der Dateien
def rename_downloaded_files(courses_to_evaluate, download_path, output_dir):
    blacklist_path = os.path.join(output_dir, "blacklist.csv")
    if os.path.exists(blacklist_path):
        blacklist_df = pd.read_csv(blacklist_path)
    else:
        blacklist_df = pd.DataFrame(columns=["Name der Vorlesung", "Moodle-Link", "Einschreibeschluessel"])

    for _, row in courses_to_evaluate.iterrows():
        course_name = row['Name der Vorlesung']
        moodle_link = row['Moodle-Link']

        # Kurs-ID aus dem Link extrahieren
        match = re.search(r"id=(\d+)", moodle_link)
        course_id = match.group(1) if match else None

        if not course_id:
            print(f"Keine Kurs-ID für {course_name}. Überspringe.")
            blacklist_df.loc[len(blacklist_df)] = {
                "Name der Vorlesung": course_name,
                "Moodle-Link": moodle_link,
                "Einschreibeschluessel": row['Einschreibeschluessel']
            }
            continue

        try:
            # Datei finden und umbenennen
            downloaded_file = next(
                f for f in os.listdir(download_path)
                if course_id in f and f.endswith(".csv")
            )
            final_file_name = f"participants_{course_name.replace(' ', '_')}.csv"
            final_file_path = os.path.join(output_dir, final_file_name)
            shutil.move(os.path.join(download_path, downloaded_file), final_file_path)
            print(f"Teilnehmerliste für {course_name} umbenannt und gespeichert unter {final_file_path}.")
        except StopIteration:
            print(f"Teilnehmerliste für {course_name} nicht gefunden. Kurs wird zur Blacklist hinzugefügt.")
            blacklist_df.loc[len(blacklist_df)] = {
                "Name der Vorlesung": course_name,
                "Moodle-Link": moodle_link,
                "Einschreibeschluessel": row['Einschreibeschluessel']
            }

    # Aktualisierte Blacklist speichern
    blacklist_df.to_csv(blacklist_path, index=False)

# Hauptprozess
def main():
    driver = setup_driver()
    moodle_login(driver, username, password)

    # Kursinformationen herunterladen
    courses_url = "https://moodle.hs-hannover.de/mod/data/view.php?id=945891"
    file_path = "courses_information.csv"
    driver.get(courses_url)
    time.sleep(5)

    try:
        # Aktionen-Menü öffnen
        actions_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'dropdown-toggle') and contains(@aria-label, 'Aktionen')]"))
        )
        driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", actions_button)
        safe_click(driver, actions_button)
        time.sleep(2)

        # "Einträge exportieren" auswählen
        export_entries = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@class='menu-action-text' and text()='Einträge exportieren']"))
        )
        driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", export_entries)
        safe_click(driver, export_entries)
        time.sleep(2)

        # Export abschicken
        export_submit = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id_submitbutton"))
        )
        driver.execute_script("arguments[0].scrollIntoViewIfNeeded();", export_submit)
        safe_click(driver, export_submit)
        time.sleep(10)

        # Heruntergeladene Datei verschieben
        download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        downloaded_file = max([os.path.join(download_path, f) for f in os.listdir(download_path)], key=os.path.getctime)
        shutil.move(downloaded_file, file_path)
        print("Kursinformationen erfolgreich heruntergeladen.")
    except Exception as e:
        print(f"Fehler beim Herunterladen der Kursinformationen: {e}")
        driver.quit()
        exit()

    driver.quit()

    # Kurse verarbeiten
    courses_data = pd.read_csv(file_path)

    # Daten für die Evaluation vorbereiten
    courses_to_evaluate = prepare_evaluation_data(courses_data, output_dir)

    print("Kurse zur Evaluation:")
    for index, row in courses_to_evaluate.iterrows():
        print(f"- {row['Name der Vorlesung']} ({row['Moodle-Link']})")

    # Alle Teilnehmerlisten herunterladen
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_course, [row for _, row in courses_to_evaluate.iterrows()]))

    # Dateien umbenennen und fehlende Teilnehmerlisten zur Blacklist hinzufügen
    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    rename_downloaded_files(courses_to_evaluate, download_path, output_dir)

    create_evaluation_table(courses_to_evaluate, courses_data, output_dir, driver, professor_data)

    # Pfade zur Evaluationstabelle und Teilnehmerlisten-Verzeichnis
    evaluation_table_path = os.path.join(output_dir, "Steuerdatei.csv")
    participants_dir = "moodle_participants_lists"
    output_file = os.path.join(output_dir, "finale_tabelle.csv")

    # Dreispaltige Tabelle generieren
    generate_three_column_table(evaluation_table_path, participants_dir, output_file)


if __name__ == "__main__":
    main()