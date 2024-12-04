from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time
import pandas as pd
import shutil

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Anmeldedaten aus Umgebungsvariablen beziehen
username = os.getenv("MOODLE_USERNAME")
password = os.getenv("MOODLE_PASSWORD")

# Ordner für die Teilnehmerlisten erstellen
output_dir = "moodle_participants_lists"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Setup für Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# URL der Moodle-Login-Seite
moodle_url = "https://moodle.hs-hannover.de/login/index.php"

# Öffne die Moodle-Login-Seite
driver.get(moodle_url)

# Warten, bis die Seite geladen ist
time.sleep(3)  # Wartezeit anpassen, je nach Ladegeschwindigkeit

# Finde das Eingabefeld für den Anmeldenamen/E-Mail
username_field = driver.find_element(By.ID, "username")
username_field.send_keys(username)

# Finde das Eingabefeld für das Passwort
password_field = driver.find_element(By.ID, "password")
password_field.send_keys(password)

# Finde und drücke den Login-Button
login_button = driver.find_element(By.ID, "loginbtn")
login_button.click()

# Optional: Warten bis die Seite geladen ist
time.sleep(5)

# Navigiere zur Seite mit den Kursinformationen zum Herunterladen der CSV-Datei
courses_url = "https://moodle.hs-hannover.de/mod/data/view.php?id=945891"
driver.get(courses_url)

# Optional: Warten bis die Seite geladen ist
time.sleep(5)

# Klicke auf den "Aktionen"-Button, um das Dropdown-Menü zu öffnen
try:
    actions_button = driver.find_element(By.XPATH, "//a[contains(@class, 'dropdown-toggle') and contains(@aria-label, 'Aktionen')]")
    actions_button.click()

    # Optional: Warten bis das Dropdown-Menü geöffnet ist
    time.sleep(2)

    # Klicke auf "Einträge exportieren"
    export_entries_button = driver.find_element(By.XPATH, "//span[@class='menu-action-text' and text()='Einträge exportieren']")
    export_entries_button.click()

    # Optional: Warten bis die Seite geladen ist
    time.sleep(2)

    # Klicke auf den Button "Einträge exportieren" zum Herunterladen der Datei
    export_submit_button = driver.find_element(By.ID, "id_submitbutton")
    export_submit_button.click()

    # Optional: Warten bis die Datei heruntergeladen ist
    time.sleep(10)

    # Verschiebe die heruntergeladene Datei in den Projektordner
    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    downloaded_file = max([os.path.join(download_path, f) for f in os.listdir(download_path)], key=os.path.getctime)
    shutil.move(downloaded_file, "courses_information.csv")
    file_path = "courses_information.csv"
except Exception as e:
    print(f"Fehler beim Herunterladen der Kursinformationen: {e}")
    driver.quit()
    exit()

# CSV-Datei laden
data = pd.read_csv(file_path)

# Duplikate im Feld "Moodle-Link" entfernen, sodass mindestens ein Eintrag pro Link erhalten bleibt
data = data.drop_duplicates(subset=['Moodle-Link'])

# CSV-Datei nach dem Entfernen von Duplikaten in einer Testdatei speichern
test_csv_path = 'test_output_filtered_courses.csv'
data.to_csv(test_csv_path, index=False)
print(f"Test-CSV-Datei wurde unter '{test_csv_path}' gespeichert.")

# Filtere die Kurse, bei denen unter Evaluierungswunsch "ja" steht
courses_to_evaluate = data[data['Evaluierungswunsch'] == 'ja']

# Gebe alle Kurse aus, die evaluiert werden sollen
print("Kurse zur Evaluation:")
for index, row in courses_to_evaluate.iterrows():
    print(f"- {row['Name der Vorlesung']} ({row['Moodle-Link']})")

# Durchlaufe alle Moodle-Links der Kurse mit Evaluierungswunsch
for index, row in courses_to_evaluate.iterrows():
    moodle_link = row['Moodle-Link']
    enrolment_key = row['Einschreibeschluessel']
    course_name = row['Name der Vorlesung']
    print(f"\nÖffne Moodle-Link: {moodle_link}")

    # Öffne die Kursseite
    driver.get(moodle_link)

    # Optional: Warten bis die Seite geladen ist
    time.sleep(5)

    # Prüfe, ob die Seite ein Einschreibeschlüsselfeld enthält und fülle es aus
    try:
        enrolment_field = driver.find_element(By.XPATH, "//input[@type='password' and contains(@id, 'enrolpassword')]")
        enrolment_field.send_keys(enrolment_key)
        enrolment_field.send_keys(Keys.RETURN)

        # Optional: Warten bis die Seite geladen ist
        time.sleep(5)
    except:
        # Falls bereits eingeschrieben, einfach fortfahren
        pass

    # Finde und klicke auf den Button "Teilnehmer*Innen"
    try:
        participants_button = driver.find_element(By.PARTIAL_LINK_TEXT, "Teilnehmer")
        participants_button.click()

        # Optional: Warten bis die Seite geladen ist
        time.sleep(5)

        # Prüfe, ob der Button "Alle Nutzer*innen auswählen" existiert und klicke darauf
        try:
            select_all_button = driver.find_element(By.XPATH, "//input[@type='button' and @id='checkall' and contains(@value, 'Alle')]")
            select_all_button.click()
        except:
            # Falls der Button nicht existiert, klicke die Checkbox "select-all-participants"
            select_all_checkbox = driver.find_element(By.ID, "select-all-participants")
            select_all_checkbox.click()

        # Optional: Warten bis die Auswahl abgeschlossen ist
        time.sleep(2)

        # Wähle die Option zum Herunterladen der Teilnehmerliste als CSV
        download_option = driver.find_element(By.XPATH, "//option[contains(@value, 'bulkchange.php?operation=download_participants') and contains(., 'Komma separierte Werte')]")
        download_option.click()

        # Optional: Warten bis die Datei heruntergeladen ist
        time.sleep(5)

        # Verschiebe die heruntergeladene Datei in den Projektordner
        downloaded_file = max([os.path.join(download_path, f) for f in os.listdir(download_path)], key=os.path.getctime)
        shutil.move(downloaded_file, os.path.join(output_dir, f"participants_{course_name}.csv"))

    except Exception as e:
        print(f"Fehler beim Zugriff auf die Teilnehmerliste: {e}")

# Schließe den Browser nach der Anmeldung (falls gewünscht)
# driver.quit()
