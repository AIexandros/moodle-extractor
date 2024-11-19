from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Anmeldedaten aus Umgebungsvariablen beziehen
username = os.getenv("MOODLE_USERNAME")
password = os.getenv("MOODLE_PASSWORD")

# URL der Moodle-Login-Seite
moodle_url = "https://moodle.hs-hannover.de/login/index.php"
# URL des Moodle-Kurses
course_url = "https://moodle.hs-hannover.de/course/view.php?id=27849"

# Setup für Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

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

# Öffne die Kursseite
driver.get(course_url)

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

for row in rows[1:]:  # Überspringe den Header
    cols = row.find_elements(By.TAG_NAME, "td")
    if len(cols) >= 3:
        vorname_nachname = cols[0].text.strip()
        email = cols[2].text.strip()
        print(f"Name: {vorname_nachname}, E-Mail: {email}")

# Schließe den Browser nach der Anmeldung (falls gewünscht)
# driver.quit()