import pandas as pd
import os
from difflib import get_close_matches

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
        dozent_name = row['Dozent'].strip().lower()
        professor_info = professor_data[professor_data['Nachname'].str.lower() == dozent_name]

        if professor_info.empty:
            # Finde den ähnlichsten Nachnamen, falls keine exakte Übereinstimmung vorliegt
            similar_names = get_close_matches(dozent_name, professor_data['Nachname'].str.lower().tolist(), n=1, cutoff=0.6)
            if similar_names:
                professor_info = professor_data[professor_data['Nachname'].str.lower() == similar_names[0]]

        if not professor_info.empty:
            professor_row = professor_info.iloc[0]
            professional_title = professor_row.get("Titel", None)
            firstname = professor_row.get("Vorname", "")
            surname = professor_row.get("Nachname", "")
            email = professor_row.get("E-Mail-Adresse", "")
        else:
            professional_title = None
            firstname = "Unbekannt"
            surname = row.get("Dozent", "")
            email = "Nicht verfügbar"

        # Teilnehmerliste laden und Anzahl bestimmen
        participants_file = os.path.join(output_dir, f"participants_{row['Name der Vorlesung']}.csv")
        if os.path.exists(participants_file):
            participants_data = pd.read_csv(participants_file)
            course_participants = max(len(participants_data) - 1, 0)  # Anzahl der Teilnehmer minus 1
        else:
            course_participants = 0

        evaluation_table = pd.concat([evaluation_table, pd.DataFrame([{
            "Funktion": "Dozent",  # Alle sind Dozenten
            "Anrede": "Herr/Frau",  # Beispiel-Anrede
            "Titel": professional_title,  # Titel des Dozenten
            "Vorname": firstname,
            "Nachname": surname,
            "E-Mail": email,
            "LV-Name": row.get("Name der Vorlesung", ""),
            "LV-Kennung": row.get("Kuerzel", ""),
            "LV-Ort": row.get("LV-Ort", ""),
            "Studiengang": row.get("Studiengang", ""),
            "LV-Art": row.get("Veranstaltungsart", ""),
            "Anzahl": course_participants,  # Anzahl Teilnehmer minus 1
            "Sekundärdoz": None,  # Optional
            "Fragebogentyp": "Standard",  # Fragebogentyp (Standard)
            "Semester": row.get("Semesterzug", "")
        }])], ignore_index=True)

    # Evaluationstabelle als CSV speichern
    output_path = os.path.join(output_dir, "evaluation_table.csv")
    evaluation_table.to_csv(output_path, index=False)

    print(f"Evaluationstabelle wurde unter folgendem Pfad gespeichert: {output_path}")
