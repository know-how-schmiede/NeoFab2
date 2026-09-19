# NeoFab2 – Installation und Wartung (v0.1.12)

Neu in 0.1.12: [SMTP-Einstellungen und persistente Versandaufträge](../doku/Core_SMTP_und_Versand.md),
explizite Migration `0009_mail_outbox` nach `0008_core_files`. Versand ist
standardmäßig deaktiviert. Unter Administration → Systemeinstellungen → SMTP
konfigurieren und Testauftrag erzeugen. Als **root**, ausgeführt durch **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 mail-worker --limit 20
```

Einmaliger Lauf, kein automatisch installierter Scheduler. Ergebniszähler und
Admin-Status prüfen; „Angenommen“ bestätigt nur die SMTP-Übernahme. Vor Updates
zusätzlich gestartete Worker/Aufrufpläne stoppen. Nach Restore zuerst SMTP pausieren
und mögliche bereits erfolgte Zustellungen abgleichen. Passwort, Standardwerte,
Fehlerhilfe und Migrationsbefehle stehen in der verlinkten Detailanleitung.

Seit 0.1.11: [CheckDesign 0.1.0](../doku/CheckDesign.md) für Mitarbeiter und
Administratoren. Unter Administration → Plugins aktivieren und danach neu starten.
Keine neue Schema-Revision gegenüber 0.1.10.

Seit 0.1.10: **Administration** bündelt Benutzerverwaltung, Plugins und
Systemeinstellungen. Paket 0 mit Plugin-Rechten und Testdateien benötigt die
explizite Migration `0008_core_files`. [Anleitung](../doku/Core_Dateien_und_Rechte.md).

Seit 0.1.9: Stammdaten-Button in den Systemeinstellungen, Icons in allen
Buttons und [UI-Gestaltungsregeln](../doku/UI_Gestaltungsregeln.md).
0.1.9 hatte keine neue Schema-Revision gegenüber 0.1.8.

Seit 0.1.8: Abschlussübersichten der Betriebsskripte sowie
[verwaltete Benutzer-Auswahllisten und englische Feldhilfen](../doku/Core_Auswahllisten.md).
Die Listen starten leer; alte Freitexte werden nicht übernommen.

Als **root in einem neuen Debian-13-Container**, nicht auf dem Proxmox-Host:

```bash
apt-get update
apt-get install -y git ca-certificates
git clone https://github.com/know-how-schmiede/NeoFab2.git /root/NeoFab2-setup
bash /root/NeoFab2-setup/script/setupNeoFab
bash /opt/neofab2/script/setupNeoFabService
```

Voraussetzung: v0.1.12 wurde manuell auf den gewählten Remote-Branch gepusht.
Netzwerkzugang zu Debian, GitHub und PyPI erforderlich.

Die Installation fragt nach Bestätigung, Repository, Branch, Port, HTTPS-Nutzung,
Erstadministrator und optionalem Teststart. Vorgaben: Branch `main`, Port `8080`,
HTTPS `j`. Feste Pfade:
Code `/opt/neofab2`, Daten `/var/lib/neofab2`, Konfiguration `/etc/neofab2`,
Benutzer `neofab2`. Vorhandene Installationen werden nicht überschrieben.
Admin-E-Mail und Anzeigename eingeben, Passwort verdeckt wiederholen (8–128
Zeichen). Keine Standardzugangsdaten. Nur für ein isoliertes HTTP-Testnetz bei
HTTPS `n` wählen; sonst wird eine HTTPS-Verbindung für die Login-Cookies benötigt.

Der optionale Test startet aus dem Installationsverzeichnis. Ein Fehler dabei
wird separat gemeldet; die erfolgreiche Basisinstallation bleibt bestehen.
Mit `n` wird der Test übersprungen, Strg+C beendet ihn regulär.

Bei der Erstinstallation wird `create-admin` automatisch nach der Migration
aufgerufen: E-Mail (Anmeldename), Anzeigename und Passwort zweimal eingeben.
Nach `Erster Administrator angelegt.` und dem Service-Start `/login` öffnen
und diese E-Mail mit dem gewählten Passwort verwenden.

Prüfen:

```bash
systemctl status neofab2.service --no-pager
curl --fail http://127.0.0.1:8080/health/ready
```

Erwartet: aktiver Dienst und `{"status":"ok"}`. Browser:
`http://<Container-IP>:8080`. Bei abweichendem Port den gewählten Wert verwenden.

Späteres Update als root:

Version 0.1.5 ergänzt [Plugin-Verwaltung im Backend und ein zweites Testplugin](../doku/plugin-development.md).
Keine zusätzliche Migration gegenüber 0.1.4. Unter **Plugins** erst `core_test`,
dann `management_test` zur Aktivierung vormerken. Anschließend startet der
**Proxmox-Admin den Container manuell neu**. Das Backend zeigt ausstehende
Änderungen an; es startet den Container nicht selbst. Das neue Testplugin
wird durch ein Update nicht automatisch aktiviert.

```bash
bash /opt/neofab2/script/upDateNeoFabService
```

Nur bei sauberem Checkout und Fast-Forward auf dem bestehenden Branch.
Vor Änderungen entstehen Sicherungen unter `/var/backups/neofab2/`.
Fehler nach Dienststopp lassen den Dienst angehalten. Keine automatische
Rückmigration oder Aktualisierung der systemd-Unit.

Nach dem Update einer bestehenden Installation ohne Administrator, als root:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 create-admin
```

Lokaler Notfall-Reset (Admin auswählen, Passwort verdeckt eingeben):

```bash
bash /opt/neofab2/script/resetAdminPassword
```

Ein deaktiviertes Admin-Konto bleibt dabei gesperrt; nur mit ausdrücklich
angegebenem `--reactivate` wieder aktivieren. Alle Sitzungen des Kontos enden.

[Zugang, HTTP-Testkonfiguration und Rollen](../doku/Core_Zugang.md).

Bei „Formularsitzung ungültig“ im HTTP-Testnetz den bestehenden Eintrag
`SESSION_COOKIE_SECURE = false` prüfen. Nach einer Änderung Dienst neu starten
und Loginseite frisch öffnen. Die Meldung betrifft die Sitzung, nicht die
Passwortlänge. [Konkrete Fehlerbehebung und erster Login](../doku/SETUP.md).

[Ausführliche Anleitung und Fehlerhilfe](../doku/SETUP.md) ·
[Betrieb und Wiederherstellung](../doku/operations.md)

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

Erwartet: Version 0.1.12, HTTP-/HTTPS-Hinweis und vorhandene Admin-E-Mails. Falls
Angaben fehlen: Konfigurationspfad, Installation und Datenbankschema mit `check`
prüfen; keine Secrets zur Fehlersuche veröffentlichen. Betriebsbefehle in der
Übersicht sind für **root im NeoFab2-Container**, nicht für den Proxmox-Host.
# Nachbesserung der Abschlussausgaben in 0.1.8

Die Datenbankprüfung und Bereitschaftsmeldung werden mit Trennlinien abgesetzt;
der abschließende Zusammenfassungsblock ist eingerahmt. Die Adressen stammen
aus `hostname -I` im Container, IPv6-Adressen werden in URL-Klammern ausgegeben.
Ist keine Adresse ermittelbar, erscheint ein Diagnosehinweis statt eines Platzhalters.

Beim ersten Update von 0.1.7 läuft noch das zuvor geladene Skript; dessen Ausgabe
enthält die neue Zusammenfassung daher noch nicht. Zur Prüfung nach dem Update
als **root im NeoFab2-Container** erneut ausführen:

```bash
bash /opt/neofab2/script/upDateNeoFabService
```

Bei unverändertem Repository-Stand wird kein weiteres Update ausgeführt; die
Zusammenfassung erscheint trotzdem. Standardport: `8080`, maßgeblich ist der
konfigurierte Port. Bei fehlender IP `ip -brief address` ausführen; externe
Erreichbarkeit und Reverse-Proxy-Adresse werden nicht automatisch geprüft.
