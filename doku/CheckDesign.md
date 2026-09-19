# CheckDesign 0.1.0 – Designprüfung in NeoFab2 0.1.11

CheckDesign ist ein ausdrücklich beauftragtes technisches Core-Testplugin zur
Sichtprüfung der Oberfläche, kein Fachplugin. Kennung: `checkdesign`, Plugin-API 1,
eigene Version **0.1.0**, keine Plugin-Abhängigkeiten und keine eigenen Tabellen.
Die [Gestaltungsregeln](UI_Gestaltungsregeln.md) bleiben die gemeinsame Grundlage.

## Aktivieren und öffnen

Ausführungsbenutzer: **NeoFab2-Administrator**. Nach Update auf 0.1.11 unter
**Administration → Plugins** bei **CheckDesign** die Aktivierung vormerken.
Anschließend alle Anwendungsprozesse kontrolliert neu starten; siehe
[Plugin-Betrieb](plugin-development.md). Als **root im NeoFab2-Testcontainer**
mit dem Standarddienst:

```bash
systemctl restart neofab2.service
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: NeoFab2 **0.1.11**, `Database and schema ready.` und CheckDesign in
der laufenden Plugin-Auswahl aktiv. Es ist keine neue Schema-Revision nötig;
der Stand bleibt `0008_core_files`.

Danach erscheint **CheckDesign** als eigener Hauptmenüpunkt für angemeldete
**Mitarbeiter (`staff`) und Administratoren (`admin`)**. Die Adresse lautet
`/plugins/checkdesign/`. Normale Benutzer erhalten keinen Menüeintrag und bei
direktem Zugriff HTTP 403. Gäste werden zur Anmeldung weitergeleitet.
Mitarbeiter dürfen das Plugin nutzen, aber nicht die zentrale Plugin-Verwaltung.

Standard: CheckDesign ist installiert, aber nicht automatisch aktiviert.
Bestehende Aktivierungsauswahlen bleiben unverändert. Es kann unabhängig von
`core_test` und `management_test` betrieben werden. Nach Deaktivierung und
Neustart sind Seite, Stylesheet und Menüeintrag nicht mehr verfügbar.

## Hell und Dunkel direkt prüfen

Oben auf der Plugin-Seite **Hell / Light** oder **Dunkel / Dark** wählen.
Beide Buttons enthalten ein passendes Icon; der aktive Zustand ist farblich und
mit `aria-pressed` gekennzeichnet. Der Wechsel lädt die Vorschau neu und setzt
ausprobierte Beispielfelder zurück. Er benötigt kein JavaScript.

Die Auswahl gilt ausschließlich für diese Vorschauseite, einschließlich des
gemeinsamen Kopfbereichs, Menüs und Fußbereichs. Weder Profil noch Systemvorgabe
werden gespeichert oder geändert. Beim Wechsel zu anderen Seiten gilt sofort
wieder die persönliche Darstellung bzw. Systemvorgabe. Andere Sitzungen bleiben
unberührt. **Aktuelle Darstellung verwenden / Use current appearance** entfernt
die Vorschauauswahl. Ohne Auswahl gilt zunächst das reguläre Kontodesign.

Direkte Vorschauadressen:

```text
/plugins/checkdesign/?theme=light
/plugins/checkdesign/?theme=dark
```

Andere Theme-Werte werden mit HTTP 400 abgelehnt. Es gibt keinen Schreibendpunkt.

## Enthaltene Gestaltungselemente

| Bereich | Beispiele |
|---|---|
| Gemeinsamer Rahmen | Logo, Seitentitel, Hauptnavigation, Administrationseinstieg nach Recht, Abmelden, Footer mit Core-Version |
| Typografie | Eyebrow, Haupt-/Abschnitts-/Unterüberschriften, Einleitung, Fließtext, Hervorhebungen, Hilfetext, mehrzeiliger Text, Listen, Code/Tastaturhinweise |
| Farben | Alle 15 gemeinsamen CSS-Farbvariablen als beschriftete Flächen; Werte stammen direkt aus Hell-/Dunkel-Theme |
| Buttons/Links | Primär, sekundär, deaktivierte Varianten, echte Navigationslinks in Buttonform, gesperrter Link ohne Ziel, langer Buttontext, Textlink |
| Icons | Alle Icons des gemeinsamen Makros, automatisch aus demselben Bestand, einschließlich Sonne/Mond |
| Formulare | Text, E-Mail, Passwort, Zahl, Auswahl, Textarea, Checkbox, Radio, Dateiauswahl, Hilfe, Pflichtfeld, readonly, disabled, aria-invalid |
| Native Zusatzfelder | Suche, Datum, Zeit, Schieberegler, Fortschritt und aufklappbarer Bereich; Browserdarstellung ausdrücklich gekennzeichnet |
| Rückmeldungen | Hinweis mit Statusrolle, klar als Beispiel markierte Fehlermeldung, Badge und Hilfetext |
| Tabellen/Navigation | Synthetische Datensätze, Kopfzellen/Caption, lange Inhalte, Bearbeiten-Link mit zugänglichem Datensatznamen, Seitennavigation, leerer Zustand |
| Layout | Karten, Rahmen, Abstände, Rundungen, schmale Ansichten, echte gemeinsame CSS-Komponenten |

Die Galerie verwendet die tatsächlichen Core-Komponenten. Plugin-CSS ergänzt nur
Galerieanordnung und Farbmuster; es kopiert keine alternativen Button- oder
Formularstile. Noch nicht implementierte Fachkomponenten wie Viewer gehören nicht
zu diesem Plugin. Beispiele benötigen keine echten Daten: Beispielfelder liegen
außerhalb absendbarer Formulare, Buttons führen keine Speicheraktion aus,
Dateiauswahl wird weder gelesen noch hochgeladen. Sprunglinks bewegen innerhalb
der Seite. Englische Ausgangstexte, deutsche Bereichs-/Bedienbezeichnungen;
fehlende Detailübersetzungen und Französisch fallen weiterhin auf Englisch zurück.

## Prüfanleitung und Fehlerhilfe

Ausführungsbenutzer: **Mitarbeiter oder Administrator mit synthetischem Testkonto**.

1. Beide Designs durchschalten und Kontrast von Text, Rahmen, Hilfen und Icons prüfen.
2. Mit Tab/Shift+Tab alle aktiven Elemente erreichen; Fokusrahmen prüfen.
   Maus über Buttons bewegen, gedrückten Zustand ansehen und Beschriftungen lesen.
3. Beispielfelder bedienen, Checkboxen/Radio wechseln, Auswahl öffnen.
   Deaktivierte Elemente dürfen keine Aktion auslösen.
4. Browser schmal ziehen und bei Bedarf vergrößern: lange Labels, Karten,
   Formularbreiten und Tabellen kontrollieren. Native Controls variieren je Browser.
5. Zum Profil wechseln: Kontodesign muss unverändert sein. Mit normalem
   Benutzer Direktzugriff ablehnen lassen; nach Deaktivierung/Neustart 404 prüfen.

Für automatisierte Prüfung als **Entwickler**, im Repository unter PowerShell:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/plugin_contract/test_checkdesign.py --basetemp (Join-Path '.test-artifacts' ('checkdesign-' + [guid]::NewGuid().ToString('N')))
git diff --check
```

Erwartet: sechs Tests bestanden und keine Whitespace-Fehler. Bei fehlendem Menü
gespeicherte und laufende Aktivierung sowie Rolle prüfen. Bei 403 mit einem
Mitarbeiter-/Administratorkonto anmelden; keine Berechtigungsprüfung entfernen.
Bei 404 Aktivierung und Neustart prüfen, bei 400 Theme-Parameter entfernen.
Bei fehlenden Farbfeldern oder altem Design Browsercache neu laden und den
korrekt ausgelieferten Plugin-Stylesheet-Pfad prüfen.

Automatisiert geprüft: Rechte/Navigation/Assets, Aktivierung/Deaktivierung,
Theme-Isolation, fehlende Speichervorgänge, Icon-/Farbbestand, IDs und Labels.
Eine visuelle Browserabnahme bleibt offen, da kein Browser verbunden war.
