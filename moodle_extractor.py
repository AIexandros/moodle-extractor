from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# URL der Moodle-Seite und Kurs-Link
moodle_url = "https://moodle.hs-hannover.de"
kurs_link = "/course/view.php?id=27849"
benutzername = "dein_benutzername"  # Deinen Moodle-Benutzernamen hier einfügen
passwort = "dein_passwort"           # Dein Moodle-Passwort hier einfügen
einschreibeschluessel = ""           # Einschreibeschlüssel, falls erforderlich

# Setup für Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Öffne Moodle und gehe zur Login-Seite
driver.get(moodle_url)

# Warten, bis die Login-Felder sichtbar sind
time.sleep(30)  # Anpassen je nach Ladezeit der Seite

# Finde die Eingabefelder für den Login und fülle sie aus
username_field = driver.find_element(By.ID, "username")
password_field = driver.find_element(By.ID, "password")

username_field.send_keys(benutzername)
password_field.send_keys(passwort)

# Absenden des Login-Formulars
password_field.send_keys(Keys.RETURN)

# Warten, bis die Login-Seite verarbeitet ist und die Moodle-Startseite angezeigt wird
time.sleep(50)

# Öffne den gewünschten Kurs
driver.get(moodle_url + kurs_link)

# Warten, bis das Einschreibeschlüsselfeld erscheint (falls erforderlich)
time.sleep(30)

try:
    # Falls der Kurs einen Einschreibeschlüssel benötigt, gib diesen ein
    einschreibefeld = driver.find_element(By.ID, "enrol_password")  # Anpassen, wenn nötig
    einschreibefeld.send_keys(einschreibeschluessel)
    einschreibefeld.send_keys(Keys.RETURN)

    # Warte auf die Bestätigung der Einschreibung
    time.sleep(5)
except:
    print("Kein Einschreibeschlüssel benötigt oder Feld nicht gefunden.")

# Holen der HTML-Seite nach dem Einschreiben
html_content = driver.page_source

# BeautifulSoup verwenden, um die Teilnehmer zu extrahieren
soup = BeautifulSoup(html_content, 'html.parser')

# Angenommene Struktur der Teilnehmerliste: Extrahiere Teilnehmer-Daten aus der Tabelle
participants = []
table = soup.find('table', {'id': 'participants_table'})  # Passe die ID an, falls nötig

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

# Schließe den Browser (auskommentieren, falls du den Browser offen halten möchtest)
# driver.quit()
