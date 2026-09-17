# NeoFab2 – Versionshistorie

## Version 0.1.0 – 2026-09-17

Bereich: Projektgerüst / Distribution / Branding.

### Änderungen

- Ordnerstruktur für Core, Dienste, Plugin-API, spätere Plugins, Templates,
  statische Dateien, Migrationen und Tests vorbereitet.
- Planungsunterlagen von `docu/` nach `doku/` verschoben.
- Dauerhafte Arbeitsregeln in `AGENTS.md` festgehalten.
- Zentrale Anfangsversion in `src/neofab2/version.py` angelegt.
- Neues NeoFab2-Logo erstellt und in der README eingebunden.
- Architektur, Installationsstand und nächste Arbeitspakete dokumentiert.

### Betrieb und Migration

Keine Migration erforderlich. Noch keine startfähige Anwendung, keine
Installationsskripte und keine Core-Abnahme. Das alte NeoFab bleibt unverändert.

### Prüfungen

- Logo visuell auf Schriftzug, Motiv und Lesbarkeit geprüft.
- Verzeichnisstruktur, Dokumentationslinks und Versionsangabe geprüft.
- `git diff --check`: bestanden.
- Keine Anwendungstests: Laufzeit und Application Factory noch nicht eingerichtet.
  Der lokale Aufruf `python --version` scheiterte an einem Windows-Anmeldesitzungsfehler.

### Commit für GitHub Desktop

Commit-Titel:

```text
0.1.0: NeoFab2-Projektstruktur und neues Logo anlegen
```

Commit-Beschreibung:

```text
Grundstruktur für Core, Dienste, Plugin-API, Migrationen und Tests vorbereiten.
Projektunterlagen unter doku bündeln und dauerhafte Arbeitsregeln festhalten.
Zentrale Version 0.1.0 sowie neues NeoFab2-Logo mit README-Einbindung ergänzen.
Architektur, Installationsstand und Funktionsnachweis dokumentieren.
Struktur, Links, Versionsangabe und Logo geprüft; git diff --check bestanden.
Noch keine startfähige Anwendung oder Datenmigration.
```

Der Commit wird manuell in GitHub Desktop erstellt.
