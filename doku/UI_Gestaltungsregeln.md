# Gestaltung von Buttons und Oberflächen – v0.1.11

Diese Regeln gelten für Core und Plugin-Oberflächen. Gemeinsame Umsetzung:
`src/neofab2/static/core.css`, Icons: `src/neofab2/templates/ui_icons.html`.
Bestehende Templates erweitern `base.html`; dadurch ist `icon()` verfügbar.
Keine externen Icon-Schriften, CDNs oder JavaScript-Abhängigkeiten erforderlich.

Die [CheckDesign-Galerie](CheckDesign.md) zeigt seit NeoFab2 0.1.11 die vorhandenen
Komponenten direkt aus diesen Quellen. Mitarbeiter und Administratoren können
dort unabhängig von Profil-/Systemeinstellungen Hell/Dunkel prüfen. Die Galerie
liest den gemeinsamen Iconbestand aus `ui_icons.html` und zeigt alle Farbvariablen.

## Buttons und Links

| Zweck | Element und Gestaltung | Icon |
|---|---|---|
| Speichern | `<button type="submit">`, gefüllte Akzentfarbe | `save` |
| Benutzer anlegen | Button oder Navigation mit `class="button"` | `user-plus` |
| Stammdaten öffnen | `<a class="button secondary" href="…">` | `database` |
| Anmelden / Abmelden | POST-Button, Abmelden mit `class="secondary"` | `login` / `logout` |
| Passwort ändern | Submit-Button | `key` |
| Sprache anwenden | Submit-Button | `language` |
| Plugin-Aktivierung / Deaktivierung vormerken | Submit-Button mit passendem Aktionstext | `play` / `pause` |
| Berechtigungsprüfung im Testplugin | Submit-Button | `shield` |
| Datei hochladen | Submit-Button | `upload` |
| Verwaltungsbereiche öffnen | Sekundäre Link-Buttons unter Administration | `users` / `plugin` / `settings` |

Jeder Button enthält links ein kleines passendes Icon **und sichtbaren Text**.
Beschriftungen benennen die Aktion, beispielsweise „Profil speichern“.
Englische Ausgangstexte mit `_()` übersetzbar halten. Keine reinen Icon-Buttons.
Bei wechselnden Aktionen müssen Icon und Beschriftung gemeinsam wechseln.

Navigation bleibt ein echtes `<a href>`; Formularaktionen verwenden `<button>`
mit explizitem `type`. Keine klickbaren `div`-Elemente und kein `role="button"`
auf Navigationslinks. Normale Menü-, Tabellen-, Rück- und Textlinks bleiben Links
ohne Button-Gestaltung; sie benötigen kein zusätzliches Icon.
Die Stammdatenpflege wird aus den Systemeinstellungen geöffnet. Benutzerliste
und Benutzerformulare enthalten keine Stammdaten-Verwaltungslinks.
Seit 0.1.10 enthält die Hauptnavigation nur den Einstieg „Administration“ für
Benutzerverwaltung, Plugin-Verwaltung und Systemeinstellungen. Die Übersichtsseite
zeigt die berechtigten Ziele als Buttons mit Icons; Unterseiten markieren den
Administrationsbereich in der Hauptnavigation. Normale Konten erhalten keinen
sichtbaren oder direkten Zugang zur Core-Administration.

## Maße, Farben und Zustände

- Schrift: vorhandene Systemschrift, Gewicht 600; Textgröße vom Kontext geerbt.
- Mindesthöhe 44 px; Standard-Innenabstand 12 px vertikal / 18 px horizontal.
  Sekundäre Buttons: 8 / 14 px bei derselben Mindesthöhe.
- Eckenradius 7 px, Rahmen 1 px. Icon 1,125 rem (bei 16 px Grundschrift: 18 px),
  Abstand zum Text 0,5 rem. SVG: 24 × 24 ViewBox, Strichstärke 2,
  runde Linienenden, `currentColor`, nicht schrumpfend.
- Primär: `--accent` als Hintergrund, `--background` für Text/Icon.
  Sekundär: transparenter Hintergrund, `--link` für Text/Icon.
  Ausschließlich gemeinsame Farbvariablen nutzen, damit Hell/Dunkel funktionieren.
- Hover und gedrückter Zustand werden über Helligkeit hervorgehoben.
  Tastaturfokus bleibt als 3-px-Umrandung sichtbar; niemals unterdrücken.
- Deaktivierte Buttons verwenden das native `disabled`-Attribut, reduzierte
  Deckkraft und einen entsprechenden Mauszeiger. `aria-disabled` allein sperrt
  einen Link technisch nicht: bei gesperrter Navigation keinen aktiven `href`
  ausgeben und den Grund sichtbar erklären. Serverrechte weiterhin prüfen.
- Texte dürfen umbrechen. Keine feste Buttonbreite oder abgeschnittenen Labels;
  Aktionsgruppen umbrechen lassen und auf schmalen Ansichten prüfen.

Icons sind dekorativ: `aria-hidden="true"` und `focusable="false"` verhindern
doppelte Screenreader-Ausgabe und zusätzliche Tabstopps. Der sichtbare Text
liefert den zugänglichen Namen. Neue Icons zentral im Makro ergänzen.

## Kopierbare Beispiele

In einem Template mit `{% extends "base.html" %}` innerhalb des Inhaltsblocks:

```jinja
<button type="submit">{{ icon('save') }} {{ _('Save changes') }}</button>
<a class="button secondary" href="{{ url_for('user_options.overview') }}">
  {{ icon('database') }} {{ _('Master data') }}
</a>
```

Unabhängige Template-Fragmente importieren das Makro ausdrücklich:

```jinja
{% from "ui_icons.html" import icon %}
```

Formulare behalten CSRF-Token, serverseitige Validierung und Rechteprüfung.
Stammdaten-Links nur bei `core.users.manage` anbieten.

## Weitere Bedienelemente

Formulare verwenden `.card-form`, sichtbare zugeordnete Labels und Hilfetexte
mit `.field-help` sowie `aria-describedby`. Pflichtfelder und Grenzen müssen
auch serverseitig gelten. Fehlermeldungen nutzen `.error` und `role="alert"`,
Erfolgsmeldungen `.notice` und bei dynamischer Rückmeldung `role="status"`.
Informationen nicht ausschließlich durch Farbe vermitteln.

Tabellen erhalten Überschrift (`caption`), Kopfzellen mit `scope` und bei Bedarf
`.table-scroll`. Wiederholte „Bearbeiten“-Links erhalten mit `.sr-only` den
Datensatznamen. Navigation verwendet `nav` mit verständlichem `aria-label`;
die aktuelle Seite wird bei entsprechenden Bereichslinks mit `aria-current`
gekennzeichnet. Abstände, Flächen und Eingaben aus dem gemeinsamen CSS übernehmen.

## Prüfung und Fehlerhilfe

Ausführungsbenutzer: Entwickler mit normalem Benutzerkonto im Repository;
Standardumgebung Windows/PowerShell mit vorhandener `.venv`:

```powershell
.venv/Scripts/python.exe -m pytest -q --basetemp (Join-Path '.test-artifacts' ('ui-' + [guid]::NewGuid().ToString('N')))
git diff --check
```

Erwartet: alle Tests bestanden und keine Whitespace-Fehler. Der eigene temporäre
Pfad vermeidet Zugriffsprobleme im allgemeinen Windows-Temp-Verzeichnis.
Für die visuelle Abnahme als Testadministrator mit synthetischen Daten anmelden:
Hell/Dunkel, schmale Ansicht, lange Beschriftungen, Tab-Fokus, Enter/Leertaste
und Formularversand prüfen. Icons müssen neben Text sichtbar bleiben.
Bei fehlenden Icons den Makroimport und Iconnamen prüfen; bei altem Design
Browsercache neu laden. Bei HTTP 403 Rechte prüfen, nicht den Zugriffsschutz entfernen.

Stand 0.1.9: gerenderte HTML-Ausgabe automatisiert geprüft; eine interaktive
visuelle Browser-Abnahme steht mangels verbundenem Browser aus.
