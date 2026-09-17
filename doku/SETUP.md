# NeoFab2 v0.1.2 – Installation und Entwicklung

## Umfang und Prüfstand

Startfähiger Core mit Startseite, Version, SQLite-Basis und expliziter
Alembic-Migration. Der aktuelle Arbeitsstand ergänzt Anmeldung, Administratoren,
Benutzerverwaltung, Profil und lokalen Passwort-Reset. Selbstregistrierung,
E-Mail-Verfahren, Plugin-Verwaltung und Benutzerübernahme folgen. SQLite dient der ersten isolierten
Testinstallation; die endgültige produktive Datenbankentscheidung bleibt offen.

Lokal geprüft unter Windows/Python 3.12: Core, Migration, Sicherung und
Wiederherstellung, Wheel einschließlich Logo/Templates, Bash-Syntax, ShellCheck
und simulierte Update-Abläufe. Ziel der Skripte: Debian 13, Python 3.13, systemd.
Das Grundsystem läuft laut Nutzerrückmeldung im Container. Ein eigener
Proxmox-LXC-Test des neuen Benutzer-Schritts und die Ausführung der Linux-CI
stehen noch aus.
Auch eine visuelle Browserprüfung war hier mangels verbundenem Browser nicht möglich.

## 1. Container vorbereiten

Einen separaten Debian-13-LXC mit eigener IP-Adresse, DNS und Internetzugang
verwenden. Startwerte für einen kleinen Test: 2 CPU-Kerne, 2 GiB RAM, 8 GiB
Speicher und zusätzlich Platz für Backups; keine gemessene Kapazitätszusage.
Die Skripte laufen im Container, nicht auf dem Proxmox-Host.

In dessen Konsole als **root**:

```bash
cat /etc/os-release
ps -p 1 -o comm=
```

Erwartet: Debian 13 und `systemd`. Python 3.13 wird vom Installer installiert
und geprüft. Betriebssystem-Updates bleiben ein separater Administrationsschritt.

## 2. Basisinstallation

Voraussetzung: v0.1.2 wurde manuell in GitHub Desktop committed und auf den
gewählten Branch gepusht. Codex und Installer übernehmen keinen Commit/Push.

```bash
apt-get update
apt-get install -y git ca-certificates
git clone https://github.com/know-how-schmiede/NeoFab2.git /root/NeoFab2-setup
bash /root/NeoFab2-setup/script/setupNeoFab
```

Die Bootstrap-Kopie bleibt unter `/root/NeoFab2-setup`; die Anwendung wird
separat geklont. Die Anleitung geht von einem lesbaren HTTPS-Repository aus.
Keine Tokens in URLs eintragen. Private Repositories benötigen zuvor
eingerichteten Git-Zugriff für den Dienstbenutzer.

| Frage | Vorgabe |
|---|---|
| Neue Installation beginnen? | `n`; zum Start `j` eingeben |
| Repository | dieses NeoFab2-Repository |
| Git-Branch | `main` mit dem bereits veröffentlichten Code |
| HTTP-Port | `8080`, zulässig 1024–65535 |
| Anmeldung über HTTPS? | `j`; nur im isolierten HTTP-Testnetz `n` wählen |
| Erster Administrator | E-Mail, Anzeigename und verdeckte Passwortwiederholung; kein Standardkonto |
| Temporärer Teststart? | `n`; mit `j` Gunicorn im Terminal, Ende mit Strg+C |

| Feste Ablage | Pfad / Name |
|---|---|
| Benutzer ohne Login-Shell | `neofab2` |
| Checkout / virtuelle Umgebung | `/opt/neofab2`, `/opt/neofab2/.venv` |
| SQLite-Datei | `/var/lib/neofab2/neofab2.sqlite3` |
| Konfiguration (root:neofab2, 0640) | `/etc/neofab2/config.toml` |
| Port | `/etc/neofab2/port` |
| systemd-Dienst | `neofab2.service` |

Der Installer erzeugt einen zufälligen Secret-Key, installiert das Python-Paket
und führt `neofab2 migrate`, `neofab2 check` sowie `neofab2 create-admin` aus.
Das Admin-Passwort muss 15 bis 128 Zeichen enthalten. Keine Beispieldaten,
keine Änderungen am alten NeoFab. Existiert einer der Installationspfade oder
der Benutzer bereits, bricht er ab. Nach einer unvollständigen Erstinstallation
Fehlerursache prüfen und vorzugsweise einen frischen Testcontainer verwenden;
es wird nichts automatisch gelöscht oder überschrieben.

## 3. Service

Der optionale Teststart wechselt vor dem Benutzerwechsel nach `/opt/neofab2`,
damit er auch beim Aufruf des Installers aus einem für `neofab2` unzugänglichen
Verzeichnis funktioniert. Fehler dieses Tests bedeuten keine fehlgeschlagene
Basisinstallation; der Testfehler liefert weiterhin einen von null verschiedenen
Exit-Code. Strg+C (130) gilt als reguläres Testende. Mit `n` lässt sich der Test
überspringen. Eine bereits erfolgreiche Installation nicht erneut installieren,
sondern mit der Service-Einrichtung fortfahren.

Optionalen Teststart vorher mit Strg+C beenden. Als root:

```bash
bash /opt/neofab2/script/setupNeoFabService
systemctl status neofab2.service --no-pager
curl --fail http://127.0.0.1:8080/health/ready
```

Erwartet: `active (running)` und `{"status":"ok"}`. Bei abweichendem Port den
gewählten Wert verwenden. Browser: `http://<Container-IP>:8080`.

Der Dienst bindet an alle Container-Schnittstellen. Für diese Testinstallation
den Zugriff über Netzwerk/Firewall auf das Testnetz begrenzen.
HTTPS-/Reverse-Proxy-Einrichtung ist noch kein Bestandteil des Installers.
Secure-Cookies sind voreingestellt. Für eine Anmeldung über HTTP im isolierten
Testnetz muss `SESSION_COOKIE_SECURE = false` in `/etc/neofab2/config.toml`
stehen (Neuinstallation: HTTPS-Frage mit `n` beantworten). Nach Änderung
`systemctl restart neofab2.service` ausführen. Bei HTTPS `true` beibehalten.

Die Unit läuft als `neofab2` mit zwei Gunicorn-Workern, prüft vor dem Start das
Schema und darf dauerhaft nur im Datenverzeichnis schreiben. Kein zusätzlicher
Worker oder Timer, da Hintergrundaufgaben noch nicht implementiert sind.
Eine passende bestehende Unit wird gestartet, aber nicht überschrieben.

## 4. Update

Als root:

```bash
bash /opt/neofab2/script/upDateNeoFabService
```

Das Skript prüft Schema, Unit, sauberen Checkout und Branch. Es holt `origin`,
prüft Fast-Forward und zeigt alten/neuen Commit. Erst nach Bestätigung stoppt
es den Dienst und sichert Datenbank, Konfiguration, Unit, Quellcode,
Versionsstand und bisherige virtuelle Umgebung. Anschließend: Git-Fast-Forward,
Paketinstallation, Migration, Core-Check, Start und HTTP-Bereitschaftsprüfung.

Gleicher Git-Stand: Ende ohne Neuinstallation. Fehler nach Dienststopp:
Dienst bleibt angehalten, Sicherung bleibt erhalten. Kein Branchwechsel,
keine automatische Rückmigration. Änderungen am Service-Vertrag müssen bei
späteren Releases separat dokumentiert werden. [Wiederherstellung](operations.md).

### Bestehendes Grundsystem um Benutzer erweitern

Den neuen Arbeitsstand zunächst manuell committen und auf den verwendeten
Remote-Branch pushen. Dann das Update-Skript **vor einem manuellen Git-Pull**
ausführen: Es sichert mit dem noch installierten alten Code und migriert nach
der Paketinstallation von `0001_core_settings` auf `0002_core_users`.
Die Anwendungsversionsnummer dieses Arbeitspakets ist `0.1.2`;
der Schemawechsel wird unabhängig davon durch Alembic verwaltet.

Nach erfolgreichem Update, als root:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 create-admin
```

E-Mail, Anzeigename und Passwort eingeben. Anschließend `/login` öffnen.
Im bisherigen HTTP-Testaufbau vorher die oben beschriebene Cookie-Einstellung
anpassen. Existiert bereits ein Administrator, erstellt der Befehl keinen
weiteren; zusätzliche Benutzer und Administratoren werden angemeldet über
die Benutzerverwaltung angelegt. [Details und Notfallzugang](Core_Zugang.md).

## 5. Fehlerhilfe

```bash
journalctl -u neofab2.service -n 80 --no-pager
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
ss -ltnp
```

- **Konfiguration ungültig:** Pfad, Rechte, Secret-Key (mindestens 32 Zeichen)
  und absoluten `DATA_DIR` prüfen; Secret nicht posten.
- **Datenbank nicht bereit / HTTP 503:** Pfad und Rechte prüfen. Nach Sicherung
  `runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 migrate` ausführen.
- **Port belegt:** optionalen Teststart beenden oder Portkonflikt auflösen.
- **Nur lokal erreichbar:** Container-IP, Bridge, Routing und Firewall prüfen.
- **Git-Update abgelehnt:** lokale Änderungen/Commits manuell klären.
- **Downloadfehler:** DNS und Zugang zu Debian, GitHub und PyPI prüfen.
- **Wartung läuft bereits:** anderen Installations-/Update-Prozess beenden lassen.
- **Formularsitzung ungültig / Login bleibt leer:** Seite neu laden; bei HTTP
  die Cookie-Einstellung prüfen. Bei HTTPS Cookies aktivieren und korrekten
  Host verwenden. Nach einer Kontosperre oder Inaktivität neu anmelden.
- **Zu viele Loginversuche:** Standardmäßig 15 Minuten warten. Details zu
  kontobezogener und IP-bezogener Begrenzung unter [Core-Zugang](Core_Zugang.md).

## 6. Lokale Entwicklung

Python 3.12 oder 3.13, als normaler Benutzer im Checkout (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
New-Item -ItemType Directory -Force instance
.\.venv\Scripts\neofab2.exe init-config --output instance/config.toml --data-dir "$((Get-Location).Path)\instance\data" --http-test
$env:NEOFAB2_CONFIG = "$((Get-Location).Path)\instance\config.toml"
.\.venv\Scripts\neofab2.exe migrate
.\.venv\Scripts\neofab2.exe check
.\.venv\Scripts\neofab2.exe create-admin
.\.venv\Scripts\python.exe -m flask --app neofab2:create_app run --port 8080
```

`init-config` nur einmal ausführen; vorhandene Dateien werden nicht
überschrieben. Unter Linux entsprechend `.venv/bin/python`,
`.venv/bin/neofab2` und `export NEOFAB2_CONFIG=/absoluter/pfad/config.toml`.
Flask-Entwicklungsserver nur lokal verwenden.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build
```

Bei blockiertem Windows-Python-Alias den vollständigen Pfad eines vorhandenen
Python-3.12-/3.13-Interpreters verwenden. Bei unzugänglichem Tempverzeichnis
einen neuen Unterpfad unter `.test-artifacts/` mit `pytest --basetemp`
angeben; Elternverzeichnis vorher anlegen. Pytest leert einen vorhandenen
`--basetemp` selbständig: niemals einen Pfad mit benötigten Daten wählen.
