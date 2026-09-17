# Arbeitsregeln für NeoFab2

- Vor jedem Arbeitspaket `doku/NeoFab2_Projektbeschreibung.md` und `doku/NeoFab2_Funktionsmatrix.md` lesen. Betroffene Funktions-IDs benennen und den Umsetzungsnachweis mit Pfaden, Status, Prüfungen und Abweichungen aktualisieren.
- Zuerst ausschließlich den Core mit einem Testplugin umsetzen und seine Abnahmekriterien prüfen. Produktive Fachplugins erst nach Core-Abnahme; neue Modulvorschläge vor Umsetzung entscheiden.
- Das alte NeoFab und produktive Daten unverändert lassen. Keine Produktivmigration oder Löschung ohne gesonderten Auftrag. Nur synthetische Testdaten verwenden.
- Core, technische Dienste, Plugin-Vertrag und Plugins getrennt halten. Keine Fachplugin-Abhängigkeiten im Core. Schemaänderungen ausschließlich durch explizite versionierte Migrationen.
- `doku/` und `script/` beibehalten. Vertraute Bedienung von Installation, Service, Update und Notfall-Passwort-Reset erhalten; eigene NeoFab2-Pfade und Dienstnamen verwenden. Alte Skripte nicht ungeprüft übernehmen.
- Deutsche Anleitungen mit kopierbaren Befehlen, Ausführungsbenutzer, Standardwerten, Ergebnisprüfung und Fehlerhilfe schreiben. Schnellstart: `script/README.md`; Details: `doku/SETUP.md`.
- Zentrale Version: `src/neofab2/version.py`. Anfangsversion ist `0.1.0`; Schema MAJOR.MINOR.PATCH. Ohne Versionsauftrag keine Versionsanhebung.
- Bei angeforderter Versionsänderung Versionsangaben und `doku/Version_Timeline.md` gemeinsam aktualisieren. Datum, tatsächliche Änderungen, Prüfungen, Betriebs-/Migrationshinweise und kopierbaren Commit-Titel samt Beschreibung aufnehmen.
- Kein automatischer Git-Commit und kein Push. Der Benutzer erstellt den Commit manuell in GitHub Desktop.
- Fortschritt nachvollziehbar dokumentieren. Geplante, ungeprüfte oder nur vorbereitete Funktionen nicht als fertig melden.
