# NeoFab2 – Installation und Wartung (v0.1.1)

Als **root in einem neuen Debian-13-Container**, nicht auf dem Proxmox-Host:

```bash
apt-get update
apt-get install -y git ca-certificates
git clone https://github.com/know-how-schmiede/NeoFab2.git /root/NeoFab2-setup
bash /root/NeoFab2-setup/script/setupNeoFab
bash /opt/neofab2/script/setupNeoFabService
```

Voraussetzung: v0.1.1 wurde manuell auf den gewählten Remote-Branch gepusht.
Netzwerkzugang zu Debian, GitHub und PyPI erforderlich.

Die Installation fragt nach Bestätigung, Repository, Branch, Port und optionalem
Teststart. Vorgaben: Branch `main`, Port `8080`. Feste Pfade:
Code `/opt/neofab2`, Daten `/var/lib/neofab2`, Konfiguration `/etc/neofab2`,
Benutzer `neofab2`. Vorhandene Installationen werden nicht überschrieben.
Noch kein Admin-Zugang: Die Benutzerverwaltung folgt im nächsten Arbeitspaket.

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

`resetAdminPassword` folgt mit Benutzerverwaltung und sicherem CLI-Reset;
kein funktionsloses Ersatzskript.

[Ausführliche Anleitung und Fehlerhilfe](../doku/SETUP.md) ·
[Betrieb und Wiederherstellung](../doku/operations.md)
