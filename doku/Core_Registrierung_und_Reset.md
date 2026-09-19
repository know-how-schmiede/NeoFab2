# Registrierung, Aktivierung und Passwort-Reset – 0.1.13

Paket 2 des [Core-Arbeitsplans](Core_Naechste_Schritte.md), Funktions-IDs
U02–U04 und S06, ergänzend U01/U05/U06/U08 und X05–X07. Technische
Grundlage ist die [SMTP-Warteschlange](Core_SMTP_und_Versand.md).
Keine Fachplugins und keine Produktivmigration. Version 0.1.13 folgt auf den
vorliegenden Stand 0.1.12.

## Vor der Freischaltung

Selbstregistrierung **und** Passwort-Rücksetzung per E-Mail sind standardmäßig
ausgeschaltet. Bereits vorhandene Konten behalten ihren Aktivstatus; deaktivierte
Konten werden weder als wartende Registrierung behandelt noch automatisch aktiviert.
Administratives Anlegen und der lokale Notfall-Reset bleiben verfügbar.

Als **root im NeoFab2-Testcontainer** die vorhandene geschützte Datei
`/etc/neofab2/config.toml` mit einem Editor ergänzen; vorhandene Werte erhalten:

```toml
PUBLIC_BASE_URL = "https://neofab2.example.org"
```

Den Beispielhost durch die tatsächliche öffentliche Adresse ersetzen.
Erlaubt ist eine HTTP(S)-Origin mit optionalem Port, ohne Pfad, Zugangsdaten,
Query oder Fragment. HTTPS ist vorgeschrieben; HTTP ist ausschließlich mit
`SESSION_COOKIE_SECURE = false` für ein isoliertes Testnetz erlaubt.
Beispiel dafür: `http://127.0.0.1:5000`. Ein abschließender Slash wird entfernt.
Die Anwendung bildet E-Mail-Adressen für Links ausschließlich aus dieser
Konfiguration, niemals aus dem vom Browser gesendeten Host-Header.

```bash
systemctl restart neofab2.service
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: `Database and schema ready.`. Worker ebenfalls mit der aktuellen
Konfiguration starten. SMTP zuerst konfigurieren und mit kontrollierter Adresse
testen; ein laufender Worker ist für die Zustellung erforderlich.

Als **NeoFab2-Administrator** unter **Administration → Systemeinstellungen →
Registrierung und Kontowiederherstellung**:

1. Die zugelassenen E-Mail-Domains festlegen, höchstens 100, eine pro Zeile.
   `example.org` erlaubt keine Subdomain wie `students.example.org`; diese
   erhält bei Bedarf einen eigenen Eintrag. Keine Wildcards oder URLs.
2. Alternativ bewusst **Ausdrücklich alle E-Mail-Domains erlauben** auswählen.
   Eine leere Liste ohne diese Auswahl erlaubt keine Freischaltung.
3. Selbstregistrierung und/oder Passwort-Rücksetzung per E-Mail einschalten
   und speichern. Ohne öffentliche URL oder aktiviertes SMTP wird das abgewiesen.

Neue Registrierungskonten erhalten immer Rolle **Benutzer**, unabhängig von
zusätzlich übermittelten Formularfeldern. Die Domain-Regel gilt nur für
Registrierung und Aktivierung. Bestehende aktive Konten können auch außerhalb
der Liste einen Reset anfordern. Konkrete Produktionsdomains werden nicht
vorbelegt; ihre Freigabe bleibt eine Betriebsentscheidung des Administrators.

## Registrierung und Aktivierung

Als **Gast** auf der Anmeldeseite **Registrieren** wählen, Anzeigename und
E-Mail eingeben. Das Konto wird inaktiv mit dem gesonderten Status
**Wartet auf E-Mail-Aktivierung** angelegt. Ein Passwort wird hier noch nicht
festgelegt. Konto, Aktivierungsvorgang und Versandauftrag werden gemeinsam
gespeichert; ein Fehler beim Einplanen rollt den gesamten Vorgang zurück.

Die Antwort verrät nicht, ob eine Adresse bereits vorhanden, gesperrt oder
nicht zur Registrierung zugelassen ist. Erneutes Registrieren überschreibt
weder Namen noch Zugangsdaten eines bestehenden Kontos.

Die E-Mail nennt die Seite `/activate` und einen vollständigen Aktivierungscode.
Den Code dort einfügen und ein neues Passwort zweimal eingeben. Der Code ist
24 Stunden ab Anforderung gültig und nur einmal verwendbar. Erst nach dieser
Bestätigung wird das Konto aktiv. Die Passwortwahl durch den Postfachinhaber
verhindert, dass ein fremder Antragsteller ein vorher gewähltes Passwort behält.
Eine Willkommensnachricht wird eingeplant. Anschließend regulär anmelden;
es gibt keine automatische Anmeldung durch die Aktivierung.

Unter **Neuen Aktivierungscode anfordern** (`/activation-request`) können
wartende Konten einen neuen Code erhalten. Frühestens nach 60 Sekunden wird
ein neuer Vorgang erzeugt; der vorherige Code wird dann ungültig. Die erneute
Anforderung ändert das Konto nicht. Ein deaktiviertes Bestandskonto wird dadurch
nicht zu einer wartenden Registrierung und kann so nicht reaktiviert werden.

## Passwort vergessen

Als **Benutzer oder Administrator ohne Anmeldung** auf der Anmeldeseite
**Passwort vergessen** wählen und die eigene Adresse eingeben. Der Aufruf
ändert weder Passwort noch Kontostatus oder bestehende Sitzungen. Nur aktive
Konten ohne ausstehende Aktivierung erhalten einen Versandauftrag. Bekannte,
unbekannte und deaktivierte Adressen erhalten dieselbe allgemeine Antwort.

Die E-Mail nennt `/reset-password` und einen Code. Diesen innerhalb von
30 Minuten ab Anforderung zusammen mit dem zweimal eingegebenen neuen Passwort
absenden. Die gemeinsame Passwortregel lautet weiterhin 8–128 Zeichen.
Das Passwort wird als scrypt-Hash gespeichert, alle bisherigen Sitzungen werden
widerrufen und alle noch offenen Aktivierungs-/Resetcodes des Kontos ungültig.
Eine Benachrichtigung über die Passwortänderung wird ohne Passwort eingeplant.
Danach ist eine normale Anmeldung erforderlich.

Ungültige, abgelaufene, bereits verwendete und zum falschen Verfahren gehörende
Codes werden abgewiesen. Zwei parallele Einlösungen können nur einmal erfolgreich
sein. Bei Tippfehlern in der Passwortbestätigung bleibt ein gültiger Code nutzbar.
Der lokale Notfallzugang bleibt unverändert:

```bash
bash /opt/neofab2/script/resetAdminPassword
```

Ausführungsbenutzer: **root**. Dieses Verfahren bleibt unabhängig von SMTP;
es widerruft auch noch offene E-Mail-Rücksetzcodes.

## Administratoren, Status und Widerruf

Die Benutzerliste unterscheidet wartende Aktivierung von einem gesperrten Konto.
Beim administrativen Bearbeiten eines wartenden Kontos weist das Formular
ausdrücklich darauf hin: **Speichern beendet das E-Mail-Aktivierungsverfahren**
und übernimmt den gewählten aktiven oder gesperrten Zustand. Zum Aktivieren
muss der Administrator ein Anfangspasswort setzen und sicher übergeben.
Zum Sperren den Aktiv-Haken leer lassen und speichern. Keine automatische
Willkommensnachricht bei diesem administrativen Ersatzverfahren.

Änderungen von Passwort, E-Mail, Rolle oder Aktivstatus widerrufen offene Codes;
auch Deaktivieren und anschließendes Wiederaktivieren macht alte Codes nicht
wieder gültig. Profil-Passwortwechsel und lokaler Admin-Reset tun dasselbe.
Normale Profiländerungen wie Darstellung oder Sprache widerrufen Codes nicht.

Geänderte Registrierungs-/Domain-Regeln widerrufen alle noch offenen
Aktivierungscodes. Abschalten der Passwort-Rücksetzung widerruft offene
Resetcodes. Nach erneuter Freischaltung muss ein neuer Code angefordert werden.
Die Konten bleiben erhalten. Beschädigte gespeicherte Kontoeinstellungen
schalten beide öffentlichen Verfahren sicherheitshalber ab.

## Worker, Schutz der Codes und Fehlerhilfe

Als **root**, ausgeführt durch den Dienstbenutzer **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 mail-worker --limit 20
```

Ergebnis in der SMTP-Übersicht und im kontrollierten Testpostfach prüfen.
Ist SMTP später pausiert oder ausgefallen, bleiben Konten und Aufträge erhalten.
Codes laufen dennoch ab ihrer Anforderung ab. Abgelaufene, widerrufene oder
inzwischen nicht mehr zum Konto passende Aufträge werden vor Versand als
fehlgeschlagen mit **Kontoanfrage abgelaufen oder nicht mehr gültig** markiert.
Dann einen neuen Code anfordern; manuelles Wiederholen verlängert die Frist nicht.
Ein bereits übernommener SMTP-Vorgang lässt sich nicht zurückrufen; die
Gültigkeit wird deshalb auch beim Einlösen erneut geprüft.

Ein Code besteht aus zufälliger 128-Bit-Kennung und einem HMAC-SHA256-Nachweis.
In der Token-Tabelle stehen nur Kennung, Hash des vollständigen Codes,
Kontobindung und Zeitangaben. Der vollständige Code wird erst im Worker mithilfe
von `SECRET_KEY` erzeugt und der E-Mail hinzugefügt. Die persistente Outbox
enthält für diese Nachrichten einen Platzhalter statt des Codes. Der SMTP-Dialog
gibt Codes oder Passwörter nicht aus. Ein Wechsel von `SECRET_KEY` macht alte
Codes ungültig; danach neue Codes anfordern.

Codes werden ausschließlich im POST-Formular eingelöst, nicht durch GET, URL-
Parameter oder automatische Mail-Link-Aufrufe. Damit enthalten die vorgesehenen
URLs keine Codes. Ein Mail-Linkscanner aktiviert kein Konto und verbraucht
keinen Code. Request-Bodies dürfen im Reverse Proxy, Debugger oder Monitoring
nicht protokolliert werden. Die E-Mail und das Postfach selbst enthalten den Code
und müssen entsprechend geschützt bleiben.

Anfragen sind pro 15 Minuten auf drei je Adresse und 20 je Quell-IP begrenzt;
Einlöseversuche zusätzlich auf 20 je IP. Wiederholungen innerhalb der
60-Sekunden-Sperre zählen mit. Die getrennte Begrenzungstabelle speichert nur
HMAC-Schlüssel, keine Klartext-IP-/Adresslisten. Die Limits gelten auch bei
parallelen Prozessen. Nach einem Reverse Proxy zählt ohne gesonderte vertrauenswürdige
Proxy-Konfiguration dessen Socket-IP; Forwarded-Header werden nicht blind vertraut.
Keine CAPTCHA- oder weitergehende Anti-Bot-Lösung in diesem Paket.

Öffentliche Formulare haben englische Ausgangstexte und deutsche Übersetzungen;
wichtige öffentliche Texte und alle vier E-Mail-Typen sind zusätzlich französisch.
Fehlende Oberflächentexte verwenden den vorhandenen englischen Fallback.
Neue Registrierungen übernehmen die gewählte Gast-Sprache, bestehende Konten
ihre gespeicherte Kontosprache. Codes und Passwörter werden bei Formularfehlern
nicht ins HTML zurückgeschrieben.

## Migration, Sicherung und Prüfgrenzen

Neue explizite Revision **`0010_account_flows`** nach `0009_mail_outbox`:
`core_users.activation_pending` (für alle Bestandskonten false), Tabellen
`core_account_tokens` und `core_account_limits`, zwei optionale Zuordnungsfelder
in `core_mail_outbox`. Vorhandene Konten, Sitzungen und Versandaufträge bleiben
erhalten. Anwendungsstart erzeugt oder migriert kein Schema.

Vor Update eigene Worker/Aufrufpläne stoppen und wie bisher sichern. Als **root**
das vorhandene Update-Skript verwenden, nachdem Version 0.1.13 manuell committed
und auf den verwendeten Branch übertragen wurde:

```bash
bash /opt/neofab2/script/upDateNeoFabService
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version **0.1.13**, Bereitschaft erfolgreich, beide Verfahren zunächst
ausgeschaltet. Keine automatische Freischaltung oder Zustellung durch das Update.
Bei bereits manuell installiertem Code die fehlende Migration bei gestoppten
Prozessen explizit als Dienstbenutzer mit `neofab2 migrate` ausführen.

SQLite-Sicherungen enthalten auch Token-Hashes und Warteschlange; `SECRET_KEY`
getrennt geschützt halten. Datenbank **und** Konfigurationsschlüssel zusammen
ermöglichen die Rekonstruktion noch gültiger Codes. Ein altes Backup kann zuvor
verbrauchte Codes oder Sitzungen wiederherstellen. Nach Restore zunächst keine
öffentlichen Kontoverfahren/Worker freigeben; beide Verfahren deaktivieren und
vor Wiederfreigabe neue Codes anfordern lassen. Bestehende Sitzungsschlüssel
bei sicherheitsbedingter Wiederherstellung gegebenenfalls wechseln. Es gibt
noch keine automatische Löschung wartender Konten oder alter Tokenmetadaten.

Geprüft wird mit synthetischen Konten und simuliertem SMTP: Registrierung und
Domain-Grenzen, Aktivierung, Passwort-Reset, Rechte/CSRF, Rollenmanipulation,
abgelaufene/falsche/verbrauchte Codes, Limits, Parallelität, Transaktionsabbruch,
SMTP-Pause, Geheimnisschutz, Sprache, Migration, Neustart und Sicherung/Restore.
Echte Postfachzustellung, visuelle Browserabnahme und Debian/LXC-Betrieb bleiben
separate Prüfungen. Paket 3 (Audit-Logs/Betriebsstatus) folgt als nächstes;
die vollständige Core-Abnahme ist weiterhin offen.

Sicherheitsreferenz: [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).
