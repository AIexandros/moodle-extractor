from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time
import csv
import pandas as pd

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Anmeldedaten aus Umgebungsvariablen beziehen
username = os.getenv("MOODLE_USERNAME")
password = os.getenv("MOODLE_PASSWORD")

# Pfad zur CSV-Datei mit den Kursinformationen
file_path = 'Link-DB-549_records-20241118_1037.csv'

# CSV-Datei laden
data = pd.read_csv(file_path)

# Filtere die Kurse, bei denen unter Evaluierungswunsch "ja" steht
courses_to_evaluate = data[data['Evaluierungswunsch'] == 'ja']

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

# Durchlaufe alle Moodle-Links der Kurse mit Evaluierungswunsch
for index, row in courses_to_evaluate.iterrows():
    moodle_link = row['Moodle-Link']
    enrolment_key = row['Einschreibeschluessel']
    print(f"Öffne Moodle-Link: {moodle_link}")

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

        # Finde und klicke auf den Button "Teilnehmer*Innen"
        participants_button = driver.find_element(By.PARTIAL_LINK_TEXT, "Teilnehmer")
        participants_button.click()

        # Optional: Warten bis die Seite geladen ist
        time.sleep(5)

        # Alle Teilnehmer mit Vor- und Nachname sowie E-Mail-Adresse ausgeben
        participants_table = driver.find_element(By.TAG_NAME, "table")
        rows = participants_table.find_elements(By.TAG_NAME, "tr")

        with open(f'participants_{index}.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Vorname Nachname", "E-Mail"])

            for row in rows[1:]:  # Überspringe den Header
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 3:
                    vorname_nachname = cols[0].text.strip().replace(" auswählen", "")  # Entferne "auswählen"
                    email = cols[1].text.strip()
                    writer.writerow([vorname_nachname, email])
                    print(f"Name: {vorname_nachname}, E-Mail: {email}")
    except Exception as e:
        print(f"Fehler beim Zugriff auf die Teilnehmerliste: {e}")

# Schließe den Browser nach der Anmeldung (falls gewünscht)
# driver.quit()
