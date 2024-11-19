from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# URL der Moodle-Seite und Kurs-Link
moodle_url = "https://deine-moodle-url.de"
kurs_link = "/path-to-deinen-kurs"
einschreibeschluessel = "deinEinschreibeschluessel"

# Setup für Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Öffne Moodle und gehe zum Kurs
driver.get(moodle_url + kurs_link)

# Warten, bis das Eingabefeld für den Einschreibeschlüssel erscheint
time.sleep(3)  # Warten auf die Seite, anpassen je nach Ladezeit

# Finde das Eingabefeld für den Einschreibeschlüssel und gebe ihn ein
einschreibefeld = driver.find_element(By.ID, "enrol_password")  # Annahme: Das ID-Attribut des Feldes ist 'enrol_password'
einschreibefeld.send_keys(einschreibeschluessel)

# Absenden des Formulars
einschreibefeld.send_keys(Keys.RETURN)

# Warten, bis die Seite mit den Teilnehmern geladen ist
time.sleep(5)  # Anpassbar je nach Ladegeschwindigkeit der Seite

# Holen der HTML-Seite nach dem Einschreiben
html_content = driver.page_source

# BeautifulSoup verwenden, um die Teilnehmer zu extrahieren
soup = BeautifulSoup(html_content, 'html.parser')

# Angenommene Struktur der Teilnehmerliste: Extrahiere Teilnehmer-Daten aus der Tabelle
participants = []
table = soup.find('table', {'id': 'participants_table'})  # Stelle sicher, dass dies die richtige ID ist

if table:
    rows = table.find_all('tr')[1:]  # Überspringe den Header
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 0:
            vorname = cols[0].text.strip()
            nachname = cols[1].text.strip()
            email = cols[2].text.strip()
            status = cols[3].text.strip()
            participants.append({
                'Vorname': vorname,
                'Nachname': nachname,
                'Email': email,
                'Status': status
            })

# Ausgabe der extrahierten Teilnehmer
for participant in participants:
    print(participant)

# Schließe den Browser
driver.quit()
