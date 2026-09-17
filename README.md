# NeoFab2

![NeoFab2](src/neofab2/static/branding/neofab2-logo.png)

**Version 0.1.4 — Startfähiges Core-Grundsystem.** Application Factory,
Konfiguration, explizite Migration, Startseite und Betriebsprüfung sind vorhanden.
Der aktuelle Arbeitsstand ergänzt Anmeldung, Benutzerverwaltung, Rollen,
Profil, widerrufbare Sitzungen und lokalen Admin-Passwort-Reset. Plugin-API 1,
Rechte und Navigation, Admin-Übersicht und ein standardmäßig deaktiviertes
synthetisches Testplugin sind vorhanden. Version 0.1.4 ergänzt öffentliche
Systemeinstellungen und eine persönliche helle/dunkle Darstellung.

NeoFab2 ist eine modulare Webanwendung für Werkstätten und Makerspaces. Ein schlankes Core-System verwaltet Benutzer, Rechte und Systemfunktionen. Plugins ergänzen Workshops, 3D-Druck, Plotten, Transferdruck, CNC/Fräsen und Beschaffung.

Die Fachbereiche sind das Zielbild. Selbstregistrierung, E-Mail-Aktivierung,
Self-Service-Passwort-Reset, weitere Plugin-Dienste, Benutzerimport und Fachfunktionen
folgen. Die vollständige Core-Abnahme steht aus.

Für einen neuen Debian-13-Container unter Proxmox stehen Installations-,
Service- und Update-Skripte bereit. Einstieg: [Installation](doku/SETUP.md).
Anmeldung und Passwortwechsel im Container durch den Nutzer bestätigt;
die vollständige LXC-/systemd-Abnahme steht noch aus.

- [Projektbeschreibung](doku/NeoFab2_Projektbeschreibung.md)
- [Architektur und Ordnerstruktur](doku/architecture.md)
- [Funktionsmatrix und Umsetzungsnachweis](doku/NeoFab2_Funktionsmatrix.md)
- [Installationsstand](doku/SETUP.md) und [Skriptübersicht](script/README.md)
- [Versionen und Commit-Texte](doku/Version_Timeline.md)
- [Logo und Gestaltung](assets/branding/README.md)
- [Betrieb, Sicherung und Wiederherstellung](doku/operations.md)
- [Benutzerzugang und Erstadministrator](doku/Core_Zugang.md)
- [Plugin-Vertrag und Testplugin aktivieren](doku/plugin-development.md)
- [Systemeinstellungen und Darstellung](doku/Core_Einstellungen.md)
