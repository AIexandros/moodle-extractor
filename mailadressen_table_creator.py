import pandas as pd
import os

def create_mailadressen_table(courses_to_evaluate, output_dir):
    """
    Erstellt eine Tabelle mit LV-Kennung und den E-Mail-Adressen der Teilnehmer.
    Speichert die Tabelle im Ausgabe-Ordner.
    """
    all_emails = []

    # Alle Kurse durchgehen
    for _, row in courses_to_evaluate.iterrows():
        course_name = row['Name der Vorlesung']
        participants_file = os.path.join(output_dir, f"participants_{course_name.replace(' ', '_')}.csv")

        # Prüfen, ob die Teilnehmerliste existiert
        if os.path.exists(participants_file):
            df = pd.read_csv(participants_file)

            # Prüfen, ob die Spalte 'E-Mail-Adressen' vorhanden ist
            if 'E-Mail-Adresse' in df.columns:
                # LV-Kennung und E-Mail-Adressen extrahieren
                for email in df['E-Mail-Adresse'].dropna():
                    all_emails.append({'LV-Kennung': course_name, 'E-Mail-Adresse': email})
            else:
                print(f"Warnung: Keine E-Mail-Spalte in {participants_file} gefunden.")
        else:
            print(f"Warnung: Datei {participants_file} existiert nicht.")

    #TODO LV Kennung einbauen anstatt course_name
    
    # Daten in eine neue Tabelle speichern
    if all_emails:
        email_table = pd.DataFrame(all_emails)
        output_file = os.path.join(output_dir, "mailadressen_table.csv")
        email_table.to_csv(output_file, index=False)
        print(f"Mailadressen-Tabelle erfolgreich erstellt: {output_file}")
    else:
        print("Keine E-Mail-Adressen gefunden. Die Tabelle wurde nicht erstellt.")
