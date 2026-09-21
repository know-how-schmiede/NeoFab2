# Architektur – Stand v0.1.13

**Planungsnachtrag ohne Codeänderung:** [Plugin-Pakete und Lifecycle](Plugin_Pakete_und_Lifecycle.md)
beschreibt ein vollständiges Verzeichnis je Plugin mit eigenen Ressourcen,
einen separaten Installationsstamm, Admin-Mindestlevel und spätere ZIP-/
Deinstallationsabläufe. Code/Ressourcen bleiben von veränderlichen Laufzeitdaten
getrennt. Der bestehende Katalog und die zentrale Migrationskette werden erst
in gesonderten Paketen angepasst; die Planung ist noch nicht implementiert.

Seit 0.1.11 ergänzt das ausdrücklich beauftragte technische Testplugin
`plugins/checkdesign.py` eine Designgalerie für `staff` und `admin`.
Es verwendet Core-CSS und das gemeinsame Icon-Makro, eigenes CSS nur für die
Galerieanordnung. Die Theme-Vorschau überschreibt allein den Renderkontext der
Plugin-Seite; keine Profil-/Systemänderung, kein JavaScript und keine Migration.
[Bedienung](CheckDesign.md).

Ab 0.1.7 sind die App und CLI standardmäßig englisch. Deutsche Bezeichnungen
in dieser Anleitung gelten bei gewählter deutscher Kontosprache.
[Sprachwahl und Migration 0006](Core_Sprachen.md).

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
| `src/neofab2/plugins/` | Drei technische Testplugins, bei neuer Installation deaktiviert; künftig vollständiger Unterordner je Plugin |
| `src/neofab2/services/` | Technischer kleiner Dateidienst; weitere Dienste geplant |
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
noch keinen Import/Export. SMTP und minimale Outbox sind seit 0.1.12 vorhanden;
U02–U04/S06 sind seit 0.1.13 mit abschaltbaren Kontoverfahren umgesetzt;
weitere Teilumfänge von S02–S11 und N04 bleiben offen.
N01 ist mit API 1 teilweise umgesetzt: Abhängigkeiten, Backend-Auswahl mit
Aktivierung beim Neustart, Seiten, Rechte, Navigation und lokale Aufgaben.
Seit 0.1.10: zusätzliche `Permission`-Deklarationen, Besitzerprüfung und minimale
Dateischnittstelle über `plugin_api/files.py`. `services/files.py` speichert kleine
Anhänge samt Metadaten atomar in `core_files` (explizite Revision `0008_core_files`).
Core-Verwaltungsziele liegen unter dem neuen Einstieg `/admin`. Weitere
Dienstverträge fehlen; [Umfang und Grenzen](Core_Dateien_und_Rechte.md).
[Plugin-Vertrag und Betriebsprüfung](plugin-development.md).

Die drei vertrauten Betriebsskriptnamen und interaktive Bedienung bleiben.
Bewusste Abweichung: Benutzer/Pfade für die erste neue Installation fest auf
NeoFab2 begrenzt. Admin-Fragen und Notfall-Passwort-Reset sind jetzt enthalten.
Der Update-Funktionskörper wird vor Git vollständig eingelesen, damit die
laufende Skriptdatei selbst aktualisiert werden kann.

## Nächste Arbeitspakete

0.1.7: `core/i18n.py` verwendet englische Ausgangsschlüssel und englischen Fallback
für Core-Oberfläche, Administration und Testplugins. Deutsch ist eine Übersetzungssprache. `0004_user_locale` speichert die Kontosprache.
`0005_user_details` ergänzt optionale administrative Benutzerangaben. Sie werden
nicht in den allgemeinen Auth-Kontext geladen. Passwortänderungen im Admin-Formular
werden atomar mit den übrigen Feldern gespeichert und widerrufen bestehende Sitzungen.
[Umfang und offene Punkte](Core_Sprachen.md).

Priorisierter Plan mit Funktions-IDs und Prüfkriterien: [Nächste Core-Schritte](Core_Naechste_Schritte.md).
Nach der Planungspräzisierung zunächst Plugin-Rechte und minimale Datei-Verträge
mit Testplugins vervollständigen (Paket 0, 0.1.10); der Versanddienst folgt in
Paket 1 (0.1.12), die Kontoverfahren in Paket 2 (0.1.13). Als nächstes folgen
Audit-Logs und Betriebsstatus in Paket 3.
Nach vollständiger Core-Abnahme `orders` minimal und `printing3d` als Referenzplugin.
Gemeinsame Upload-/STL-Viewer-Komponenten bleiben technische Infrastruktur;
PrintFleet folgt nach dem lokalen MVP. [Verbindliche Abgrenzung](Plugin_Umsetzungsplan.md).

Offen: betriebliche Freigabe der Registrierungsdomains, Rollen-/Konfliktzuordnung beim Import, produktive
Datenbank und Umstellungstermin. Keine Datenübernahme in v0.1.7.

## Referenzen

- [Flask Application Factory](https://flask.palletsprojects.com/en/stable/tutorial/factory/)
- [Alembic: programmatische Konfiguration](https://alembic.sqlalchemy.org/en/latest/api/config.html)
- [Debian 13: Python 3.13](https://packages.debian.org/trixie/python3.13)
- [Flask-WTF: CSRF](https://flask-wtf.readthedocs.io/en/latest/api/)
- [Werkzeug: Passwort-Hashing](https://werkzeug.palletsprojects.com/en/stable/utils/)

## Benutzer-Auswahllisten 0.1.8

`core/user_options.py` kapselt die drei getrennt gepflegten Listen in
`core_user_options`. `0007_user_options` legt diese Tabelle leer an; keine
Übernahme bisheriger Freitexte. Benutzerzuordnungen bleiben in den bestehenden
Textspalten, werden bei Kontospeicherung aber innerhalb derselben Transaktion
gegen den Katalog geprüft. Umbenennen aktualisiert die Zuordnungen atomar.
Die Kostenstellenliste ist Benutzer-Metadatenpflege, keine O13-Finanzfunktion.
[Details und Grenzen](Core_Auswahllisten.md).

## SMTP und Outbox 0.1.12

`core/mail.py` administriert SMTP unter `/admin/settings/mail`; `services/mail.py`
kapselt Einstellungen, transaktionale Outbox und Transport. `plugin_api/notifications.py`
stellt den additiven API-1-Vertrag mit explizitem `mail_permission` bereit.
`0009_mail_outbox` ergänzt die persistente Tabelle. Der einmalige CLI-Befehl
`mail-worker` reserviert Aufträge atomar, führt SMTP außerhalb der DB-Transaktion
aus und begrenzt Wiederholungen. Verwaiste Übernahmen und mehrdeutige SMTP-Abbrüche
werden ungeklärt statt automatisch erneut versendet. Secrets bleiben in TOML;
Plugin-Deaktivierung pausiert neue Übernahmen. Seit 0.1.14 ruft ein eigener
systemd-Timer den Worker regelmäßig auf (Service-Einrichtung erforderlich). Keine Anhänge,
keine Kontoverfahren in Paket 1 und keine automatische Löschung.
[Betrieb, Zustände, Schnittstelle und Grenzen](Core_SMTP_und_Versand.md).

## Kontoverfahren 0.1.13

`core/account_flows.py` kapselt Registrierung, Aktivierung, Passwort-Reset,
Freigaberegeln, Codegültigkeit und Kontonachrichten. `0010_account_flows`
ergänzt `activation_pending`, Token- und Begrenzungstabellen sowie optionale
Zuordnungsfelder der Outbox. Kontoänderung und Versandauftrag werden atomar
gespeichert. `core/users.py` widerruft bei sicherheitsrelevanten Änderungen
offene Codes; Authentifizierung und Sitzungen sperren wartende Konten.

Der Core registriert bei der Application Factory einen Mail-Vorbereitungshook.
Der generische Worker ruft ihn ausschließlich für zugeordnete Kontonachrichten
auf; der Hook prüft Ablauf, aktuelle Freigaben und Kontostatus. Vollständige
Codes werden erst im Arbeitsspeicher des Workers erzeugt, nicht in der Outbox
gespeichert. Einlösung ausschließlich per CSRF-geschütztem POST, keine Tokens
in vorgesehenen URLs. Domains mit internationalisierten Namen werden für SMTP
in die ASCII-Darstellung normalisiert; SMTPUTF8-Lokalteile bleiben ausgeschlossen.
[Bedienung, Schutzmaßnahmen und offene Prüfungen](Core_Registrierung_und_Reset.md).

## Audit und Betriebsbeobachtung ab 0.1.15

`services/audit.py` speichert ausschließlich feste Ereigniscodes, Modulkennung,
Zeit, numerische Konto-/Objektreferenzen und ggf. Anzahl. Änderungen und Audit
teilen die Transaktion; kein automatisches Schema und keine Geheimnisdetails.
`core/operations.py` stellt Admin-Ansichten bereit. `plugin_api/audit.py` ergänzt
API 1 um Audit für deklarierte, aktuell erlaubte Plugin-Aktionen.
`services/operations.py` speichert den letzten beobachteten Worker-Lauf; das
ist weder systemd-Status noch externer Zustellnachweis. Explizite Migration 0011,
keine automatische Aufbewahrungsbereinigung. [Details](Core_Audit_und_Betriebsstatus.md).
