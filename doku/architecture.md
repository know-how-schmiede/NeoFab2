# Architektur und Projektstruktur

## Stand 0.1.0

Das Repository enthält das Projektgerüst und Branding. Es gibt noch keine
lauffähige Webanwendung und keine Core-Abnahme.

Die beschlossene Zielarchitektur ist ein modularer Monolith mit Flask,
Application Factory, SQLAlchemy, Jinja und gemeinsamer Datenbank.
Bibliotheksversionen, unterstützte Python-Versionen und produktive Datenbank
werden im nächsten technischen Arbeitspaket festgelegt und geprüft.
Debian mit systemd bleibt die Planungsbasis für den Betrieb.

| Pfad | Verantwortung |
|---|---|
| `src/neofab2/core/` | Benutzer, Rechte, Einstellungen und gemeinsame Oberfläche |
| `src/neofab2/services/` | Technische Dienste, etwa Versand, Dateien und Audit |
| `src/neofab2/plugin_api/` | Versionierter Erweiterungsvertrag |
| `src/neofab2/plugins/` | Spätere eigene Fachplugins, derzeit leer |
| `src/neofab2/templates/` | Gemeinsame Jinja-Templates |
| `src/neofab2/static/branding/` | Logo für die spätere Anwendung und README |
| `assets/branding/` | Herkunft und Gestaltungsbeschreibung des Logos |
| `migrations/versions/` | Spätere explizite Migrationen mit Modulzuordnung |
| `tests/core/` | Core-Tests |
| `tests/plugin_contract/` | Prüfungen des Plugin-Vertrags |
| `tests/integration/` | Zusammenspiel, Migration und Betrieb |
| `tests/fixtures/plugins/` | Ausschließlich synthetische Testplugins |
| `doku/` | Spezifikation, Nachweise und Betriebsdokumentation |
| `script/` | Installation und Wartung |

Leere Zielverzeichnisse werden mit `.gitkeep` versionierbar gehalten. Die
vorhandenen Planungsunterlagen wurden aus `docu/` nach `doku/` verschoben,
wie in der Spezifikation vorgesehen. Es werden keine Fachplugin-Gerüste
angelegt, die bereits implementierte Fachfunktionen suggerieren.

## Nächste Arbeitspakete

1. Laufzeit- und Datenbankentscheidung, Paketmetadaten, Application Factory,
   Konfiguration, CI und erste explizite Migration (X07).
2. Benutzer, Authentifizierung, Rechte und Admin-Erstzugang (U01–U08).
3. Gemeinsames Layout, Sprachen und Einstellungen (S01–S04, S08, S12).
4. Plugin-Vertrag und synthetisches Testplugin (N01).
5. Technische Dienste, Benutzerimport und Betriebsabläufe; danach vollständige
   Core-Abnahme gemäß Projektbeschreibung.

Registrierungsregeln, produktive Datenbank sowie Rollen- und Konfliktregeln
beim Benutzerimport bleiben ausdrücklich offen.
