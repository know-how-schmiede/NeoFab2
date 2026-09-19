# Nächste Schritte für das Core-System – Stand 0.1.13

Stand: 19.09.2026. Dies ist ein priorisierter Arbeitsplan, keine Fertigmeldung
und kein Auftrag für produktive Fachplugins. Grundlage sind die zehn
Abnahmekriterien in der [Projektbeschreibung](NeoFab2_Projektbeschreibung.md)
und der [Umsetzungsnachweis](NeoFab2_Funktionsmatrix.md).

Zusätzlich auf Benutzerauftrag in 0.1.11: [CheckDesign 0.1.0](CheckDesign.md)
als technische Designgalerie für Mitarbeiter/Admins. Die Galerie unterstützt die
spätere visuelle Abnahme; sie ersetzt diese nicht. Paket 1 wurde in 0.1.12
umgesetzt; Paket 2 folgt in 0.1.13. Paket 3 ist der nächste offene Schritt dieser Liste.

Planungsnachtrag: [Plugin-Pakete und Lifecycle](Plugin_Pakete_und_Lifecycle.md)
beschreibt eigene Plugin-Verzeichnisse, Mindestzugriff, ZIP-Bereitstellung und
Deinstallation. **Noch nicht implementieren**; Benutzerauftrag ist ausschließlich
Dokumentation. Die zusätzlichen Pakete
P1–P5 werden unten nach Abhängigkeiten eingeordnet, ohne Fachplugins freizugeben.

| Reihenfolge | Geplanter Umfang / Funktions-IDs | Erforderlicher Nachweis |
|---|---|---|
| 0 – umgesetzt in 0.1.10 | Plugin-Vertrag, Rollen und minimale Datei-Schnittstellen vorziehen (N01, U06, S10) | Mehrere Plugin-Rechte, Besitzerprüfung, Navigation, Aktivierung/Deaktivierung und sichere Upload-/Download-Zugriffe mit Testplugins automatisiert geprüft. `employee` entspricht `staff`. Minimaler Dateidienst: kleine Anhänge in SQLite, Testplugin nur TXT bis 256 KiB; Details und Grenzen: [Dateien und Rechte](Core_Dateien_und_Rechte.md). |
| 1 – umgesetzt in 0.1.12 | SMTP-Einstellungen, Testversand, persistente Versandaufträge und minimaler Worker/CLI (S05, S06, N05, N01) | Synthetische SMTP-Ausfälle, Wiederholung, Neustart, Status, begrenzte Versuche, Geheimnisschutz, parallele Worker und Plugin-Pause automatisiert geprüft. [Betrieb und Grenzen](Core_SMTP_und_Versand.md). Echte SMTP-/Postfach- und LXC-Prüfung bleiben offen; keine Zusage exakt einmaliger SMTP-Zustellung. |
| 2 – umgesetzt in 0.1.13 | Registrierung, E-Mail-Aktivierung und Self-Service-Passwort-Reset (U02–U04, S06) | Abschaltbare Registrierung/Reset, genaue Domain-Regeln, befristete Einmalcodes, Kontostatus, Sitzungswiderruf und Versand über vorhandenen Worker. [Bedienung, Prüfungen und Grenzen](Core_Registrierung_und_Reset.md). Produktionsregeln werden vor ausdrücklicher Freischaltung durch den Admin festgelegt; echte SMTP-/Browser-/LXC-Abnahme bleibt offen. |
| 3 | Audit-Logs und Betriebsstatus (S09, S12, N01) | Rechte, sicherheitsrelevante Ereignisse, Aufbewahrung und Fehlerdarstellung prüfen; keine Passwörter, Tokens oder SMTP-Secrets protokollieren. |
| 4 | Core-Oberfläche und Einstellungen vervollständigen (S01–S04, S08, U06/U07) | Infoseite, sichere Impressums-/Datenschutzinhalte, Zeitzonen einschließlich Sommerzeit, Einstellungsimport/-export und Rollenpflege prüfen. Deutsche/französische Kataloge und Plugin-Übersetzungsschnittstelle ergänzen; Englisch bleibt Ausgangssprache. |
| 5 | Technischen Datei- und Plugin-Vertrag vervollständigen (S10, N01, U05, N06 als Vertrag) | Modulzuordnung, Pfad-/Downloadrechte, Größenlimits, Plugin-Einstellungen und Dienstverträge ausschließlich mit Testplugins prüfen. Benutzerlöschung und spätere Plugin-Auswirkungen zuerst definieren. Noch keine jährliche Löschung produktiver Daten. |
| 6 | Benutzerimport mit Vorschau und Ergebnisbericht (U09, N04, U06) | Nur synthetische Daten: wiederholbarer Import ohne Duplikate, Rollen-/Statuszuordnung, E-Mail-Kollisionen und Hash-Kompatibilität. Altrollen und gelöschte Konten vor Umsetzung verbindlich behandeln. Keine Übernahme alter Tokens/Sitzungen. |
| 7 | Isolierte Betriebsprüfung und vollständige Core-Abnahme (X01–X07, alle Core-IDs) | Saubere Debian-/LXC-Installation, systemd, Update vom vorherigen Schema, Worker, Notfall-Reset sowie vollständige Sicherung/Wiederherstellung nachweisen. Browserprüfung in Hell/Dunkel und schmaler Ansicht; direkte HTTP-Rechteprüfungen. Alle zehn Abnahmekriterien einzeln mit Beleg abschließen. |

### Zusätzlich eingeplante Plugin-Pakete – nur Planung

| Einordnung | Paket / IDs | Umsetzung und erforderlicher Nachweis |
|---|---|---|
| Im Rahmen von Paket 5, vor dessen Abschluss | P1 – eigene Plugin-Verzeichnisse (N01, S10, X03/X05) | Code, Templates, Übersetzungen und eigene Ressourcen je Plugin bündeln; gemeinsame Core-Ressourcen weiterverwenden. Drei Testplugins, Paketierung, geschützte PDF-/Bild-/Icon-Zugriffe und unveränderte IDs/URLs prüfen. |
| Nach P1 und Audit-Grundlage aus Paket 3, im Rahmen von Paket 5 | P2 – Mindestzugriff (U06, S01, S09, N01) | Admin-Auswahl Benutzer/Mitarbeiter/Admin, persistent und pro Anfrage wirksam; Einstiegsrecht von Einzel-/Besitzerrechten trennen. Rollenmatrix, Direktzugriffe, Ressourcen, mehrere Prozesse und sichere Bestandsübernahme prüfen. |
| Nach P1/P2, zunächst technischer Ausbau mit Testpaketen | P3 – Paket-/Migrationsvertrag (N01, X03/X07) | Manifest, zentrale Installationshistorie, Kompatibilität, Versions-/ID-Konflikte, modularer Migrationsvertrag und Core-Recovery ohne Plugin-Code. Vertrauensmodell und endgültige Pfade festlegen. |
| Nach P3 und geprüfter Sicherung/Wiederherstellung; optionale Erweiterung nach Basis-Core-Abnahme | P4 – ZIP-Bereitstellung (N01, S09/S10, X03/X07) | Admin-Upload in Staging, codefreie Prüfung, kontrollierter lokaler Installer, gesonderte Aktivierung/Neustart. Archivangriffe, Abbruch, Parallelität, Update/Recovery prüfen. Noch kein Pflichtpunkt der ursprünglichen Core-Abnahme. |
| Nach P3/P4 und vollständigem Ressourcenvertrag; spätere Erweiterung | P5 – Deinstallation (N01, N06 als Vertrag, X03/X07) | Abhängigkeiten/Jobs/Prozesse prüfen, Paket entfernen, Daten standardmäßig erhalten; Wiederinstallation/Restore nachweisen. Endgültige Datenlöschung separat entscheiden und beauftragen. |

Alle P-Pakete sind **geplant**, nicht begonnen. Details und eindeutige
Prüfkriterien: [Plugin-Pakete und Lifecycle](Plugin_Pakete_und_Lifecycle.md).
P3 ist eine technische Voraussetzung für P4/P5, keine automatische Freigabe
zur Paketinstallation oder Erweiterung der zehn ursprünglichen Abnahmekriterien.

Paket 0 wurde in 0.1.10, Paket 1 in 0.1.12 und Paket 2 in 0.1.13 umgesetzt.
Als nächstes folgt Paket 3 mit Audit-Logs und Betriebsstatus.
Registrierungs- und Domain-Regeln sind vor einer betrieblichen Freischaltung
festzulegen; beide Kontoverfahren bleiben standardmäßig aus. Paket 5 ergänzt die weitergehenden
Dienstverträge; die übrigen Core-Abnahmekriterien werden nicht übersprungen. Es wird dabei kein neues Fachmodul
eingeführt. Dienste gehören nach `src/neofab2/services/`, Core-Administration
nach `src/neofab2/core/` und öffentliche Verträge nach `src/neofab2/plugin_api/`.
Neue Tabellen erhalten explizite versionierte Migrationen.

Jedes Paket ergänzt Tests, deutsche Betriebsanleitungen und den Umsetzungsnachweis
mit tatsächlichen Ergebnissen und offenen Punkten. Eine neue Versionsnummer wird
nur auf Auftrag vergeben. S11/PDF und weitergehende Präferenzen werden erst bei
konkretem Bedarf eingeplant; daraus entsteht keine stillschweigende Core-Abnahme.

Erst nach dokumentierter Core-Abnahme folgen die minimale `orders`-Basis und
`printing3d` als erstes Fach-/Referenzplugin. Den STL-Viewer dabei als gemeinsame
Komponente herauslösen; kein eigener Viewer-Eintrag in der Plugin-Verwaltung.
PrintFleet folgt nach dem MVP, Workshops später. Details und Prüfkriterien:
[Plugin-Umsetzungsplan](Plugin_Umsetzungsplan.md). Produktivmigration, Abschaltung oder Löschung des alten NeoFab bleiben
gesonderte Aufträge. Neue Modulvorschläge werden vor ihrer Umsetzung entschieden.
