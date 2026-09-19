# NeoFab2

![NeoFab2](src/neofab2/static/branding/neofab2-logo.png)

**Version 0.1.9 — Startfähiges Core-Grundsystem.** Application Factory,
Konfiguration, explizite Migration, Startseite und Betriebsprüfung sind vorhanden.
Der aktuelle Arbeitsstand ergänzt Anmeldung, Benutzerverwaltung, Rollen,
Profil, widerrufbare Sitzungen, lokalen Admin-Passwort-Reset, öffentliche
Systemeinstellungen und eine persönliche helle/dunkle Darstellung.
Version 0.1.5 ergänzt Plugin-Aktivierung im Backend mit Neustarthinweis und
ein zweites synthetisches Testplugin zur Prüfung von Abhängigkeiten.

**Neu in 0.1.9:** Stammdaten-Einstieg als Button in den Systemeinstellungen,
keine Stammdaten-Links in Benutzerliste und Benutzerformularen sowie passende
Icons in allen Buttons. [Gestaltungsregeln](doku/UI_Gestaltungsregeln.md).

**Seit 0.1.8:** Deutliche Abschlussübersichten der Betriebsskripte, englische
übersetzbare Feldhilfen und eigene Backend-Formulare für Positionen, Studiengänge
und Kostenstellen als Benutzer-Auswahllisten. Keine Übernahme alter Freitextwerte.
[Nächste Core-Schritte](doku/Core_Naechste_Schritte.md).

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
- [Plugin-Umsetzungsplan für Codex: 3D-Druck, Viewer und PrintFleet](doku/Plugin_Umsetzungsplan.md)
- [Systemeinstellungen und Darstellung](doku/Core_Einstellungen.md)
- [Sprachwahl](doku/Core_Sprachen.md)
- [Benutzerformulare und Zusatzfelder](doku/Benutzerverwaltung.md)
- [Auswahllisten und Feldhilfen](doku/Core_Auswahllisten.md)
