# Core-Zugang – aktueller Arbeitsstand v0.1.2

Die zentrale Version dieses Arbeitspakets ist `0.1.2`.
Dieses Arbeitspaket erweitert U01, U05–U08 und X04. Es ist keine vollständige
Core-Abnahme; insbesondere E-Mail-Verfahren und Plugin-Vertrag fehlen noch.

## Was bereits funktioniert

- Anmeldung mit E-Mail und Passwort, Abmeldung ausschließlich per POST.
- Benutzerverwaltung für Administratoren: anlegen, Anzeigename/E-Mail/Rolle
  bearbeiten, aktivieren und deaktivieren. Keine Benutzerlöschung in diesem Schritt.
- Eigenes Profil: Anzeigename ändern; Passwortwechsel nur mit aktuellem Passwort.
- Lokaler Erstadministrator und Notfall-Passwort-Reset ohne Webanmeldung.
- Schutz des letzten aktiven Administrators, auch bei parallelen Änderungen.

E-Mail-Adressen werden validiert, normalisiert und vollständig ohne Beachtung
der Groß-/Kleinschreibung verglichen. Es findet keine Zustellprüfung oder
E-Mail-Verifikation statt. Registrierung, E-Mail-Aktivierung und Self-Service-Reset
werden erst mit dem Versanddienst umgesetzt. Es gibt keine versteckten
Standardkonten, Startpasswörter oder automatisch übernommenen Benutzer.

## Rollen und Rechte

| Rolle | Core-Rechte |
|---|---|
| Benutzer (`user`) | eigenes Profil und eigenes Passwort |
| Mitarbeiter (`staff`) | derzeit dieselben Core-Rechte wie Benutzer; Fachrechte folgen |
| Administrator (`admin`) | eigenes Profil und `core.users.manage` |

Rechte werden serverseitig geprüft, nicht nur in der Navigation.
Profilanfragen dürfen weder andere Konten bearbeiten noch Rolle/E-Mail ändern.
Admin-Schreiboperationen prüfen den aktiven Administrator in ihrer Transaktion
erneut. Plugins erhalten später explizite Rechte; derzeit kein pauschales
Administrator-Wildcard-Recht für zukünftige Plugins.

Der letzte aktive Administrator kann nicht deaktiviert oder herabgestuft werden.
Ein Administrator darf sein eigenes Konto ändern, sofern diese Regel erhalten
bleibt. E-Mail-, Rollen- und Statusänderungen beenden alle Sitzungen des Kontos.

## Erstadministrator und Update

Neue Installationen fragen nach der Migration automatisch nach E-Mail,
Anzeigename und Passwort. Bei einem bestehenden Grundsystem zuerst das Update
gemäß [SETUP](SETUP.md) ausführen. Es führt `0002_core_users` explizit aus;
die bisherige Einstellungstabelle bleibt erhalten.

Danach als **root im Container**:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 create-admin
```

Erwartet: verdeckte Passwortabfrage mit Wiederholung und Meldung
`Erster Administrator angelegt.` Ein bereits vorhandenes Admin-Konto verhindert
eine erneute Erstadmin-Anlage, auch wenn es deaktiviert ist. Zusätzliche Konten
werden über `/admin/users` angelegt. Startpasswörter persönlich über einen
sicheren Weg übergeben; Benutzer können sie im Profil ändern.

Passwörter: 15–128 Zeichen, keine stillschweigende Kürzung und keine erzwungene
Zeichenmischung. Speicherung nur als Werkzeug-scrypt-Hash. Es gibt kein
CLI-Passwortargument; Passwörter erscheinen weder in Shell-History noch in
Erfolgsmeldungen. Secrets/Hashwerte werden nicht in HTML ausgegeben.

## Anmeldung im bestehenden HTTP-Testcontainer

Unter `/etc/neofab2/config.toml` steht standardmäßig:

```toml
SESSION_COOKIE_SECURE = true
```

Für eine Anmeldung benötigt der Browser dann HTTPS. Gunicorn stellt selbst
kein HTTPS bereit; der HTTPS-Zugang ist separat einzurichten.
Nur für das isolierte HTTP-Testnetz den bestehenden Eintrag auf `false` ändern
(nicht einen zweiten gleichnamigen Eintrag anhängen), anschließend als root:

```bash
systemctl restart neofab2.service
```

Bei Neuinstallation entspricht dies der Antwort `n` auf die HTTPS-Frage;
bei lokaler Entwicklung der Option `init-config --http-test`. Außerhalb des
isolierten Tests HTTPS und `true` verwenden. Die Cookies heißen
`neofab2_session`, sind HttpOnly und SameSite=Lax.

## Sitzungen und Anmeldebegrenzung

| TOML-Einstellung | Standard | Wirkung |
|---|---|---|
| `SESSION_IDLE_SECONDS` | 1800 | Ablauf nach 30 Minuten ohne Seitenzugriff |
| `SESSION_MAX_SECONDS` | 43200 | Spätestens nach 12 Stunden neu anmelden |
| `LOGIN_WINDOW_SECONDS` | 900 | Zeitfenster von 15 Minuten |
| `LOGIN_ACCOUNT_LIMIT` | 5 | Fehlversuche pro normalisierter E-Mail |
| `LOGIN_IP_LIMIT` | 30 | Fehlversuche pro Quell-IP, auch für unbekannte Konten |

Einstellungen sind optionale positive Ganzzahlen. Änderungen benötigen einen
Dienstneustart. Erfolgreiche Anmeldung setzt den Kontozähler zurück, nicht den
IP-Zähler. Nach Ausschöpfen einer Grenze endet die Sperre mit dem Zeitfenster.
Die Zähler liegen in der Datenbank und gelten über Worker/Neustarts hinweg.
IP-Adressen und Eingabe-E-Mails werden im Versuchszähler nur als HMAC gespeichert.

Es wird `request.remote_addr` verwendet; ungeprüfte `X-Forwarded-For`-Header
werden nicht vertraut. Hinter einem Reverse Proxy teilen sich Nutzer daher
zunächst dessen IP-Limit. Eine Konfiguration vertrauenswürdiger Proxies gehört
zu einem späteren Betriebsauftrag, kein pauschales Vertrauen in Client-Header.

Sitzungstoken sind zufällig und serverseitig widerrufbar. Abmeldung löscht die
Sitzung, Passwortwechsel/Reset löschen alle Sitzungen des Kontos. Deaktivierte
Konten verlieren beim nächsten Zugriff den Zugang. Health- und statische
Anfragen verlängern die Inaktivitätsfrist nicht. Neue Logins räumen abgelaufene
Sitzungen und alte Versuchszähler auf. Keine Hintergrundaufgaben erforderlich.

Alle schreibenden Formulare einschließlich Login/Logout haben CSRF-Schutz.
Bei abgelaufener Formularsitzung Seite neu laden und gegebenenfalls neu anmelden.
HTML-Antworten werden mit `Cache-Control: no-store` ausgeliefert.

## Notfall-Passwort-Reset

Als **root im Container**:

```bash
bash /opt/neofab2/script/resetAdminPassword
```

Vorhandene Administratoren werden mit ID und Status angezeigt. ID wählen,
bestätigen und neues Passwort zweimal verdeckt eingeben. Erwartet:
`Admin-Passwort geändert; bisherige Sitzungen beendet.`

Deaktivierte Administratoren bleiben ohne ausdrückliche Reaktivierung gesperrt:

```bash
bash /opt/neofab2/script/resetAdminPassword --reactivate
```

Alternativ direkt im Installationsverzeichnis als Dienstbenutzer:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 reset-admin-password
```

Der Reset entfernt den kontobezogenen Loginzähler. Eine bestehende IP-Sperre
läuft normal ab. Kein Dienstneustart erforderlich. Allgemeine E-Mail-Resets
für Benutzer und Mitarbeiter gehören noch zum offenen Self-Service-Arbeitspaket.

## Nachweise und Grenzen

47 Tests unter Windows/Python 3.12 bestanden. Bash-Syntax und ShellCheck für
alle fünf Shell-Dateien bestanden; Wheel und sdist gebaut. Das installierte
Wheel wurde einschließlich Migration, Login, Profil und Benutzerübersicht geprüft.

Automatisierte Tests verwenden ausschließlich synthetische Konten. Geprüft
werden gültige/ungültige/deaktivierte Logins, CSRF, Rechte bei Direktzugriff,
unerlaubte Profiländerungen, Hashing, Cookie-Replay nach Logout,
Sitzungsablauf, Passwortwechsel, Erstadmin-/Letzter-Admin-Parallelität,
Anmeldebegrenzung sowie CLI-Reset und Migration vom vorherigen Schema.

Die Benutzerverwaltung ergänzt die bereits vom Nutzer als laufend gemeldete
Grundinstallation. Ein eigener LXC-Echttest dieses neuen Schritts und visuelle
Browserprüfung stehen noch aus. Benutzerlöschung, eigene Rollenverwaltung,
Sprachen/Design, SMTP, Registrierung, E-Mail-Aktivierung, Self-Service-Reset,
Plugin-Vertrag und Benutzerimport bleiben ausdrücklich offen.
