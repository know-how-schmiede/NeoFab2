# SMTP und persistente Versandaufträge – 0.1.12

Paket 1 des [Core-Arbeitsplans](Core_Naechste_Schritte.md): S05, N05 und
Teilumfänge von S06/N01; Migration X07, Betriebsanleitung X05. Keine Fachplugins.
Registrierung, Aktivierung, Willkommens- und Passwort-Reset-E-Mails folgen in
Paket 2. Dieser Stand implementiert den technischen Versand und einen Testauftrag.

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

Der Befehl arbeitet einmalig und beendet sich. Er installiert keinen Scheduler
und keinen weiteren systemd-Dienst. Für einen erneuten Versuch nach der
angezeigten Fälligkeit denselben Befehl wieder ausführen. Ein späterer
regelmäßiger Betrieb kann diese CLI unter demselben Dienstbenutzer aufrufen;
ein automatisch installierter Timer ist noch nicht Bestandteil dieses Pakets.

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

Neue explizite Revision `0009_mail_outbox`, Vorgänger `0008_core_files`.
Sie ergänzt ausschließlich `core_mail_outbox` samt Index und Eindeutigkeitsregel;
keine automatische Migration beim App-Start, keine Änderung alter NeoFab-Daten.

Beim normalen Update das bestehende Update-Skript verwenden. Zuvor alle
zusätzlich gestarteten Worker bzw. selbst eingerichteten Aufrufpläne stoppen:
das Update-Skript kennt nur den Webdienst. Alternativ nach Sicherung bei
gestopptem Webdienst/Worker als **root**, ausgeführt durch **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 migrate
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
systemctl start neofab2.service
```

Ergebnis: Readiness erfolgreich, Anwendungsversion 0.1.12, SMTP-Seite erreichbar.
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
Ein echter SMTP-Anbieter, reale Postfachzustellung, visuelle Browserabnahme und
Debian/systemd-Workerbetrieb sind noch nicht geprüft. Keine vollständige Core-Abnahme.

Transportreferenz: [Python-Standardbibliothek smtplib](https://docs.python.org/3/library/smtplib.html).
