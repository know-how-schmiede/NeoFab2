# Architektur – Stand v0.1.2

## Erster Core-Schritt

Modularer Monolith mit Flask-Application-Factory, SQLAlchemy und Jinja.
`create_app()` lädt Konfiguration und Routen, erzeugt aber keine Datenbank
und führt keine Migration aus. Core startet ohne Fachplugins.
Zentrale Version: `src/neofab2/version.py` für Paket, CLI und Oberfläche.

Laufzeitbereich: Python 3.12/3.13. Installer: Debian 13/Python 3.13.
Lokal geprüft: Windows/Python 3.12. Abhängigkeiten haben kompatible Bereiche
in `pyproject.toml`, noch keine vollständig gesperrte transitive Liste.
Updates können deshalb neuere Versionen innerhalb dieser Bereiche installieren.
Das Update sichert auch die bisherige virtuelle Umgebung.

SQLite dient der ersten Testinstallation. Keine Zusage für PostgreSQL/MariaDB
oder produktive Last. Die endgültige produktive Datenbankentscheidung bleibt offen.

| Pfad | Verantwortung |
|---|---|
| `src/neofab2/__init__.py` | Factory und gemeinsame HTTP-Header |
| `src/neofab2/config.py` | TOML-Konfiguration und Validierung |
| `src/neofab2/database.py` | Engine, Schema-Check und Migration |
| `src/neofab2/cli.py` | Konfiguration, Migration, Check, SQLite-Backup |
| `src/neofab2/core/` | Startseite, Health, Benutzerregeln, Anmeldung und Rechte |
| `src/neofab2/templates/`, `static/` | Layout, CSS, Logo |
| `migrations/` | Zentrale Revisionen; als `neofab2.migrations` im Wheel |
| `src/neofab2/services/`, `plugin_api/`, `plugins/` | Vorbereitete Zielbereiche |
| `tests/` | Core, CLI, Restore, simulierte Update-Steuerung |
| `script/` | Debian-Installation und Wartung |
| `.github/workflows/core.yml` | Vorbereitete Linux-CI für Python 3.12/3.13 |

Revision `0001_core_settings` legt nur die leere Core-Einstellungstabelle an.
Noch keine Einstellungsoberfläche; Secrets liegen ausschließlich in der
geschützten TOML-Datei. Migrationen laufen nur über `neofab2 migrate`,
niemals über `create_all()` oder HTTP-Routen.

`0002_core_users` ergänzt Benutzer, serverseitige Sitzungen und zeitlich
begrenzte Loginversuchszähler. SQLAlchemy Core verwendet explizite Transaktionen;
`BEGIN IMMEDIATE` serialisiert Erstadmin-Anlage und Letzter-Admin-Prüfung in
SQLite. Fremdschlüssel sind aktiviert. Es werden keine Benutzer migriert oder
automatisch mit einer Migration angelegt.

Passwörter werden über Werkzeug/scrypt gehasht, Formulare durch Flask-WTF
gegen CSRF geschützt. Das signierte Flask-Cookie enthält einen zufälligen
Sitzungstoken, keine Rechte oder Passwörter. Sein SHA-256-Hash verweist auf
die serverseitige Sitzung. Rollen/Kontostatus werden bei jedem Seitenzugriff
aus der Datenbank gelesen. [Zugangsvertrag und Konfiguration](Core_Zugang.md).

`/health/live` prüft den HTTP-Prozess. `/health/ready` prüft Datenbank,
Alembic-Stand und Core-Tabelle. Falscher/fehlender Stand liefert 503;
Antworten enthalten keine internen Pfade oder SQL-Fehler.

## Grenzen und Abweichungen

S01 umfasst Startseite, Profil und Benutzerverwaltung; Plugin-Navigation folgt.
S12 für die Core-Version umgesetzt; Plugin-Versionen folgen mit N01.
U01, U08 und die lokale Wiederherstellung X04 sind umgesetzt. U05 umfasst
Anlegen/Bearbeiten/Aktivieren/Deaktivieren, noch kein Löschen. U06 verwendet die
festen Rollen Benutzer/Mitarbeiter/Administrator; Plugin-Rechte und Importzuordnung
folgen. U07 umfasst Anzeigename und Passwortwechsel; Sprache/Design folgen.
U02–U04, S02–S11, N01, N04 und N05 bleiben offen.

Die drei vertrauten Betriebsskriptnamen und interaktive Bedienung bleiben.
Bewusste Abweichung: Benutzer/Pfade für die erste neue Installation fest auf
NeoFab2 begrenzt. Admin-Fragen und Notfall-Passwort-Reset sind jetzt enthalten.
Der Update-Funktionskörper wird vor Git vollständig eingelesen, damit die
laufende Skriptdatei selbst aktualisiert werden kann.

## Nächste Arbeitspakete

1. Profileinstellungen für Sprache/Design sowie Systemeinstellungen ausbauen.
2. Selbstregistrierung und E-Mail-Verfahren mit dem Versanddienst umsetzen.
3. Versionierter Plugin-Vertrag und synthetisches Testplugin.
4. Technische Dienste und Benutzerimport mit abgestimmten Konfliktregeln.
5. Echter Debian-/Proxmox-Installations-, Update- und Wiederherstellungstest;
   vollständige Core-Abnahme vor Fachplugins.

Offen: Registrierungsregeln, Rollen-/Konfliktzuordnung beim Import, produktive
Datenbank und Umstellungstermin. Keine Datenübernahme in v0.1.2.

## Referenzen

- [Flask Application Factory](https://flask.palletsprojects.com/en/stable/tutorial/factory/)
- [Alembic: programmatische Konfiguration](https://alembic.sqlalchemy.org/en/latest/api/config.html)
- [Debian 13: Python 3.13](https://packages.debian.org/trixie/python3.13)
- [Flask-WTF: CSRF](https://flask-wtf.readthedocs.io/en/latest/api/)
- [Werkzeug: Passwort-Hashing](https://werkzeug.palletsprojects.com/en/stable/utils/)
