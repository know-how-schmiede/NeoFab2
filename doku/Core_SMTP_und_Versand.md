# SMTP und persistente Versandaufträge – Stand 0.1.15, eingeführt in 0.1.12

Seit 0.1.16 zeigen Oberflächenzeiten die eingestellte IANA-Zeitzone samt UTC-Abstand; Speicherung bleibt UTC. [Zeitzone einstellen](Core_Oberflaeche_und_Einstellungen.md).

Paket 1 des [Core-Arbeitsplans](Core_Naechste_Schritte.md): S05, N05 und
Teilumfänge von S06/N01; Migration X07, Betriebsanleitung X05. Keine Fachplugins.
Seit 0.1.13 ergänzt Paket 2 [Registrierung, Aktivierung, Willkommens- und
Passwort-Reset-E-Mails](Core_Registrierung_und_Reset.md). Seit 0.1.14 ergänzt die Service-Einrichtung einen regelmäßigen Versandtimer;
der einmalige CLI-Aufruf bleibt verfügbar.

## Administration und Standardwerte

Als Administrator: **Administration → Systemeinstellungen → SMTP & Versandaufträge**.
Der Zugriff einschließlich Speichern, Testauftrag und Wiederholung erfordert
`core.settings.manage`, ein aktives Konto und bei Änderungen CSRF-Schutz.
Buttons nutzen die gemeinsamen Icons; Englisch und Deutsch sind vorhanden,
Französisch verwendet den englischen Fallback.

| Einstellung | Standard / Bedeutung |
|---|---|
| Versand aktivieren | Aus; vorhandene Aufträge bleiben erhalten |
| Host / Absender | Leer; beide beim Aktivieren erforderlich |
| Port | 587, zulässiger Bereich 1–65535 |
| Transport | STARTTLS mit Zertifikatsprüfung; alternativ direktes TLS oder unverschlüsseltes lokales Relay |
| Benutzername | Leer; Anmeldung nur mit TLS |
| Passwort | `SMTP_PASSWORD` in der geschützten TOML-Datei; Standard leer |
| Worker-Limit | 20 Aufträge pro Aufruf, auswählbar 1–100 |
| Netzwerk-Timeout | 10 Sekunden je Socketoperation |
| Automatische Versuche | Höchstens 5 je Versandzyklus, Wartezeiten 60/120/240/480 Sekunden |

Host, Absender, Port, Transport, Benutzername und Aktivierung liegen in
`core_settings` unter `core.smtp`. Das Passwort wird weder in dieser Tabelle
noch im HTML oder in Worker-Ausgaben gespeichert. Die Seite zeigt nur, ob es
konfiguriert ist. Rohe SMTP-Antworten werden nicht protokolliert oder angezeigt;
Fehler erscheinen als feste Kategorien. Kein SMTP-Debuglogging aktivieren.

Das SMTP-Passwort als **root** mit einem Editor in `/etc/neofab2/config.toml`
ergänzen; vorhandene Werte, insbesondere `SECRET_KEY`, beibehalten:

```toml
SMTP_PASSWORD = "hier-das-SMTP-Passwort-eintragen"
```

Die Datei bleibt ausschließlich für root und den Dienstbenutzer lesbar,
entsprechend der vorhandenen Installation (`root:neofab2`, Modus `640` oder
restriktiver mit passendem Eigentümer). Passwort nicht als CLI-Argument oder
in der Shell-Historie eingeben. Danach als **root**:

```bash
systemctl restart neofab2.service
```

Auch bereits laufende Worker müssen beendet und mit der neuen Konfiguration
gestartet werden. Ein neuer einmaliger CLI-Aufruf liest sie automatisch neu.
TLS prüft Zertifikat und Hostnamen; es gibt keinen Schalter zum Abschalten
dieser Prüfung. Unverschlüsselter Transport ist nur für ein vertrauenswürdiges
lokales Relay vorgesehen und erlaubt keine SMTP-Anmeldung.

## Regelmäßiger Versand ab 0.1.14

Als **root im NeoFab2-Container** nach dem ersten Update von 0.1.13 oder älter:

```bash
bash /opt/neofab2/script/setupNeoFabService
systemctl status neofab2-mail.timer --no-pager
journalctl -u neofab2-mail.service -n 40 --no-pager
```

Setup erhält den vorhandenen Webdienst und richtet eigene NeoFab2-Versandunits ein.
Bestehende Versandunits werden beibehalten, Dienstpfad/Benutzer geprüft.
Der Timer startet nach 15 Sekunden, dann jeweils 30 Sekunden nach Laufende.
Ein Lauf verarbeitet höchstens 20 fällige Aufträge unter dem Benutzer `neofab2`
mit `/etc/neofab2/config.toml`. Dieselbe systemd-Unit läuft nicht parallel zu sich
selbst. Nach 240 Sekunden beendet systemd einen überlangen Lauf; angefangene
ungeklärte Zustellungen behandelt die bestehende Übernahmefrist von 300 Sekunden.

Ergebnis: Timer `active (waiting)`; der kurzlebige Versanddienst darf zwischen
Läufen `inactive (dead)` sein. Zähler stehen im Journal, Auftragsstatus im Web.
Bei fehlendem Timer Setup ausführen; bei Dienstfehlern Journal und `neofab2 check`
prüfen. Ein laufender Timer kann bereits gespeicherte Aufträge versenden, sofern
SMTP aktiviert ist. Nach Restore deshalb zunächst Timer und Worker stoppen.
Spätere Updates mit dem neuen Skript stoppen beide vor Sicherung/Migration und
starten den Timer erst nach erfolgreicher Web-Bereitschaft wieder.
Beim ersten Update ist der zusätzliche Setup-Aufruf erforderlich, weil das alte
Update-Skript seine bisherigen Funktionen schon vor dem Git-Update geladen hat.

### Relay auf Port 25 ohne Anmeldung

Als Administrator Host und freigegebene Absenderadresse setzen, Port **25**,
Transport **Unverschlüsselt, ohne Anmeldung**, Benutzername leer lassen.
`SMTP_PASSWORD` ist dafür nicht erforderlich. **Versand aktivieren** anhaken und
**SMTP-Einstellungen speichern** wählen. Nach erneutem Laden müssen Port 25,
Transport und Aktivierung erhalten bleiben. Bei Validierungsfehlern bleibt der
Formularinhalt zur Korrektur sichtbar; der gespeicherte Zustand ändert sich nicht.
Ein automatisches Zurücksetzen des Ports beim Aktivieren ist nicht vorgesehen.

## Testauftrag und einmaliger Worker

SMTP konfigurieren und speichern. Auf derselben Seite eine kontrollierte
Testadresse eingeben und **Testnachricht einplanen** wählen. Dies erzeugt
einen persistenten Auftrag mit festem Testtext; der Webrequest öffnet keine
SMTP-Verbindung. Doppelte Übermittlung desselben Formulars erzeugt keinen
zweiten Auftrag. Ein neu geöffnetes Testformular erlaubt einen neuen Test.

Als **root** starten; der eigentliche Prozess läuft als **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 mail-worker --limit 20
```

Erwartete Ausgabe beispielsweise `sent=1 retry=0 failed=0 uncertain=0`.
Bei deaktiviertem Versand, pausierten Plugins oder noch nicht fälligen Jobs
sind alle Zähler null. Sie beschreiben ausschließlich diesen Aufruf, nicht
den gesamten Bestand. Fehlerhafte Aufträge stehen in der Admin-Übersicht;
der erfolgreiche CLI-Lauf allein bestätigt nicht die Zustellung aller Jobs.

Der Befehl arbeitet einmalig und beendet sich. Der oben eingerichtete Timer
ruft denselben Worker regelmäßig auf. Ohne Timer muss für erneute Versuche nach
der angezeigten Fälligkeit derselbe Befehl wieder ausgeführt werden.

Ergebnisprüfung: Seite neu laden, Status und Versuchszähler prüfen; bei
„Angenommen“ zusätzlich den Eingang im kontrollierten Testpostfach prüfen.
„Angenommen“ bedeutet ausschließlich Übernahme durch den SMTP-Server,
keine Empfangs- oder Lesebestätigung. Es wird keine exakt einmalige Zustellung
zugesagt. Ein Empfänger pro Auftrag, Textnachrichten bis 64 KiB UTF-8,
Betreff bis 200 Zeichen, keine Anhänge und keine SMTPUTF8-Adressen.

## Zustände und Störungen

| Zustand | Verhalten / Hilfe |
|---|---|
| Wartend | Auftrag gespeichert; Aktivierung, Plugin-Status und Worker-Aufruf prüfen |
| In Bearbeitung | Ein Worker hat exklusiv übernommen; kein zweiter Worker übernimmt denselben Auftrag |
| Wiederholung geplant | Vorübergehender Fehler; Fälligkeit abwarten und Worker erneut aufrufen |
| Angenommen | SMTP hat übernommen; kein automatischer oder manueller Neuversand dieses Auftrags |
| Fehlgeschlagen | Dauerhafte Ablehnung, Konfigurations-/Protokollfehler oder fünf erfolglose Versuche; Ursache korrigieren, anschließend ausdrücklich erneut einplanen |
| Ungeklärt | Verbindungsabbruch während DATA oder verwaister Workerauftrag; keine automatische Wiederholung |

Verbindungsfehler vor der Datenübertragung und SMTP-4xx-Antworten können
wiederholt werden; SMTP-5xx-Ablehnungen beenden den Zyklus. Unterbrechungen
während der Datenübertragung können trotz fehlender Antwort bereits zugestellt
worden sein. Nach 300 Sekunden wird ein nicht abgeschlossener Workerauftrag
beim **nächsten Worker-Aufruf** als ungeklärt markiert, auch bei pausiertem SMTP.
Ein hängender alter Prozess kann noch aktiv sein: vor manueller Wiederholung
den Prozess beenden und beim Relay/Testempfänger prüfen, ob bereits zugestellt
wurde. Die erforderliche Checkbox bestätigt das verbleibende Doppelzustellrisiko.
Ein Versuchs-Token verhindert, dass ein verspätetes Ergebnis eines alten Workers
den Status eines neuen Versuchs überschreibt; es kann keine bereits laufende
SMTP-Übertragung zurückrufen.

Manuelles erneutes Einplanen setzt den Zykluszähler auf null, erhält aber den
lebenslangen Gesamtzähler, Auftrag und Idempotenzschlüssel. Aufträge werden
nicht gelöscht. Eine deaktivierte SMTP-Konfiguration oder ein deaktiviertes
Plugin verbraucht keine Versuche. Die gespeicherte Plugin-Auswahl wird vor
jeder Übernahme gelesen; eine Deaktivierung stoppt neue Übernahmen sofort,
auch im noch laufenden Worker. Bereits übernommene Sendungen können fertiglaufen.
Neue Plugin-Aktivierungen benötigen weiterhin einen Prozessneustart.

Bei Verbindungsfehlern Host, Port, Firewall und TLS-Vertrauen prüfen. Bei
fehlendem Passwort TOML-Datei und Prozessneustart prüfen. Bei Ablehnungen
Absender-/Empfängerfreigaben beim SMTP-Anbieter kontrollieren. Ungültige gespeicherte
SMTP-Werte stoppen den Worker; die Admin-Seite erlaubt erneutes Speichern.

### „Angenommen“, aber keine Nachricht im Postfach

„Angenommen“ wird erst nach SMTP-Antwort **250 auf die vollständige DATA-Übertragung**
gespeichert (`services/mail.py`, `deliver`). Der Worker hat den Auftrag damit
an das konfigurierte Relay übergeben. Die weitere Zustellung, Quarantäne oder
spätere Ablehnung ist ohne Relay-/Postfachprotokolle nicht erkennbar.
Den Timer erneut einzurichten hilft bei diesem Status nicht.

Als **Administrator in der Weboberfläche** beim Vergleich mit einem funktionierenden
Altsystem zuerst dieselbe freigegebene Absenderadresse verwenden: Nur dieses Feld
ändern, speichern und einen **neuen** Testauftrag an dasselbe kontrollierte interne
Testpostfach anlegen. Host, Port, Transport und Anmeldung unverändert lassen.
Eine neue Adresse mit gleichem Domainnamen ist nicht automatisch ebenso freigegeben.
Erwartetes Ergebnis: neuer Auftrag „Angenommen“ und Eingang im Testpostfach.

Wenn weiter kein Eingang erfolgt:

1. Spamordner und gegebenenfalls zentrale Quarantäne prüfen. Bei einem vorhandenen
   Absenderpostfach auch nach einer Unzustellbarkeitsnachricht suchen.
2. Die Mailadministration soll die Nachricht im Relay nachverfolgen: Zeitpunkt
   aus der Übersicht (einschließlich Zonenname und UTC-Abstand), Empfänger, beim Versand verwendeter Absender und
   Message-ID bereitstellen. NeoFab2 bildet diese als
   `<neofab2-AUFTRAGSID@ABSENDERDOMAIN>`; die Auftrags-ID steht in der Tabelle.
   Das ist die Nachrichtenkennung, keine SMTP-Queue-ID.
3. Bei verschiedenen Installationen zusätzlich die tatsächlich am Relay sichtbare
   Quell-IP und die Relay-Freigabe vergleichen. Die im Browser angezeigte Webadresse
   beweist keine bestimmte SMTP-Quell-IP (beispielsweise bei NAT).

Ein bereits angenommener Auftrag wird nicht erneut eingeplant; ein neuer Test
bekommt eine neue Kennung. Ohne Absendervergleich und Relay-Nachverfolgung sind
Absenderfreigabe, Filterung oder Routing nur mögliche Ursachen, keine Diagnose.

Codevergleich am 21.09.2026: Bei leerem Benutzernamen und ausgeschaltetem TLS/SSL
nutzen beide Anwendungen unverschlüsseltes SMTP und die konfigurierte Adresse
als Envelope-Absender. NeoFab verwendet `send_message` im SMTP-Kontextmanager;
NeoFab2 prüft MAIL/RCPT/DATA einzeln und schließt danach die Verbindung. NeoFab2
setzt zusätzlich eine stabile Message-ID und Quoted-Printable-Kodierung. Aus
diesen Unterschieden allein ist kein Zustellfehler nach SMTP-Annahme nachgewiesen.

## Transaktionen und Plugin-Vertrag

`services/mail.py` kapselt Transport und Outbox. `core/mail.py` enthält
ausschließlich die Admin-Oberfläche. `plugin_api/notifications.py` ist der
additive öffentliche API-1-Vertrag:

```python
from neofab2.plugin_api import Permission
from neofab2.plugin_api.notifications import enqueue_email

# Im bestehenden Plugin-Manifest:
# permissions=(Permission("example.mail_send", ("staff", "admin")),)
# mail_permission="example.mail_send"

# In einem authentifizierten Plugin-Request:
job_id = enqueue_email(
    "example", "event:123:recipient:45", "test@example.org",
    "Synthetischer Test", "Synthetischer Nachrichtentext",
    connection=connection,  # optional: aktive NeoFab2-Transaktion des Aufrufers
)
```

Das Beispiel ist kein ausgeliefertes Fachplugin. Einstieg **und** ausdrücklich
deklariertes Versandrecht werden gegen den aktuellen Kontostand geprüft;
Administratoren erhalten keine pauschale Ausnahme. Fachliche Empfänger-/Besitzer-
und Objektberechtigungen muss das Plugin zusätzlich prüfen. Der Vertrag ist für
authentifizierte Requests vorgesehen, nicht für beliebige Hintergrundcallbacks.

Ohne `connection` öffnet und committet der Dienst eine eigene Transaktion.
Mit einer aktiven Verbindung derselben NeoFab2-Engine bleibt die Transaktion
beim Aufrufer: Fachänderung und Versandauftrag können gemeinsam zurückgerollt
werden. SMTP läuft erst später und außerhalb der Schreibtransaktion.
`(module_id, dedupe_key)` ist eindeutig. Identische Wiederholungen liefern dieselbe
Auftrags-ID, anderer Inhalt mit gleichem Schlüssel wird abgewiesen. Die
Message-ID bleibt pro Auftrag stabil, ist aber keine Zustellgarantie.
Die drei ausgelieferten Testplugins erhalten keine zusätzlichen Versandrechte;
ein synthetischer Vertragsfixture prüft diese Schnittstelle.

## Migration, Sicherung und Betriebsgrenzen

Die Outbox wurde mit Revision `0009_mail_outbox`, Vorgänger `0008_core_files`, eingeführt.
Sie ergänzt ausschließlich `core_mail_outbox` samt Index und Eindeutigkeitsregel;
keine automatische Migration beim App-Start, keine Änderung alter NeoFab-Daten.

Beim normalen Update das bestehende Update-Skript verwenden. Zuvor alle
zusätzlich gestarteten Worker bzw. selbst eingerichteten Aufrufpläne stoppen:
das Update-Skript ab 0.1.14 stoppt die eigenen Versandunits automatisch.
Eigene Cronjobs oder manuelle Worker bleiben Betreiberverantwortung. Alternativ nach Sicherung bei
gestopptem Webdienst/Worker als **root**, ausgeführt durch **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 migrate
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
systemctl start neofab2.service
```

Aktueller Schemastand: `0011_audit_status` ergänzt Audit und Worker-Beobachtung.
Die Kontoverfahren und zwei optionale Zuordnungsfelder der Outbox stammen aus
`0010_account_flows`. Ergebnis: Readiness erfolgreich,
Anwendungsversion 0.1.16, SMTP-Seite erreichbar.
Erst anschließend Worker wieder ausführen. Plugin-Versionen bleiben 0.1.0.

Die SQLite-Sicherung umfasst die Outbox samt Empfängern und Nachrichtentexten.
Diese Daten und die TOML-Sicherung sind vertraulich zu behandeln. Es gibt noch
keine automatische Aufbewahrungs-/Löschroutine. Nach Restore zunächst **keinen
Worker starten**: SMTP im Web pausieren und gesicherten Auftragsstand gegen
bereits versandte Nachrichten abgleichen. Ein älteres Backup kann bereits
zugestellte Nachrichten erneut als wartend enthalten. Rückkehr zu altem Code
erfordert die dazu passende Datenbanksicherung; kein automatisches Downgrade.

## Prüfstand

Automatisierte Tests verwenden ausschließlich synthetische Konten, lokale
Testdatenbanken und simulierte SMTP-Transporte. Geprüft werden Rechte/CSRF,
Secretschutz, Einstellungen, Migration von 0008, Sicherung, Neustart,
Idempotenz/Rollback, Plugin-Pause, parallele Worker, begrenzte Wiederholung,
abgelaufene Übernahme, verspätetes Ergebnis, TLS-Modi, Status und CLI.
Zusätzlich ab 0.1.14: realer SMTP-Dialog an einem lokalen synthetischen Relay,
Port-25-Persistenz und Formularfehler sowie simulierte systemd-Steuerung geprüft.
Ein echter SMTP-Anbieter, reale Postfachzustellung, visuelle Browserabnahme und
Debian/systemd-Workerbetrieb sind noch nicht geprüft. Keine vollständige Core-Abnahme.

Transportreferenz: [Python-Standardbibliothek smtplib](https://docs.python.org/3/library/smtplib.html).

## Nutzerrückmeldung vom 21.09.2026

Zwei Testnachrichten des Absenders `neofab2` wurden im Hochschulpostfach im
Junk-Ordner gefunden; interne Zustellung damit vom Benutzer bestätigt.
Die externe Testnachricht wurde laut Benutzer nicht empfangen. Eine Beschränkung
des Relays auf interne Empfänger ist eine Vermutung und nicht anhand von
Relay-Protokollen bestätigt. Der Benutzer behandelt den E-Mail-Punkt vorerst
als gelöst. Keine Zusage externer Zustellung und keine allgemeine SMTP-Abnahme.
Ab 0.1.15 zeigt der [Betriebsstatus](Core_Audit_und_Betriebsstatus.md) zusätzlich
den zuletzt beobachteten Worker-Lauf; dies ersetzt keinen Zustellnachweis.
