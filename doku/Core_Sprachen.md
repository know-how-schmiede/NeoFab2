# Sprachwahl – Stand v0.1.9

Englisch ist die Ausgangssprache, die Standardsprache für Gäste ohne Auswahl
und neue Konten sowie der Fallback (S02/U07). Deutsch und Französisch werden
als Übersetzungen behandelt. Gespeicherte Kontosprachen haben weiterhin Vorrang
vor der Gast-Auswahl; bestehende deutschsprachige Konten bleiben deutsch.

## Umsetzung

- Englische Texte und Übersetzungsschlüssel für Startseite, Navigation, Anmeldung,
  Profil, Benutzerverwaltung, Systemeinstellungen und beide synthetischen Testplugins.
- `src/neofab2/core/i18n.py`: `MESSAGES` verwendet englische Schlüssel mit
  sprachbezogenen Werten, etwa `"Sign in": {"de": "Anmelden", "fr": "Se connecter"}`.
  In Templates sind übersetzbare Texte an `_("English source text")` erkennbar.
  Platzhalter werden nach Übersetzung eingefügt und anschließend HTML-maskiert.
- Deutsche Übersetzungen bleiben verfügbar. Die bisherige französische Abdeckung
  bleibt erhalten; fehlende französische Texte erscheinen englisch. Technische,
  dynamische Plugin-Diagnosen können ebenfalls auf Englisch zurückfallen.
- CLI-Hilfe, Rückmeldungen und Fehlermeldungen sind englisch. Deutsche
  Betriebsanleitungen und die vertrauten Shell-Skripte bleiben erhalten.
- Benutzerdefinierte Begrüßungen, Werkstattnamen, Notizen und andere gespeicherte
  Inhalte werden weder automatisch übersetzt noch überschrieben. Neue öffentliche
  Standardtexte sind englisch.

Neue Meldungen immer als vollständigen englischen Text anlegen. Übersetzungen
ergänzen denselben Schlüssel; keine deutschen Ausgangsschlüssel einführen.
Technische Werte wie `enable`, `disable`, Rollen-IDs und Sprachcodes bleiben
unübersetzte Protokollwerte. Eigene Plugin-Kataloge und vollständige französische
Abdeckung bleiben Teil des weiteren S02-/N01-Ausbaus.

## Ergänzung 0.1.8

Englische Feldhilfen und Benutzer-Auswahllisten sind ergänzt. Die Hilfetexte
verwenden bereits `_()`; ihre DE-/FR-Übersetzungen folgen später. Individuelle
Listennamen sind Benutzerdaten. [Details](Core_Auswahllisten.md).

## Bedienung

Gast: `/login` öffnen, unter **Language** die Sprache wählen und **Apply language**
betätigen. Angemeldet: unter **My profile / Mein Profil** die Kontosprache wählen
und **Save profile / Profil speichern** betätigen. Für eine bisher deutsche
Installation im eigenen Profil **English** auswählen. Die Auswahl bleibt nach
erneuter Anmeldung erhalten. Abmeldung und Passwortwechsel erhalten sie auch
für die folgende Anmeldeseite. Unbekannte Sprachcodes werden beim Speichern
abgewiesen; beschädigte gespeicherte Sprachcodes fallen auf Englisch zurück.

## Update und Prüfung im Container

Voraussetzung: 0.1.9 wurde vom Benutzer manuell committed und auf den verwendeten
Remote-Branch übertragen. Als **root im NeoFab2-Testcontainer**:

```bash
bash /opt/neofab2/script/upDateNeoFabService
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version `0.1.9` und `Database and schema ready.`. Die explizite Migration
`0006_english_default` ändert ausschließlich den Datenbank-Standard für neue
Kontosprachen auf `en`. Bestehende Kontosprachen, Hashes, Zusatzfelder,
Einstellungen und E-Mail-Eindeutigkeit bleiben erhalten. SQLite baut dazu die
Benutzertabelle über Alembic kontrolliert neu auf; vorherige Sicherung behalten.
Keine Migration beim Start oder beim Seitenaufruf.

1. In einem frischen privaten Browserfenster `/login` öffnen: **Sign in**.
2. Als Admin Englisch im Profil wählen; Benutzer-, Einstellungs- und Plugin-Seiten prüfen.
3. Ein synthetisches Konto anlegen: Vorgabe **English**.
4. Deutsch wählen: **Mein Profil**, **Benutzer anlegen**, **Werkstattname**.
5. Französisch wählen: **Mon profil**; noch nicht übersetzte Admin-Texte englisch.
6. Ab- und wieder anmelden: Kontosprache bleibt erhalten.

Fehlerhilfe: Bei weiterhin deutscher Oberfläche zuerst die gespeicherte Profil-
oder Gast-Auswahl prüfen. Eigene deutsche Startseitentexte unter **System settings**
selbst bearbeiten. Bei fehlender Datenbankbereitschaft Update-Ausgabe und Migration
prüfen; nicht die vorhandene Datenbank löschen. Vollständige Container-/Browser-
und Core-Abnahme stehen weiterhin aus.
