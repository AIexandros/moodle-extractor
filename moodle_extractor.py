from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# URL der Moodle-Login-Seite
moodle_url = "https://moodle.hs-hannover.de/login/index.php"

# Deine Anmeldedaten
username = ""  # Ersetze durch deinen Anmeldenamen oder E-Mail
password = ""  # Ersetze durch dein Passwort

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

# Schließe den Browser nach der Anmeldung (falls gewünscht)
# driver.quit()
=======
>>>>>>> 8722097ed98db368825e06104d8b5fd2a6438c99
