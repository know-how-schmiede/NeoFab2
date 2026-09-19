# Nächste Schritte für das Core-System – Stand 0.1.10

Stand: 19.09.2026. Dies ist ein priorisierter Arbeitsplan, keine Fertigmeldung
und kein Auftrag für produktive Fachplugins. Grundlage sind die zehn
Abnahmekriterien in der [Projektbeschreibung](NeoFab2_Projektbeschreibung.md)
und der [Umsetzungsnachweis](NeoFab2_Funktionsmatrix.md).

| Reihenfolge | Geplanter Umfang / Funktions-IDs | Erforderlicher Nachweis |
|---|---|---|
| 0 – umgesetzt in 0.1.10 | Plugin-Vertrag, Rollen und minimale Datei-Schnittstellen vorziehen (N01, U06, S10) | Mehrere Plugin-Rechte, Besitzerprüfung, Navigation, Aktivierung/Deaktivierung und sichere Upload-/Download-Zugriffe mit Testplugins automatisiert geprüft. `employee` entspricht `staff`. Minimaler Dateidienst: kleine Anhänge in SQLite, Testplugin nur TXT bis 256 KiB; Details und Grenzen: [Dateien und Rechte](Core_Dateien_und_Rechte.md). |
| 1 | SMTP-Einstellungen, Testversand, persistente Versandaufträge und minimaler Worker/CLI (S05, S06, N05, N01) | Synthetischer SMTP-Ausfall verliert keine Aufträge; Wiederholung, Neustart, Zustellstatus, begrenzte Versuche und deaktivierte Plugin-Aufgaben prüfen. Geheimnisse nicht ausgeben. Keine Zusage exakt einmaliger SMTP-Zustellung. |
| 2 | Registrierung, E-Mail-Aktivierung und Self-Service-Passwort-Reset (U02–U04, S06) | Registrierung abschaltbar, Domain-Regeln, abgelaufene/verbrauchte Tokens, Kontostatus und Sitzungswiderruf prüfen. Registrierungsregeln vor Freischaltung festlegen. |
| 3 | Audit-Logs und Betriebsstatus (S09, S12, N01) | Rechte, sicherheitsrelevante Ereignisse, Aufbewahrung und Fehlerdarstellung prüfen; keine Passwörter, Tokens oder SMTP-Secrets protokollieren. |
| 4 | Core-Oberfläche und Einstellungen vervollständigen (S01–S04, S08, U06/U07) | Infoseite, sichere Impressums-/Datenschutzinhalte, Zeitzonen einschließlich Sommerzeit, Einstellungsimport/-export und Rollenpflege prüfen. Deutsche/französische Kataloge und Plugin-Übersetzungsschnittstelle ergänzen; Englisch bleibt Ausgangssprache. |
| 5 | Technischen Datei- und Plugin-Vertrag vervollständigen (S10, N01, U05, N06 als Vertrag) | Modulzuordnung, Pfad-/Downloadrechte, Größenlimits, Plugin-Einstellungen und Dienstverträge ausschließlich mit Testplugins prüfen. Benutzerlöschung und spätere Plugin-Auswirkungen zuerst definieren. Noch keine jährliche Löschung produktiver Daten. |
| 6 | Benutzerimport mit Vorschau und Ergebnisbericht (U09, N04, U06) | Nur synthetische Daten: wiederholbarer Import ohne Duplikate, Rollen-/Statuszuordnung, E-Mail-Kollisionen und Hash-Kompatibilität. Altrollen und gelöschte Konten vor Umsetzung verbindlich behandeln. Keine Übernahme alter Tokens/Sitzungen. |
| 7 | Isolierte Betriebsprüfung und vollständige Core-Abnahme (X01–X07, alle Core-IDs) | Saubere Debian-/LXC-Installation, systemd, Update vom vorherigen Schema, Worker, Notfall-Reset sowie vollständige Sicherung/Wiederherstellung nachweisen. Browserprüfung in Hell/Dunkel und schmaler Ansicht; direkte HTTP-Rechteprüfungen. Alle zehn Abnahmekriterien einzeln mit Beleg abschließen. |

Paket 0 wurde in 0.1.10 umgesetzt. Als nächstes folgt Paket 1 mit SMTP,
Testversand, persistenten Versandaufträgen und minimalem Worker/CLI.
Der Versanddienst bleibt Voraussetzung
für die offenen Aktivierungs- und Reset-Verfahren. Paket 5 ergänzt die weitergehenden
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
