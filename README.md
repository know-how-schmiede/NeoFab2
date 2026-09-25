# NeoFab2

Neu in 0.1.21: [Benutzerimport trotz einzelner Konflikte](doku/Core_Benutzerimport.md) nach ausdrücklicher Bestätigung. Konfliktkonten bleiben unverändert; keine neue Migration, Schema weiterhin `0013_user_deletion`.

Geplanter Ausbau (noch nicht umgesetzt): [Plugin-Pakete, eigene Ressourcenverzeichnisse,
Mindestzugriff und Deinstallation](doku/Plugin_Pakete_und_Lifecycle.md).

![NeoFab2](src/neofab2/static/branding/neofab2-logo.png)

**Version 0.1.21 — Startfähiges Core-Grundsystem.** Application Factory,
Konfiguration, explizite Migration, Startseite und Betriebsprüfung sind vorhanden.
Der aktuelle Arbeitsstand ergänzt Anmeldung, Benutzerverwaltung, Rollen,
Profil, widerrufbare Sitzungen, lokalen Admin-Passwort-Reset, öffentliche
Systemeinstellungen und eine persönliche helle/dunkle Darstellung.
Version 0.1.5 ergänzt Plugin-Aktivierung im Backend mit Neustarthinweis und
ein zweites synthetisches Testplugin zur Prüfung von Abhängigkeiten.

**Seit 0.1.15:** [Audit-Protokoll und Betriebsstatus](doku/Core_Audit_und_Betriebsstatus.md)
für Administratoren, strukturierte Ereignisse ohne Geheimnisse, Worker-Beobachtung
und explizite Audit-Aufbewahrung. Migration `0011_audit_status`.

**Seit 0.1.14:** SMTP-Formular erhält Eingaben bei Fehlern; regelmäßiger Versand
über eigenen systemd-Timer. Beim ersten Update anschließend die
[Service-Einrichtung](script/README.md) erneut ausführen.

**Seit 0.1.13:** [Registrierung, E-Mail-Aktivierung und Passwort-Reset](doku/Core_Registrierung_und_Reset.md).
Beide Selbstbedienungsverfahren starten ausgeschaltet. Admin-Freigabe mit
Domain-Regeln, einmalige befristete Codes, Sitzungswiderruf und Konto-E-Mails
über den vorhandenen Worker. Explizite Migration `0010_account_flows` erforderlich.

**Seit 0.1.12:** [SMTP und Versandaufträge](doku/Core_SMTP_und_Versand.md).
Admin-Einstellungen mit Testauftrag, persistente Warteschlange, begrenzte
Wiederholungen und CLI-Worker. Neue Migration `0009_mail_outbox`; Versand startet
deaktiviert; der Versandtimer oder ein manueller Worker-Aufruf verarbeitet Aufträge.

**Seit 0.1.11:** [CheckDesign 0.1.0](doku/CheckDesign.md), ein technisches
Core-Testplugin für Mitarbeiter und Administratoren. Galerie der gemeinsamen
Designelemente mit eigener Hell-/Dunkel-Vorschau ohne Änderung von Einstellungen.

**Seit 0.1.10:** Menüpunkt **Administration** für Benutzerverwaltung, Plugins
und Systemeinstellungen. Paket 0 ergänzt mehrere Plugin-Rechte, Besitzerprüfung
und einen minimalen Dateidienst mit synthetischem Upload-/Download-Test.
[Bedienung, Migration und Grenzen](doku/Core_Dateien_und_Rechte.md).

**Seit 0.1.9:** Stammdaten-Einstieg als Button in den Systemeinstellungen,
keine Stammdaten-Links in Benutzerliste und Benutzerformularen sowie passende
Icons in allen Buttons. [Gestaltungsregeln](doku/UI_Gestaltungsregeln.md).

**Seit 0.1.8:** Deutliche Abschlussübersichten der Betriebsskripte, englische
übersetzbare Feldhilfen und eigene Backend-Formulare für Positionen, Studiengänge
und Kostenstellen als Benutzer-Auswahllisten. Keine Übernahme alter Freitextwerte.
[Nächste Core-Schritte](doku/Core_Naechste_Schritte.md).

NeoFab2 ist eine modulare Webanwendung für Werkstätten und Makerspaces. Ein schlankes Core-System verwaltet Benutzer, Rechte und Systemfunktionen. Plugins ergänzen Workshops, 3D-Druck, Plotten, Transferdruck, CNC/Fräsen und Beschaffung.

Die Fachbereiche sind das Zielbild. Audit-Logs, weitere Plugin-Dienste,
Benutzerimport und Fachfunktionen folgen. Die vollständige Core-Abnahme steht aus.

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
