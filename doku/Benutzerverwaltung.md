# Benutzer anlegen und bearbeiten – v0.1.13

Seit 0.1.18: [Benutzerimport mit Vorschau und Ergebnisbericht](Core_Benutzerimport.md),
Admin-Oberfläche und lokaler CLI-Betrieb. Keine automatische Produktivübernahme.

Seit 0.1.13 unterscheidet die Liste **Wartet auf E-Mail-Aktivierung** von
gesperrten Konten. Beim administrativen Speichern eines wartenden Kontos endet
dessen E-Mail-Aktivierungsverfahren; der gewählte Aktivstatus gilt unmittelbar.
Zum Aktivieren ist dabei ein Anfangspasswort erforderlich. Passwort-, E-Mail-,
Rollen- und Statusänderungen widerrufen offene Aktivierungs-/Resetcodes.
[Selbstregistrierung und Wiederherstellung](Core_Registrierung_und_Reset.md).

Ab 0.1.7 sind die App und CLI standardmäßig englisch. Deutsche Bezeichnungen
in dieser Anleitung gelten bei gewählter deutscher Kontosprache.
[Sprachwahl und Migration 0006](Core_Sprachen.md).

Als **NeoFab2-Administrator** unter **Administration → Benutzerverwaltung** ein Konto anlegen
oder **Bearbeiten** öffnen. Beide Formulare enthalten die Felder der bereitgestellten
Vorlage; der bisherige Anzeigename bleibt für bestehende Konten erhalten.

| Feld | Vorgabe / Grenze |
|---|---|
| Anzeigename | Pflichtfeld, 1–100 Zeichen |
| E-Mail | Pflichtfeld, validiert und eindeutig |
| Rolle | Benutzer, Mitarbeiter oder Administrator |
| Sprache | Deutsch, Englisch oder Französisch; Standard Englisch (`en`); bestehende Sprachwahl bleibt erhalten |
| Konto aktiv | Neue Konten standardmäßig aktiv; kann abgewählt werden |
| Anrede | Optionaler Freitext, höchstens 50 Zeichen |
| Vorname / Nachname | Jeweils optional, höchstens 100 Zeichen |
| Adresse | Optionaler Freitext, höchstens 500 Zeichen |
| Position | Optionale Auswahl aus der Liste Positions; Namen höchstens 150 Zeichen |
| Kostenstelle | Optionale Auswahl aus Cost centers; Namen höchstens 100 Zeichen; reine organisatorische Benutzerangabe, keine Finanzverwaltung |
| Studiengang | Optionale Auswahl aus Study programs; Namen höchstens 150 Zeichen |
| Notiz | Optional, höchstens 2000 Zeichen; nur im Admin-Formular verfügbar |

Die Listen werden unter **Administration → System settings → Master data → Positions / Study programs / Cost centers**
über eigene Formulare gepflegt und starten leer. Es erfolgt keine Übernahme alter
Freitextwerte. Englische Feldhilfen sind bereits übersetzbar eingebunden.
[Bedienung, Speicherung und Fehlerhilfe](Core_Auswahllisten.md).

Neue Konten benötigen ein Startpasswort mit 8–128 Zeichen und dessen Wiederholung.
Beim Bearbeiten sind **Neues Passwort** und Wiederholung optional. Beide leer:
bisheriges Passwort bleibt. Ausgefüllt: neues Passwort wird gehasht gespeichert,
alle bisherigen Sitzungen des Kontos werden beendet. Ein Tippfehler in der
Wiederholung verhindert die gesamte Änderung. Passwörter werden bei Fehlern
nicht wieder in das Formular eingesetzt.

Kontaktdaten und Notizen werden nicht in den öffentlichen Bereich oder das
normale Benutzerprofil ausgegeben. Der Benutzer kann diese administrativen Felder
nicht über manipulierte Profilanfragen ändern. Alle Änderungen erfordern das
Admin-Recht und CSRF-Schutz. Der letzte aktive Administrator bleibt geschützt.
Die bisherige NeoFab2-Regel zur eigenen Rolle bleibt bestehen: Änderung ist möglich,
solange ein anderer aktiver Administrator erhalten bleibt. Der Screenshot ist
die Feldvorlage, keine Übernahme der alten Rollenlogik.

**Aktivierungslink senden** aus dem alten Screenshot ist keine zusätzliche
Benutzereigenschaft. E-Mail-Aktivierung und Versanddienst sind noch nicht umgesetzt;
deshalb gibt es dafür keinen funktionslosen Button.

## Update und Prüfung

Nach manuellem Commit und Push des endgültigen Standes als **root im Container**:

```bash
bash /opt/neofab2/script/upDateNeoFabService
```

Das Update sichert die Datenbank und führt `0004_user_locale` sowie
`0005_user_details` explizit aus. Bestehende Konten erhalten Sprache `de` und
leere neue Zusatzfelder; vorhandene Passwörter und Daten bleiben erhalten.
Keine Übernahme realer Daten aus dem alten NeoFab oder dem Screenshot.

Prüfen: synthetisches Testkonto mit Zusatzfeldern anlegen, erneut öffnen und
Werte vergleichen. Notiz ändern, Sprache auf Englisch setzen und erneut laden.
Ein inaktives Konto darf sich nicht anmelden. Anschließend aktivieren und mit
dem Startpasswort anmelden. Beim Admin-Passwortwechsel müssen alte Sitzungen enden.
Ein ungültiger Feldwert darf keine anderen Änderungen teilweise speichern.

Bei fehlender Schema-Bereitschaft das Update-/Migrationsprotokoll prüfen;
keine Datenbankspalten manuell anlegen. Sprachabdeckung und Prüfschritte sind
unter [Sprachwahl](Core_Sprachen.md) beschrieben. Der Container-Test der neuen
Formulare und die interaktive visuelle Abnahme stehen noch aus.
