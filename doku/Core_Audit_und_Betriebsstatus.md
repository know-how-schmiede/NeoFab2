# Audit-Protokoll und Betriebsstatus – 0.1.15

Paket 3 des [Core-Arbeitsplans](Core_Naechste_Schritte.md): S09, S12 und N01,
Rechte U06, Migration X07, Betrieb X05/X06. Nur Core und technische Testplugins.

## Bedienung und Rechte

Als **Administrator** unter **Administration → Audit-Protokoll** bzw.
**Administration → Betriebsstatus** öffnen. Die Rechte `core.audit.view` und
`core.status.view` gehören zunächst ausschließlich zur Administratorrolle.
Gäste werden zur Anmeldung geleitet, Benutzer und Mitarbeiter erhalten auch beim
direkten Seitenaufruf 403. Gesperrte Konten verlieren den Zugriff. Beide Seiten
sind nur lesend; es gibt keinen Web-Endpunkt zum Verändern oder Löschen von Logs.
Englisch ist Ausgangssprache; neue Bedienhinweise sind deutsch übersetzt,
Französisch verwendet zunächst den englischen Fallback. Ereigniscodes sind stabil.

Das Audit-Protokoll zeigt 50 Ereignisse pro Seite, neueste zuerst; bei gleichen
UTC-Zeitpunkten entscheidet die Ereignis-ID. Ein Filter grenzt auf einen Core-
Ereignistyp ein. Plugin-Ereignisse erscheinen in der ungefilterten Liste.
Ausführendes Konto und Ziel werden als numerische IDs gezeigt. Ein Strich steht
für unbekannt, anonym oder lokalen Betriebszugang; der Zieltyp folgt dem Ereignis
(bei Benutzerereignissen eine Benutzer-ID, bei Plugin-Aktionen eine Plugin-Objekt-ID).

## Ereignisse und Datensparsamkeit

| Ereignis | Inhalt / Grenze |
|---|---|
| Anmeldung erfolgreich / fehlgeschlagen, Abmeldung | Erfolgreiche Anmeldung und Abmeldung mit Konto-ID; Fehlversuch ohne eingegebene Adresse oder IP. Bereits rate-limitierte oder formal ungültige Versuche werden nicht zusätzlich protokolliert |
| Zugriff verweigert | Authentifizierter Zugriff ohne Recht durch den zentralen Rechte-Decorator; keine URL, Parameter oder Formularwerte. Individuelle Objektprüfungen außerhalb dieses Decorators sind nicht automatisch erfasst |
| Konto angelegt / administrativ geändert | Ausführendes Konto und Zielkonto; Rollenwechsel, Aktivierung/Sperrung und administratives Passwortsetzen zusätzlich als eigene Ereignisse |
| Passwort geändert / lokaler Notfall-Reset | Nur Konto-ID; keine Hashes oder Passwörter |
| Aktivierung / Passwort-Reset per Code | Erfolgreiches Einlösen mit Zielkonto; keine Codes, Token-IDs, Links oder Hashes |
| System-, SMTP- und Kontoverfahrenseinstellungen geändert | Nur Ereignis und ausführendes Konto, keine alten/neuen Konfigurationswerte |
| Plugin-Auswahl geändert / lokal wiederhergestellt | Ereignis und ggf. ausführendes Konto; aktueller Zielzustand steht im Betriebsstatus |
| Audit-Protokoll bereinigt | Zeitpunkt und gelöschte Anzahl; lokaler Betreiberzugang |

Gespeichert werden ausschließlich UTC-Zeit, Ereignis-ID, Modulkennung,
Ereigniscode, optionale Konto-/Objekt-IDs und optionale Anzahl. Keine Freitext-
Details, Namen, E-Mail-Adressen, IPs, Requestdaten, Sitzungs- oder Reset-Tokens,
Passwörter, SMTP-Antworten, Nachrichteninhalte oder Geheimnisse.

Schreibende Core-Aktionen und Audit-Ereignis teilen eine Transaktion. Scheitert
das Audit-Schreiben, wird auch die Änderung zurückgerollt. Ein Rollback erzeugt
kein erfolgreiches Ereignis. Die Tabelle wird ausschließlich durch Migration
angelegt; fehlende Tabellen werden nicht automatisch repariert. Schemafehler
führen zu fehlender Bereitschaft. SQL-/Betriebsfehler sind lokal zu prüfen.

Kein vollständiges HTTP-Zugriffsprotokoll: Profilkosmetik, Auswahllistenpflege,
Dateidownloads, einzelne Versandaufträge, CSRF-Fehler und abgewiesene öffentliche
Aktivierungscodes sind nicht zusätzlich erfasst. Versandfehler bleiben mit ihren
festen Kategorien in der vorhandenen Outbox sichtbar. Es gibt keine rückwirkende
Erfassung alter Aktionen und keine kryptografische Manipulationssicherung gegen
Administratoren mit direktem Datenbank-/Dateizugriff.

## Betriebsstatus

Die Seite zeigt Core-Version und tatsächlich gelesene Schema-Revision,
SMTP aktiv/pausiert/ungültig, Anzahl der Versandaufträge je Zustand sowie
Plugin-Versionen mit **in diesem Prozess geladen** und **für nächsten Start
ausgewählt**. Bei abweichender Auswahl wird ein Neustart empfohlen. Eine beschädigte
oder inkompatible gespeicherte Auswahl erscheint als Fehler ohne rohe Konfigurationsdaten.
Bei bereits am Start ungültiger Plugin-Auswahl kann die Webanwendung nicht starten;
dann den lokalen Wiederherstellungsweg aus der Betriebsanleitung verwenden.

Der Versandworker schreibt Beginn und Ende seines letzten beobachteten Laufs in
eine eigene Tabelle. Auch ein Lauf bei pausiertem SMTP ist eine Beobachtung.
Nicht behandelte Workerfehler werden als `failed` erfasst; SMTP-Einzelfehler
stehen weiterhin bei den Versandaufträgen. Nach mehr als **300 Sekunden** seit
Beginn bzw. Ende der letzten Beobachtung erscheint der Stand als veraltet.
Nach einem Prozessabbruch fehlt ggf. das Ende. Eine ältere parallel laufende
Instanz darf den Status eines später gestarteten Laufs nicht überschreiben.
Es wird nur der jüngste begonnene Lauf gespeichert, kein vollständiger Laufverlauf.

**Die Beobachtung prüft weder systemd noch DNS, Netzwerk oder Postfacheingang.**
Ein manueller Lauf zählt genauso wie ein Timer-Lauf. Ein aktueller abgeschlossener
Lauf beweist keine erfolgreiche Zustellung aller Nachrichten. Bei Datenbankausfall
kann auch die Fehlerbeobachtung fehlen. Seite zum Aktualisieren neu laden.

Als **root im NeoFab2-Container** bei veraltetem/fehlendem Worker-Stand:

```bash
systemctl status neofab2-mail.timer --no-pager
journalctl -u neofab2-mail.service -n 40 --no-pager
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Timer aktiv, aktuelle Laufzähler im Journal, Datenbank und Schema bereit.
Falls der Timer fehlt, `bash /opt/neofab2/script/setupNeoFabService` ausführen.
Falls Schema fehlt, kontrolliert aktualisieren/migrieren; nicht im laufenden
Betrieb Tabellen manuell erzeugen. [SMTP-Details](Core_SMTP_und_Versand.md).

## Aufbewahrung: Vorschau und bewusste Bereinigung

Standard: **keine automatische Löschung**. Der lokale Befehl verwendet ohne
andere Angabe eine Grenze von **180 Tagen**, zulässig sind 1–3650 Tage. Diese
Angabe ist eine technische Voreinstellung; eine betriebliche Aufbewahrungsregel
ist separat festzulegen. Nur Ereignisse strikt älter als die Grenze werden erfasst.

Als **root**, ausgeführt unter dem Dienstbenutzer **neofab2**, zuerst Vorschau:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 audit-prune --days 180
```

Ergebnis: UTC-Grenze und Anzahl, anschließend `Preview only; no events deleted.`
Die Vorschau löscht nichts. Nach passender Sicherung und ausdrücklicher
betrieblicher Entscheidung erfolgt die Bereinigung mit zusätzlicher Bestätigung:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 audit-prune --days 180 --apply
```

Ergebnis: Bestätigungsfrage, anschließend tatsächlich gelöschte Anzahl und ein
neues Audit-Ereignis `audit.pruned`. Abbruch erhält alle Ereignisse. Zum Zeitpunkt
der Ausführung wird die Anzahl erneut ermittelt. Es gibt keinen Timer für diese
Bereinigung. Konten, Outbox, Dateien und letzter Worker-Stand bleiben erhalten.
SQLite-Dateigröße wird dadurch nicht zwingend kleiner; kein automatisches VACUUM.
Backups können ältere Ereignisse weiterhin enthalten und benötigen eine eigene
Aufbewahrungsregel. Löschungen lassen sich nur aus einer passenden Sicherung
wiederherstellen; daraus folgt keine Autorisierung einer produktiven Löschung.

## Minimaler Plugin-Vertrag (API 1)

```python
from neofab2.plugin_api.audit import record_action

# permission muss im Plugin-Vertrag deklariert sein.
# Eigene Objektberechtigung vorher prüfen!
record_action("example", "example.manage", target_id=42, connection=connection)
```

Der Dienst prüft die aktuelle Konto-/Plugin-Freigabe, Plugin-Einstiegsrecht und
Aktionsrecht. Administratoren haben keinen Wildcard-Zugriff. Das Ereignis ist
exakt der deklarierte Berechtigungscode; beliebige Ereignis-/Freitextwerte sind
nicht erlaubt. Die Ziel-ID ist eine nichtnegative Ganzzahl. Es werden keine
Fachdaten interpretiert; Objektberechtigungen verbleiben beim Plugin.
Mit `connection` muss eine aktive Transaktion derselben NeoFab2-Engine vorliegen;
ohne sie wird eine eigene Transaktion geöffnet. Nur authentifizierte Requests,
kein öffentlicher Log-Upload. Der Vertrag ist mit einem synthetischen Testplugin
geprüft; produktive Fachplugins bleiben gesperrt.

## Migration und Prüfgrenzen

Explizite Migration **0011_audit_status** nach **0010_account_flows** legt
`core_audit_events` samt Zeitindex und `core_worker_status` an. Bestehende
Konten, Einstellungen und Versandaufträge bleiben erhalten. Kein Backfill.
Das normale Update stoppt Webdienst und eigene Versandunits vor Sicherung und
Migration. Zusätzlich gestartete eigene Worker vorher beenden.

Nach Update als **root** prüfen:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: 0.1.15, Schema bereit; beide Admin-Seiten erreichbar. Eine neue Anmeldung
erscheint im Audit-Protokoll, nach dem nächsten Worker-Lauf dessen Beobachtung.
Die neuen Tabellen sind Teil der SQLite-Sicherung. Nach Restore wie bisher SMTP
pausieren und Zustellstand prüfen; ein alter Worker-Zeitpunkt ist keine aktuelle
Betriebsbestätigung. Rückkehr zu altem Code mit passender Datenbanksicherung.

Automatisiert werden nur synthetische Daten verwendet. Rechte, Geheimnisschutz,
Rollbacks, Filter/Paginierung, Aufbewahrungsgrenze/Bestätigung, Workerfehler und
veraltete Beobachtungen, Plugin-Vertrag, Migration, Neustart und Sicherung werden
geprüft. Eigene Browser-/Debian-/LXC-Abnahme und Manipulationssicherung bleiben
offen. Keine vollständige Core-Abnahme.
