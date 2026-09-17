# NeoFab2 – Installation und Wartung (v0.1.2)

Als **root in einem neuen Debian-13-Container**, nicht auf dem Proxmox-Host:

```bash
apt-get update
apt-get install -y git ca-certificates
git clone https://github.com/know-how-schmiede/NeoFab2.git /root/NeoFab2-setup
bash /root/NeoFab2-setup/script/setupNeoFab
bash /opt/neofab2/script/setupNeoFabService
```

Voraussetzung: v0.1.2 wurde manuell auf den gewählten Remote-Branch gepusht.
Netzwerkzugang zu Debian, GitHub und PyPI erforderlich.

Die Installation fragt nach Bestätigung, Repository, Branch, Port, HTTPS-Nutzung,
Erstadministrator und optionalem Teststart. Vorgaben: Branch `main`, Port `8080`,
HTTPS `j`. Feste Pfade:
Code `/opt/neofab2`, Daten `/var/lib/neofab2`, Konfiguration `/etc/neofab2`,
Benutzer `neofab2`. Vorhandene Installationen werden nicht überschrieben.
Admin-E-Mail und Anzeigename eingeben, Passwort verdeckt wiederholen (15–128
Zeichen). Keine Standardzugangsdaten. Nur für ein isoliertes HTTP-Testnetz bei
HTTPS `n` wählen; sonst wird eine HTTPS-Verbindung für die Login-Cookies benötigt.

Der optionale Test startet aus dem Installationsverzeichnis. Ein Fehler dabei
wird separat gemeldet; die erfolgreiche Basisinstallation bleibt bestehen.
Mit `n` wird der Test übersprungen, Strg+C beendet ihn regulär.

Prüfen:

```bash
systemctl status neofab2.service --no-pager
curl --fail http://127.0.0.1:8080/health/ready
```

Erwartet: aktiver Dienst und `{"status":"ok"}`. Browser:
`http://<Container-IP>:8080`. Bei abweichendem Port den gewählten Wert verwenden.

Späteres Update als root:

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

[Ausführliche Anleitung und Fehlerhilfe](../doku/SETUP.md) ·
[Betrieb und Wiederherstellung](../doku/operations.md)
