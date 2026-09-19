# Plugin-Rechte, Testdateien und Administration – 0.1.10

Paket 0 des [Core-Arbeitsplans](Core_Naechste_Schritte.md), IDs N01, U06, S10,
S01/S12 und X05–X07. Keine Fachfunktionen und keine vollständige Core-Abnahme.

## Administration bedienen

Als **angemeldeter NeoFab2-Administrator** den Menüpunkt **Administration**
öffnen (`/admin`). Dort stehen Buttons mit Icons für **User management**,
**Plugins** und **System settings**. Die bisherigen Zieladressen funktionieren
weiterhin. Die Hauptnavigation enthält diese drei Einzelverweise nicht mehr.
Stammdaten erreichen Sie über **Administration → System settings → Master data**.

Der Einstieg und jeder Bereich prüfen die vorhandenen Core-Rechte. Benutzer und
Mitarbeiter sehen keinen Administrationseintrag und erhalten bei direktem Zugriff
HTTP 403; Gäste werden zur Anmeldung weitergeleitet. Plugin-Fachrechte erteilen
keine Core-Administrationsrechte.

## Mehrere Rechte in API 1

Der Vertrag ist abwärtskompatibel erweitert: bestehende `Plugin`-Definitionen
mit `<kennung>.access` funktionieren unverändert. Zusätzliche Rechte stehen in
`permissions`, beispielsweise:

```python
from neofab2.plugin_api import Permission, FilePolicy

permissions = (
    Permission("example.upload", ("user", "staff", "admin")),
    Permission("example.read_own", ("user", "staff", "admin")),
    Permission("example.read_all", ("staff", "admin")),
)
files = FilePolicy("example.upload", "example.read_own", "example.read_all")
```

Diese Werte als `permissions=` und `files=` der eigenen `Plugin`-Definition
übergeben. Rechte müssen eindeutig sein und zum Plugin-Namensraum gehören.
Die Registry verwirft fremde/duplizierte Rechte, unbekannte oder leere Rollenlisten
und ungültige Dateirichtlinien auch bei noch deaktivierten Plugins.
`employee` bleibt die fachliche Bezeichnung für `staff`, kein neuer Speicherwert.
Es gibt keinen Admin-Wildcard: `admin` muss je Recht ausdrücklich genannt werden.
Eine Plugin-Abhängigkeit gewährt keine Rechte auf die Seiten der Abhängigkeit.

Öffentliche Helfer unter `neofab2.plugin_api`:

- `has_permission(user, permission)` prüft aktives Konto und aktive Plugin-Rechte.
- `permission_required(permission)` schützt einzelne Flask-Aktionen zusätzlich
  zum allgemeinen Blueprint-Zugriff. Menüausblendung allein reicht nicht aus.
- `owns_or_allowed(user, owner_id, own_permission, all_permission)` erlaubt
  Zugriff nur mit ausdrücklich zugewiesenem Gesamtzugriff oder bei passender
  Besitzer-ID **und** Eigenzugriffsrecht. Die Besitzer-ID muss vom gespeicherten
  Objekt kommen, nicht aus Formularparametern.

Die festen Core-Rollen bleiben bestehen; eine Rollenpflege ist Paket 4.

## Minimaler Dateivertrag

Die öffentliche Schnittstelle `neofab2.plugin_api.files` bietet innerhalb eines
authentifizierten Requests:

```python
from neofab2.plugin_api.files import store_file, list_files, download_file

# upload ist ein werkzeug FileStorage aus request.files.
file_id = store_file("example", upload)
entries = list_files("example")
# In einer Downloadroute als Flask-Antwort zurückgeben:
response = download_file("example", file_id)
```

`list_files` liefert nur zugängliche Metadaten ohne Dateiinhalte. Der technische
Dienst lädt den Kontostatus erneut aus der Datenbank und prüft Plugin-Aktivierung,
Zugriffsrecht und die deklarierten Datei-Rechte. Besitzer ist immer das angemeldete
Konto; gesendete Besitzer-/Modulfelder werden nicht übernommen. Fremde oder
unbekannte Datei-IDs liefern beim Download 404. Plugin-Code ist vertrauenswürdig,
keine Sandbox; jedes Plugin verwendet seine eigene feste Kennung.

`FilePolicy` erlaubt standardmäßig `.txt` und **262144 Bytes (256 KiB)** pro Datei.
Der Vertrag begrenzt konfigurierbare Dateigrößen auf 1 MiB. Zusätzlich gilt das
vorhandene HTTP-Request-Limit von 1 MiB einschließlich Multipart-Overhead.
Erweiterungen müssen mit Punkt und Kleinbuchstaben/Ziffern angegeben werden.
Leere Dateien, fremde Erweiterungen, Pfadtrenner, Laufwerkspräfixe, Steuerzeichen
und Namen über 200 Zeichen werden zurückgewiesen. Akzeptierte Namen werden mit
`secure_filename` normalisiert; die Datei-ID ist eine zufällige Kennung.

Die neue Tabelle `core_files` speichert Modul, Besitzer, Name, Größe, Zeitpunkt
und Inhalt atomar als SQLite-BLOB. Es entstehen keine benutzergesteuerten Pfade
oder öffentlich erreichbaren Upload-Verzeichnisse. Die bestehende SQLite-
Sicherung enthält Dateien und Metadaten gemeinsam. Besitzer-Fremdschlüssel
verhindern versehentliches Löschen zugeordneter Konten.

Downloads sind stets Anhänge mit `application/octet-stream`, `nosniff` und
`no-store`. Die Erweiterungsprüfung ist **keine** Inhaltsprüfung oder
Virenerkennung. Keine Inline-Vorschau oder Ausführung hochgeladener Inhalte.
Große Fertigungsdateien, Streaming, Kontingente, Löschung/Bereinigung, fachliche
Objektzuordnung und Viewer werden erst in späteren Paketen umgesetzt.

## Synthetischen Test durchführen

Vorgabe: keine aktiven Plugins (`ENABLED_PLUGINS = []`), keine Testdateien.
Als **Administrator** unter **Administration → Plugins** zuerst `core_test`,
dann `management_test` aktivieren und alle Anwendungsprozesse kontrolliert neu
starten (siehe [Plugin-Betrieb](plugin-development.md)).

Das Verwaltungs-Testplugin zeigt nun einen Datei-Upload mit Icon und Hilfetext:

| Konto | Testdateien | Formularzugriff testen | Administration |
|---|---|---|---|
| Benutzer | Hochladen, eigene auflisten/herunterladen | verboten | verboten |
| Mitarbeiter (`staff`) | Hochladen, alle Dateien dieses Testplugins lesen | erlaubt | verboten |
| Administrator | Hochladen, alle Dateien dieses Testplugins lesen | erlaubt | erlaubt |

Als **lokaler Testbenutzer** eine synthetische Datei erstellen (PowerShell):

```powershell
Set-Content -Encoding utf8 -LiteralPath "$env:TEMP/neofab2-test.txt" -Value 'Synthetic NeoFab2 upload test'
```

1. Mit Testkonto A die Datei hochladen; Downloadinhalt vergleichen.
2. Als Testkonto B prüfen: Datei fehlt in der Liste; direkte Downloadadresse
   von A liefert 404. Keine echten Benutzerdateien verwenden.
3. Als Mitarbeiter prüfen: beide Testkonten-Dateien lesbar, Core-Verwaltung 403.
4. Leere Datei, falsche Erweiterung und Datei über 256 KiB zurückweisen lassen.
5. `management_test` deaktivieren und neu starten: direkte Routen sind 404,
   Aufgabe gesperrt. Daten bleiben für erneute Aktivierung erhalten.

Fehlerhilfe: HTTP 400 bedeutet fehlende/ungültige Datei oder CSRF-Formularfehler;
Seite neu öffnen und Dateiname/Typ prüfen. HTTP 413: Datei verkleinern. HTTP 403:
Kontostatus und konkrete Rechte prüfen. HTTP 404: Besitzer, Plugin-Zuordnung und
Aktivierung prüfen. HTTP 503: `neofab2 check` und explizite Migration prüfen.

## Update und Prüfung

Nach manuellem Commit/Push als **root im NeoFab2-Testcontainer**, Standardpfade:

```bash
bash /opt/neofab2/script/upDateNeoFabService
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version **0.1.10**, `Database and schema ready.`. Die explizite Revision
`0008_core_files` folgt auf `0007_user_options`; sie legt eine leere Tabelle an,
ohne Konten oder bestehende Listen zu verändern. Kein Schema-Update beim Start.
Vor Update Sicherung prüfen; Wiederherstellung gemäß [Betriebsanleitung](operations.md).

Als **Entwickler im Repository**, Windows/PowerShell:

```powershell
.venv/Scripts/python.exe -m pytest -q --basetemp (Join-Path '.test-artifacts' ('core010-' + [guid]::NewGuid().ToString('N')))
git diff --check
```

Die automatisierten Nachweise stehen in `tests/plugin_contract/test_files.py`
und den bestehenden Core-/Plugin-/Migrationstests. Browser- und echter
Debian-/LXC-Lauf bleiben gesonderte Abnahmen; keine Produktivdaten wurden verwendet.
