import pandas as pd
import os
from difflib import get_close_matches
from datetime import datetime

def determine_current_semester():
    """
    Bestimmt das aktuelle Semester basierend auf dem aktuellen Datum.

    Rückgabe:
        str: Das aktuelle Semester im Format "SS xx" oder "WS xx/xx".
    """
    now = datetime.now()
    year = now.year
    if now.month >= 9:  # Wintersemester beginnt im September
        return f"WS {year % 100}/{(year + 1) % 100}"
    elif now.month >= 3:  # Sommersemester beginnt im März
        return f"SS {year % 100}"
    else:  # Monate Januar und Februar gehören zum vorherigen Wintersemester
        return f"WS {(year - 1) % 100}/{year % 100}"

def prepare_evaluation_data(courses_data, output_dir):
    """
    Bereitet die Kursdaten für die Evaluation vor, einschließlich der Aggregation von Studiengängen,
    der Zuordnung des aktuellen Semesters, der LV-Art und des Fragebogentyps.

    Parameter:
        courses_data (pd.DataFrame): Die ursprünglichen Kursdaten.
        output_dir (str): Der Pfad zum Ausgabeverzeichnis.

    Rückgabe:
        pd.DataFrame: Die vorbereiteten Kursdaten zur Evaluation.
    """
    # Semester für alle Kurse setzen
    current_semester = determine_current_semester()
    courses_data['Semester'] = current_semester

    # Studiengänge pro Kurs aggregieren
    courses_data['Studiengang'] = courses_data.groupby('Moodle-Link')['Semesterzug'].transform(lambda x: ','.join(set(x.dropna())))

    # Blacklist-Kriterien:
    blacklist = courses_data[
        ((courses_data['Evaluierungswunsch als Vorlesung'].str.lower() == 'ja') |
         (courses_data['Evaluierungswunsch als Labor'].str.lower() == 'ja')) & (
            courses_data['Moodle-Link'].isnull() | 
            (courses_data['Moodle-Link'].str.strip() == '') | 
            (courses_data['Einschreibeschluessel'].str.strip().str.lower() == "bitte per e-mail beim dozenten erfragen")
        )
    ]

    blacklist.to_csv(f"{output_dir}/blacklist.csv", index=False)

    # LV-Art und Fragebogentyp auf Basis der Spalten "Evaluierungswunsch als Vorlesung" und "Evaluierungswunsch als Labor" definieren
    def determine_lv_art(row):
        vorlesung = str(row.get('Evaluierungswunsch als Vorlesung', '')).strip().lower()
        labor = str(row.get('Evaluierungswunsch als Labor', '')).strip().lower()

        if labor == 'ja':
            return "Labor"
        elif vorlesung == 'ja':
            return "Vorlesung"
        return "Unbekannt"

    def determine_questionnaire_type(row):
        vorlesung = str(row.get('Evaluierungswunsch als Vorlesung', '')).strip().lower()
        labor = str(row.get('Evaluierungswunsch als Labor', '')).strip().lower()

        if labor == 'ja':
            return "HsH-Labor"
        elif vorlesung == 'ja':
            return "Evalu"
        return "Unbekannt"

    courses_data['LV-Art'] = courses_data.apply(determine_lv_art, axis=1)
    courses_data['Fragebogentyp'] = courses_data.apply(determine_questionnaire_type, axis=1)

    # Duplikate entfernen
    courses_to_evaluate = courses_data.drop_duplicates(subset=['Moodle-Link'])

    if output_dir:
        blacklist.to_csv(f"{output_dir}/blacklist.csv", index=False)

    return courses_to_evaluate[
        (courses_to_evaluate['Evaluierungswunsch als Vorlesung'].str.lower() == 'ja') |
        (courses_to_evaluate['Evaluierungswunsch als Labor'].str.lower() == 'ja')
    ]

def create_evaluation_table(courses_to_evaluate, original_data, output_dir, driver, professor_data):
    """
    Erstellt eine Evaluationstabelle mit allen relevanten Kurs- und Dozentendaten.

    Parameter:
        courses_to_evaluate (pd.DataFrame): Gefilterte DataFrame mit Kursen zur Evaluation.
        original_data (pd.DataFrame): Ursprüngliche Kursdaten.
        output_dir (str): Verzeichnis, in dem die Tabelle gespeichert wird.
        driver (webdriver): Selenium WebDriver-Instanz (optional, falls benötigt).
        professor_data (pd.DataFrame): DataFrame mit Informationen über Dozenten.

    Rückgabe:
        None
    """
    # Spalten für die Evaluationstabelle definieren
    columns = [
        "Funktion", "Anrede", "Titel", "Vorname", "Nachname", "E-Mail",
        "LV-Name", "LV-Kennung", "LV-Ort", "Studiengang",
        "LV-Art", "Anzahl", "Sekundärdoz", "Fragebogentyp", "Semester"
    ]

    # Evaluationstabelle erstellen
    evaluation_table = pd.DataFrame(columns=columns)

    # Kurse iterieren und Evaluationstabelle füllen
    for index, row in courses_to_evaluate.iterrows():
        # Informationen über den Dozenten aus der professor_data suchen
        dozent_name = row['Dozent'].strip()
        professor_info = professor_data[professor_data['Nachname'].str.lower() == dozent_name.lower()]

        if professor_info.empty:
            # Finde den ähnlichsten Nachnamen, falls keine exakte Übereinstimmung vorliegt
            similar_names = get_close_matches(dozent_name.lower(), professor_data['Nachname'].str.lower().tolist(), n=1, cutoff=0.6)
            if similar_names:
                professor_info = professor_data[professor_data['Nachname'].str.lower() == similar_names[0]]

        if not professor_info.empty:
            professor_row = professor_info.iloc[0]
            professional_title = professor_row.get("Titel", None)
            firstname = professor_row.get("Vorname", "")
            surname = professor_row.get("Nachname", "")
            email = professor_row.get("E-Mail-Adresse", "")
            salutation = professor_row.get("Anrede", "")
            initials = f"{firstname[0].upper()}{surname[0].upper()}".replace("Ç", "C")
        else:
            professional_title = None
            firstname = "Unbekannt"
            surname = row.get("Dozent", "")
            email = "Nicht verfügbar"
            salutation = "Herr/Frau"
            initials = "XX"

        # LV-Kennung erstellen
        course_shortname = row.get("Kurzbezeichnung", "")
        lv_kennung = f"{course_shortname}_{initials}" if course_shortname and initials else "Unbekannt"

        # Teilnehmeranzahl aus Teilnehmerliste bestimmen
        participants_file = f"participants_{row.get('Name der Vorlesung', '').replace(' ', '_')}.csv"
        participants_path = os.path.join(output_dir, participants_file)

        try:
            if os.path.exists(participants_path):
                participants_data = pd.read_csv(participants_path)
                participant_count = len(participants_data) - 1  # Spaltenanzahl - 1
            else:
                participant_count = 0
                print(f"Teilnehmerliste für {row.get('Name der Vorlesung', '')} nicht gefunden.")
        except Exception as e:
            print(f"Fehler beim Lesen der Teilnehmerliste {participants_file}: {e}")
            participant_count = 0

        # Evaluationstabelle befüllen
        evaluation_table = pd.concat([evaluation_table, pd.DataFrame([{
            "Funktion": "Dozent",  # Alle sind Dozenten
            "Anrede": salutation,  # Anrede aus Professorendaten
            "Titel": professional_title,  # Titel des Dozenten
            "Vorname": firstname,
            "Nachname": surname,
            "E-Mail": email,
            "LV-Name": row.get("Name der Vorlesung", ""),
            "LV-Kennung": lv_kennung,  # Generierte LV-Kennung
            "LV-Ort": row.get("LV-Ort", ""),
            "Studiengang": row.get("Studiengang", ""),
            "LV-Art": row.get("LV-Art", "Unbekannt"),  # Übernommen aus prepare_evaluation_data
            "Anzahl": participant_count,  # Anzahl der Teilnehmer
            "Sekundärdoz": None,  # Optional
            "Fragebogentyp": row.get("Fragebogentyp", "Unbekannt"),  # Übernommen aus prepare_evaluation_data
            "Semester": row.get("Semester", "")
        }])], ignore_index=True)

    # Evaluationstabelle als CSV speichern
    output_path = os.path.join(output_dir, "Steuerdatei.csv")
    evaluation_table.to_csv(output_path, index=False)

    print(f"Evaluationstabelle wurde unter folgendem Pfad gespeichert: {output_path}")
