# NeoFab2 v0.1.20 – Installation und Entwicklung

Neu in 0.1.20: einheitliche Buttonleiste für Anlegen, Export und Import sowie bestätigte Löschung deaktivierter Konten. [Bedienung, Schutzregeln und Migration](Core_Benutzerloeschung.md). Neue explizite Schema-Revision: `0013_user_deletion`.

Seit 0.1.15: [Audit-Protokoll und Betriebsstatus](Core_Audit_und_Betriebsstatus.md).
Das normale Update führt die explizite Migration `0011_audit_status` aus.
Anschließend als Administrator unter **Administration** beide neuen Seiten prüfen.
Neue Ereignisse werden ab diesem Update erfasst; kein rückwirkendes Protokoll.
Der Versandworker meldet seinen letzten beobachteten Lauf. Standardmäßig keine
Audit-Löschung; `audit-prune --days 180` zeigt nur eine lokale Vorschau.
Die Detailanleitung beschreibt Rechte, Bereinigung, Fehlerhilfe und Prüfgrenzen.

Seit 0.1.14: SMTP-Eingaben bleiben bei Speicherfehlern erhalten. Die
Service-Einrichtung installiert jetzt `neofab2-mail.timer` und
`neofab2-mail.service`: erster Lauf nach 15 Sekunden, danach 30 Sekunden nach
Ende des vorigen Laufs, höchstens 20 Aufträge pro Lauf. SMTP bleibt standardmäßig aus.

**Beim ersten Update von 0.1.13 oder älter anschließend als root im Container:**

```bash
bash /opt/neofab2/script/setupNeoFabService
systemctl status neofab2-mail.timer --no-pager
journalctl -u neofab2-mail.service -n 40 --no-pager
```

Das alte Update-Skript hat beim Start noch seine bisherigen Funktionen geladen;
der zusätzliche Setup-Aufruf richtet den Timer auch auf dieser Installation ein.
Ergebnis: Timer `active (waiting)`, nach einem Lauf Zähler wie `sent=1` im Journal.
Bleibt ein Testauftrag „Wartend“, SMTP-Aktivierung und Timer prüfen.
Relay ohne Anmeldung: Port **25**, Transport **Unverschlüsselt, ohne Anmeldung**,
Benutzername leer; Host und freigegebene Absenderadresse eintragen und speichern.
Bei „Verbindungsfehler“ Erreichbarkeit/Firewall, bei Ablehnung Relay-Freigaben prüfen.
Details: [SMTP und Versand](Core_SMTP_und_Versand.md).

Neu in 0.1.13: [Registrierung, Aktivierung und Passwort-Reset](Core_Registrierung_und_Reset.md),
explizite Migration `0010_account_flows`. Beide öffentlichen Verfahren starten
ausgeschaltet. Vor Freischaltung als Administrator SMTP testen, `PUBLIC_BASE_URL`
in der geschützten TOML-Datei festlegen und die erlaubten Registrierungsdomains
unter Administration → Systemeinstellungen → Registrierung und Kontowiederherstellung
auswählen. Der vorhandene Versandworker bleibt erforderlich. Bestandskonten werden
nicht automatisch aktiviert. Standardwerte, Ergebnisprüfung und Fehlerhilfe
stehen in der verlinkten Anleitung.

Seit 0.1.12: [SMTP-Einstellungen und persistente Versandaufträge](Core_SMTP_und_Versand.md),
explizite Migration `0009_mail_outbox` nach `0008_core_files`. Versand ist
standardmäßig deaktiviert. Unter Administration → Systemeinstellungen → SMTP
konfigurieren und Testauftrag erzeugen. Als **root**, ausgeführt durch **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 mail-worker --limit 20
```

Dieser Befehl ist ein zusätzlicher einmaliger Lauf. Der Versandtimer übernimmt
den regelmäßigen Betrieb nach der Service-Einrichtung. Ergebniszähler und
Admin-Status prüfen; „Angenommen“ bestätigt nur die SMTP-Übernahme. Vor Updates
zusätzlich gestartete Worker/Aufrufpläne stoppen. Nach Restore zuerst SMTP pausieren
und mögliche bereits erfolgte Zustellungen abgleichen. Passwort, Standardwerte,
Fehlerhilfe und Migrationsbefehle stehen in der verlinkten Detailanleitung.

Seit 0.1.11: [CheckDesign 0.1.0](CheckDesign.md) für Mitarbeiter und
Administratoren. Unter Administration → Plugins aktivieren und danach neu starten.
Keine neue Schema-Revision gegenüber 0.1.10.

Seit 0.1.10: **Administration** bündelt Benutzerverwaltung, Plugins und
Systemeinstellungen. Paket 0 mit Plugin-Rechten und Testdateien benötigt die
explizite Migration `0008_core_files`. [Anleitung](Core_Dateien_und_Rechte.md).

Seit 0.1.9: Stammdaten-Button in den Systemeinstellungen, Icons in allen
Buttons und [UI-Gestaltungsregeln](UI_Gestaltungsregeln.md).
0.1.9 hatte keine neue Schema-Revision gegenüber 0.1.8.

Seit 0.1.8: Abschlussübersichten der Betriebsskripte sowie
[verwaltete Benutzer-Auswahllisten und englische Feldhilfen](Core_Auswahllisten.md).
Die Listen starten leer; alte Freitexte werden nicht übernommen.

## Umfang und Prüfstand

Startfähiger Core mit Startseite, Version, SQLite-Basis und expliziter
Alembic-Migration. Der aktuelle Arbeitsstand ergänzt Anmeldung, Administratoren,
Benutzerverwaltung, Profil, lokalen Passwort-Reset sowie abschaltbare
Selbstregistrierung, E-Mail-Aktivierung und Passwort-Rücksetzung. Audit,
weitere Plugin-Dienste und Benutzerübernahme folgen. SQLite dient der ersten isolierten
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

Voraussetzung: v0.1.20 wurde manuell in GitHub Desktop committed und auf den
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
Das Admin-Passwort muss 8 bis 128 Zeichen enthalten. Keine Beispieldaten,
keine Änderungen am alten NeoFab. Existiert einer der Installationspfade oder
der Benutzer bereits, bricht er ab. Nach einer unvollständigen Erstinstallation
Fehlerursache prüfen und vorzugsweise einen frischen Testcontainer verwenden;
es wird nichts automatisch gelöscht oder überschrieben.

### Erstadmin bei einer Neuinstallation

Nach Migration und Datenbankprüfung ruft `setupNeoFab` automatisch
`neofab2 create-admin` auf. Nacheinander E-Mail-Adresse (später der Anmeldename),
Anzeigename und Passwort mit 8–128 Zeichen eingeben. Das Passwort wird zweimal
verdeckt abgefragt; dass beim Tippen keine Zeichen erscheinen, ist beabsichtigt.

Erwartet: `Erster Administrator angelegt.` Es gibt kein voreingestelltes Konto.
Danach den optionalen Teststart ausführen oder überspringen und den Service
installieren. Für einen reinen HTTP-Testzugang die HTTPS-Frage vorher mit `n`
beantworten. Anschließend unter `/login` mit der gewählten E-Mail und dem
Passwort anmelden; erwartet werden Profil und Benutzerverwaltung.

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
Die Anwendungsversionsnummer des aktuellen Stands ist `0.1.20`;
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

### Neu in 0.1.5: Plugin-Verwaltung im Backend

Als Administrator **Plugins** öffnen und die gewünschte Aktivierung oder
Deaktivierung vormerken. Die Übersicht zeigt gespeicherte Auswahl und laufenden
Zustand getrennt. Änderungen übernimmt ein manueller Container-Neustart durch
den **Proxmox-Admin**; das Backend führt keinen Neustart aus.
Zuerst `core_test`, dann das neue abhängige `management_test` aktivieren.
Zur Deaktivierung umgekehrt vorgehen. Keine zusätzliche Schema-Revision.
[Prüfablauf, Konfigurationsvorrang und Wiederherstellung](plugin-development.md).

### Seit 0.1.4: Systemeinstellungen und Darstellung

Das Update führt `0003_user_theme` aus und ergänzt die Admin-Seite
`/admin/settings`. Im Profil kann jeder Benutzer Hell, Dunkel oder Systemvorgabe
wählen. Vorhandene Konten folgen zunächst der Systemvorgabe (Dunkel).
[Bedienung, Standardwerte und Updateprüfung](Core_Einstellungen.md).

### Seit 0.1.3: Plugin-Grundsystem

Das Plugin-Grundsystem ergänzt die Admin-Seite `/admin/plugins`. Bei einer neuen
Installation sind beide Testplugins deaktiviert. Bestehende Auswahl bleibt erhalten.
[Testplugins aktivieren und prüfen](plugin-development.md).
Das Plugin-Grundsystem selbst benötigt keine neue Tabelle. Bestehende Benutzer
und HTTP-Cookie-Konfiguration bleiben erhalten. Anmeldung und Passwortwechsel im HTTP-Container wurden nach
Korrektur von `SESSION_COOKIE_SECURE` durch den Nutzer bestätigt.

### Anmeldung: „Formularsitzung abgelaufen oder ungültig“

Diese Meldung entsteht vor der Passwortprüfung und betrifft nicht die
Passwortlänge. Im bestehenden HTTP-Testcontainer kann das voreingestellte
Secure-Cookie die Ursache sein: Der Browser sendet es nur über HTTPS zurück.

Als **root im isolierten HTTP-Testcontainer** prüfen:

```bash
grep '^SESSION_COOKIE_SECURE' /etc/neofab2/config.toml
```

Erforderlich für HTTP: `SESSION_COOKIE_SECURE = false`. Den vom Installer
angelegten `true`-Eintrag gezielt ändern und den Dienst neu starten:

```bash
sed -i 's/^[[:space:]]*SESSION_COOKIE_SECURE[[:space:]]*=[[:space:]]*true[[:space:]]*$/SESSION_COOKIE_SECURE = false/' /etc/neofab2/config.toml
grep '^SESSION_COOKIE_SECURE' /etc/neofab2/config.toml
systemctl restart neofab2.service
```

Erwartet: `SESSION_COOKIE_SECURE = false`. Bei HTTPS `true` beibehalten.
Danach `http://<Container-IP>:8080/login` frisch öffnen, nicht das alte Formular
erneut senden. Cookies für die Website zulassen und Host/IP-Adresse zwischen
Aufruf und Absenden nicht wechseln. Bei anhaltendem Fehler Cookies dieser
Website löschen und `/login` erneut öffnen. Der CSRF-Schutz bleibt eingeschaltet.
Die überarbeitete Meldung weist eine fehlende Formularsitzung gesondert aus.

**Fehler bleibt trotz `false` bestehen:** Entscheidend ist auch das Cookie,
das der laufende Dienst tatsächlich ausliefert. Als **root im Container**
die Antwort auf eine frische Loginseite prüfen (Standardport 8080 anpassen):

```bash
curl --max-time 10 -sS -D - -o /dev/null http://127.0.0.1:8080/login | sed -E 's/^(Set-Cookie: [^=]+=)[^;]*/\1<ausgeblendet>/I'
```

Erwartet: HTTP 200 und `Set-Cookie: neofab2_session=<ausgeblendet>; ...`.
Für HTTP darf diese Zeile kein `Secure` enthalten. Der Cookie-Wert wird für
die Weitergabe ausgeblendet. Erscheint dennoch `Secure`, verwendet der
angesprochene Prozess noch eine andere Einstellung: Dienstneustart, gewählten
Port und den `NEOFAB2_CONFIG`-Pfad in der systemd-Unit lokal prüfen.
Keine vollständige Konfiguration oder Sitzungscookies weitergeben.

Fehlt `Secure` und der Browser meldet weiterhin eine fehlende Sitzung,
denselben Zugang in einem privaten Browserfenster öffnen. Funktioniert das,
Website-Cookies im ursprünglichen Fenster entfernen. Andernfalls in den
Browser-Netzwerkwerkzeugen prüfen, ob beim POST auf `/login` das Cookie
`neofab2_session` gesendet wird (nur ja/nein weitergeben). Wird es gesendet,
sind unter anderem abweichende Signaturschlüssel zwischen Prozessen oder
mehrere gleichnamige Cookies zu untersuchen. Den `SECRET_KEY` nicht auf
Verdacht ändern. Richtige und falsche Zugangsdaten führen bei diesem
Sitzungsfehler gleichermaßen zu HTTP 400, weil ihre Prüfung noch nicht beginnt.

### Admin-Passwort nachträglich ändern oder wiederherstellen

Der lokale Admin-Zugang funktioniert laut Nutzerrückmeldung. Für ein neues,
auch kürzeres Passwort nach dem Code-Update als **root im Container**:

```bash
bash /opt/neofab2/script/resetAdminPassword
```

Admin-ID aus der Liste wählen, Änderung bestätigen und das neue Passwort mit
8–128 Zeichen zweimal verdeckt eingeben. Danach `/login` neu öffnen und mit
E-Mail und neuem Passwort anmelden. Bestehende Sitzungen werden beendet;
für den Passwortwechsel ist kein Dienstneustart nötig. Deaktivierte Konten
nur ausdrücklich mit `--reactivate` reaktivieren. Bereits angelegte Konten
nicht durch erneutes `create-admin` ersetzen. Längere bestehende Passwörter
bleiben gültig.

### Weitere Prüfungen

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

## Abschlussübersicht der Skripte (0.1.8)

`setupNeoFab`, `setupNeoFabService`, `upDateNeoFabService` und
`resetAdminPassword` geben beim Beenden einen deutlich eingerahmten Block
**NEOFAB2 – ZUSAMMENFASSUNG** aus. Er nennt Ergebnis/Exit-Code, Installations-,
Daten- und Konfigurationspfad, Dienstkonto und Servicezustand, ermittelte IPv4-/
IPv6-Adressen mit Port, installierte Version, Admin-E-Mails mit Aktivstatus,
gegebenenfalls den Sicherungspfad und kopierbare Wartungs-/Diagnosebefehle.

Die internen HTTP-Adressen sind keine Zusage externer Erreichbarkeit. Bei
Secure-Cookies nennt die CLI ausdrücklich die HTTPS-Anforderung; die öffentliche
HTTPS-Adresse stammt aus der eigenen Reverse-Proxy-Konfiguration. Die Skripte
richten kein TLS ein. Fehlende IP-/Kontodaten werden als nicht verfügbar angezeigt.
Passwörter, Hashes, Sitzungstokens und Konfigurationsgeheimnisse werden nicht ausgegeben.

Abbruch oder Fehler bleiben als solche erkennbar; die Zusammenfassung erhält
den ursprünglichen Exit-Code. Ein fehlgeschlagener optionaler Teststart meldet
zusätzlich, dass die Basisinstallation bereits abgeschlossen ist. Unvollständige
Sicherungen sind ausdrücklich markiert. Ein bereits aktueller Git-Stand wird als
„Keine Aktualisierung nötig“ ausgegeben, nicht als neu ausgeführtes Update.

Dieselben lokalen Konto-/Versionshinweise lassen sich als **root im Container**
ohne Änderungen an Daten oder Plugins erneut abrufen:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 maintenance-info
```

Erwartet: Version 0.1.20, HTTP-/HTTPS-Hinweis und vorhandene Admin-E-Mails. Falls
Angaben fehlen: Konfigurationspfad, Installation und Datenbankschema mit `check`
prüfen; keine Secrets zur Fehlersuche veröffentlichen. Betriebsbefehle in der
Übersicht sind für **root im NeoFab2-Container**, nicht für den Proxmox-Host.
## Abschlussausgaben und Stammdaten: Nachbesserung 0.1.8

Die Betriebsskripte zeigen ermittelte Container-Adressen statt IP-Platzhaltern.
Trennlinien setzen Datenbankprüfung und Bereitschaftsmeldung ab; die abschließende
Zusammenfassung enthält Ergebnis, Zugänge und Wartungsbefehle. Ausführung und
Fehlerhilfe: [Schnellstart](../script/README.md#nachbesserung-der-abschlussausgaben-in-018).
Ein bereits laufendes Update aus 0.1.7 verwendet noch den zuvor geladenen Skriptcode.

Als angemeldeter Administrator **System settings → Master data** öffnen
(Deutsch: **Systemeinstellungen → Stammdaten**). Dort wird für jede Serie auf
eine getrennte Liste mit eigenen Eingabe-/Änderungsformularen verlinkt.
Bedienung und Ergebnisprüfung: [Auswahllisten](Core_Auswahllisten.md).
Keine zusätzliche Schemaänderung oder Freitextmigration für diese Nachbesserung.
