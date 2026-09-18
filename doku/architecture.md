# Architektur – Stand v0.1.6

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
| `src/neofab2/plugin_api/` | API-1-Vertrag, Katalog und Abhängigkeitsprüfung |
| `src/neofab2/plugins/` | Zwei synthetische Testplugins, bei neuer Installation deaktiviert |
| `src/neofab2/services/` | Vorbereiteter Zielbereich |
| `tests/` | Core, CLI, Restore, simulierte Update-Steuerung |
| `script/` | Debian-Installation und Wartung |
| `.github/workflows/core.yml` | Vorbereitete Linux-CI für Python 3.12/3.13 |

Revision `0001_core_settings` legt nur die leere Core-Einstellungstabelle an.
Die Einstellungsoberfläche verwendet ausschließlich die vier freigegebenen
Schlüssel unter `core.presentation.*`; Secrets bleiben in der geschützten
TOML-Datei. Migrationen laufen nur über `neofab2 migrate`,
niemals über `create_all()` oder HTTP-Routen.

`0002_core_users` ergänzt Benutzer, serverseitige Sitzungen und zeitlich
begrenzte Loginversuchszähler. SQLAlchemy Core verwendet explizite Transaktionen;
`BEGIN IMMEDIATE` serialisiert Erstadmin-Anlage und Letzter-Admin-Prüfung in
SQLite. Fremdschlüssel sind aktiviert. Es werden keine Benutzer migriert oder
automatisch mit einer Migration angelegt.

`0003_user_theme` ergänzt die persönliche Darstellung mit Standard `system`.
`core/settings.py` speichert öffentliche Texte und die Standarddarstellung
transaktional in der bestehenden Einstellungstabelle; jede Speicherung prüft
den Administrator erneut. Keine globalen veraltenden Einstellungscaches:
HTML-Anfragen laden aktuelle Werte. Gemeinsame CSS-Variablen gelten auch für Plugins.

Ab 0.1.5 speichert `core/plugin_state.py` die gewünschte Plugin-Auswahl in
`core_settings` unter `core.plugins.enabled`. Ohne diesen Datensatz gilt weiterhin
`ENABLED_PLUGINS` aus TOML. Nach erster Backend-Speicherung hat die DB Vorrang,
auch bei leerer Auswahl. Beim Start wird nur gelesen, kein Schema erzeugt.
Die Registry ist ein Prozess-Snapshot; die Admin-Seite vergleicht ihn mit dem
gespeicherten Zielzustand. Änderungen wirken beim nächsten Prozessstart.
Manueller Container-Neustart durch den Proxmox-Admin übernimmt alle Prozesse.
Keine Proxmox-API, kein Web-Neustartbefehl und keine automatische Rechteerhöhung.
Abhängigkeitsprüfung und erneute Admin-Prüfung liegen in derselben serialisierten
Speichertransaktion. Der lokale Befehl `plugins-restore-config` ermöglicht die
Wiederherstellung aus einer geprüften TOML-Auswahl, falls die DB-Auswahl ungültig ist.

Passwörter werden über Werkzeug/scrypt gehasht, Formulare durch Flask-WTF
gegen CSRF geschützt. Das signierte Flask-Cookie enthält einen zufälligen
Sitzungstoken, keine Rechte oder Passwörter. Sein SHA-256-Hash verweist auf
die serverseitige Sitzung. Rollen/Kontostatus werden bei jedem Seitenzugriff
aus der Datenbank gelesen. [Zugangsvertrag und Konfiguration](Core_Zugang.md).

`/health/live` prüft den HTTP-Prozess. `/health/ready` prüft Datenbank,
Alembic-Stand und Core-Tabelle. Falscher/fehlender Stand liefert 503;
Antworten enthalten keine internen Pfade oder SQL-Fehler.

## Grenzen und Abweichungen

S01 umfasst Startseite, Profil, Benutzerverwaltung und Plugin-Navigation.
S12 zeigt Core-Version sowie Plugin-Versionen in der Admin-Übersicht.
U01, U08 und die lokale Wiederherstellung X04 sind umgesetzt. U05 umfasst
Anlegen/Bearbeiten/Aktivieren/Deaktivieren, noch kein Löschen. U06 verwendet die
festen Rollen Benutzer/Mitarbeiter/Administrator sowie explizite Plugin-Zugriffsrechte;
Importzuordnung und Rollenpflege folgen. U07 umfasst Anzeigename, Passwortwechsel
und persönliche Darstellung; Sprache folgt. S04 umfasst öffentliche Darstellungseinstellungen,
noch keinen Import/Export oder SMTP. U02–U04, S02/S03, S05–S11, N04 und N05 bleiben offen.
N01 ist mit API 1 teilweise umgesetzt: Abhängigkeiten, Backend-Auswahl mit
Aktivierung beim Neustart, Seiten, Rechte, Navigation und lokale Aufgaben.
Weitere Dienstverträge fehlen.
[Plugin-Vertrag und Betriebsprüfung](plugin-development.md).

Die drei vertrauten Betriebsskriptnamen und interaktive Bedienung bleiben.
Bewusste Abweichung: Benutzer/Pfade für die erste neue Installation fest auf
NeoFab2 begrenzt. Admin-Fragen und Notfall-Passwort-Reset sind jetzt enthalten.
Der Update-Funktionskörper wird vor Git vollständig eingelesen, damit die
laufende Skriptdatei selbst aktualisiert werden kann.

## Nächste Arbeitspakete

0.1.6: `core/i18n.py` stellt Sprachwahl und deutschen Fallback für
Navigation, Login und Profil bereit. `0004_user_locale` speichert die Kontosprache.
`0005_user_details` ergänzt optionale administrative Benutzerangaben. Sie werden
nicht in den allgemeinen Auth-Kontext geladen. Passwortänderungen im Admin-Formular
werden atomar mit den übrigen Feldern gespeichert und widerrufen bestehende Sitzungen.
[Umfang und offene Punkte](Core_Sprachen.md).

1. Sprachübersetzungen und weitere Systemeinstellungen ausbauen.
2. Selbstregistrierung und E-Mail-Verfahren mit dem Versanddienst umsetzen.
3. Plugin-Vertrag um technische Dienste und persistente Aufgaben erweitern.
4. Technische Dienste und Benutzerimport mit abgestimmten Konfliktregeln.
5. Echter Debian-/Proxmox-Installations-, Update- und Wiederherstellungstest;
   vollständige Core-Abnahme vor Fachplugins.

Offen: Registrierungsregeln, Rollen-/Konfliktzuordnung beim Import, produktive
Datenbank und Umstellungstermin. Keine Datenübernahme in v0.1.5.

## Referenzen

- [Flask Application Factory](https://flask.palletsprojects.com/en/stable/tutorial/factory/)
- [Alembic: programmatische Konfiguration](https://alembic.sqlalchemy.org/en/latest/api/config.html)
- [Debian 13: Python 3.13](https://packages.debian.org/trixie/python3.13)
- [Flask-WTF: CSRF](https://flask-wtf.readthedocs.io/en/latest/api/)
- [Werkzeug: Passwort-Hashing](https://werkzeug.palletsprojects.com/en/stable/utils/)
