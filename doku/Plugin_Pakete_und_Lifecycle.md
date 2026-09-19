# Plugin-Pakete, Mindestzugriff und Deinstallation – Planung

Stand: 19.09.2026, Dokumentationsnachtrag zu NeoFab2 **0.1.11**.
Benutzerauftrag: Anforderungen untersuchen und einplanen, **noch nicht umsetzen**.
IDs: N01, U06, S01, S09, S10, X03, X05, X07.

## 1. Ergebnis und aktueller Stand

Ein Plugin als ZIP hochzuladen und dem System bereitzustellen ist grundsätzlich
möglich. Dafür braucht NeoFab2 einen Paketvertrag und einen geregelten
Installationsablauf; ein beliebiges Python-ZIP ist kein installierbares Plugin.
In 0.1.11 existieren weder ZIP-Import noch Deinstallation oder Mindestlevel-Auswahl.
Der feste Katalog `builtin_plugins()` lädt mitgelieferte Plugins, ihre Rollen
stehen im Code. Aktivieren/Deaktivieren wird erst beim Neustart wirksam.

Bereits heute liegen Plugins unter `src/neofab2/plugins/`, aber Code, Templates
und Ressourcen sind noch auf unterschiedliche Unterordner verteilt. Ziel ist
**ein vollständiges eigenes Verzeichnis pro Plugin**, einschließlich Ressourcen.

Der bisherige Ausschluss von Web-Code-Uploads gilt für die vorhandene
Implementierung weiter. Auf Benutzerwunsch wird ein kontrollierter ZIP-Import
als späterer Ausbau geplant. Kein Hot-Reload, kein Marktplatz und keine
Sicherheits-Sandbox: installierter Python-Code läuft mit Anwendungsrechten.

## 2. Eigene Verzeichnisse und Ressourcen

Geplante Quellstruktur für alle mitgelieferten Plugins, zunächst anhand der
drei technischen Testplugins umstellen:

```text
src/neofab2/plugins/
  checkdesign/
    plugin.toml                 # rein deklaratives Manifest
    __init__.py                 # vertraglicher Einstieg
    routes.py
    templates/checkdesign/
    static/
      css/
      icons/
      images/
    resources/
      documents/                # mitgelieferte PDF-/Hilfedokumente
    translations/
    migrations/                 # erst mit geklärtem Migrationsvertrag
    tests/
  core_test/
    ...
  management_test/
    ...
```

Plugin-eigene Icons, Bilder, Stylesheets und Dokumente liegen beim Plugin.
Gemeinsame Core-Icons, CSS und Layouts bleiben zentral und werden über den
öffentlichen UI-Vertrag verwendet; keine Kopie des gesamten Core-Designs.
Ressourcen werden über paketbezogene Pfade aufgelöst, unabhängig vom Arbeitsordner.
Identische Dateinamen verschiedener Plugins dürfen sich nicht überschreiben.

Mitgelieferte Ressourcen sind unveränderliche Paketbestandteile. Benutzeruploads,
erzeugte PDFs und andere Laufzeitdaten gehören **nicht** in das Codeverzeichnis.
Der bisherige kleine Dateidienst in `core_files` bleibt zunächst unverändert.
Eine spätere externe Dateiablage verwendet `DATA_DIR/plugins/<id>/`, mit
Metadaten-/Besitzerprüfung und gemeinsamem Backup-Vertrag.

Geplantes Installationsziel für mitgelieferte und separat installierte Plugins:
ein dedizierter Paketstamm, beispielsweise `/opt/neofab2-plugins/<id>/releases/<version>/`.
Diese Pfade sind Vorschläge, keine bereits vorhandenen Standardpfade. Ein
Installationsverzeichnis darf nur eine aktive Version je ID bereitstellen.
Es gibt keinen stillen Vorrang bei Kollisionen zwischen eingebauten und externen
Paketen. Die Umstellung des bisherigen Wheels und der festen Imports wird im
Installationspaket ausdrücklich umgesetzt und geprüft. Core-Updates dürfen
separat installierte Pakete weder überschreiben noch entfernen.

CSS, Bilder und PDFs werden nicht durch einen ungeschützten Webserver-Alias
freigegeben. Grundregel: Plugin aktiviert, Konto angemeldet und Mindestzugang
erfüllt; bei privaten Dokumenten zusätzlich Dokument-/Besitzerrecht. Öffentlich
zugängliche Ressourcen benötigen später eine ausdrückliche Deklaration. Keine
automatische öffentliche Freigabe aufgrund der Endung `.pdf` oder `.svg`.

## 3. ZIP-Vertrag und Bereitstellung

Geplanter Admin-Ablauf unter **Administration → Plugins**:

1. **Paket hochladen:** nur Administrator mit Installationsrecht und CSRF-Schutz.
   Archiv in einen nicht ausführbaren Staging-Bereich schreiben.
2. **Paket prüfen:** Manifest lesen, ohne Plugin-Code zu importieren. ID, Name,
   Plugin-Version, Core-/API-Kompatibilität, Einstieg, Ressourcen, deklarierte
   Rechte, vorgeschlagenes Mindestlevel, Abhängigkeiten und Migrationen prüfen.
3. **Prüfergebnis anzeigen:** Herkunft, Prüfsumme, Version, Konflikte,
   Abhängigkeiten, geplante Änderungen und erforderlicher Neustart. Fehlerhafte
   Pakete bleiben nicht installierbar. Ein Hash belegt Integrität, nicht Vertrauen.
4. **Installieren/Update ausdrücklich auslösen:** Backup, erneute Prüfung des
   aktuellen Zustands, exklusive Lifecycle-Sperre, Installation in ein neues
   Versionsverzeichnis und expliziter versionierter Migrationsschritt.
5. **Bereitstellen:** erst nach erfolgreicher Installation im Katalog auswählbar,
   zunächst deaktiviert. Aktivierung gesondert vormerken und alle Web-/Worker-
   Prozesse kontrolliert neu starten. Kein Import beim bloßen Upload.

Der Webprozess darf nicht beliebig laufenden Code überschreiben oder privilegierte
Shell-Befehle ausführen. Zunächst ist ein kontrollierter lokaler Installer durch
den Betriebsadministrator vorgesehen: UI nimmt Pakete an und zeigt ihren Status,
Installation erfolgt über einen später zu implementierenden CLI-Ablauf. Ein
vollständig aus der UI gesteuerter Installer benötigt danach einen eigenen
begrenzten Betriebsdienst. Dafür gibt es heute noch keine Befehle oder Freigabe.

Archivprüfung umfasst relative normalisierte Pfade, Pfadflucht, absolute Pfade,
Links, doppelte/bei Großschreibung kollidierende Namen, Dateienzahl sowie Limits
für Archivgröße, entpackte Größe und Kompressionsverhältnis. Keine ungeprüfte
Extraktion in das Zielverzeichnis. Konkrete Limits im Paketvertrag festlegen.
Keine Installations-Hooks oder automatische `pip`-/Netzwerkaufrufe aus dem ZIP;
zusätzliche Python-Abhängigkeiten zuerst als überprüfte Betriebsänderung planen.
Vor ausführbarer Installation müssen Herkunft und Vertrauensentscheidung
feststehen; Signatur-/Freigabeverfahren ist noch zu spezifizieren.

Migrationen dürfen keine Revisionen anderer Plugins ersetzen. Die aktuelle
zentrale Alembic-Kette kann nicht unverändert unabhängige ZIP-Migrationsketten
annehmen. Vor Importfreigabe einen modulbezogenen, versionierten Migrationsvertrag
und nachvollziehbares Installationsjournal festlegen. Bei Fehlern: ursprüngliches
Paket weiter verfügbar halten, Teilschritte kenntlich machen, keine Aktivierung.
Nach inkompatibler Schemaänderung genügt ein Code-Rollback nicht; Wiederherstellung
von Code, Daten und Konfiguration muss zusammenpassen. Core-Recovery muss auch
ohne Import eines defekten oder bereits entfernten Plugins möglich bleiben.

## 4. Mindestzugriffslevel in der Plugin-Übersicht

Geplant ist je Plugin ein Auswahlfeld **Mindestzugriff** mit diesen Werten:

| Auswahl | Zugang zum Plugin |
|---|---|
| Benutzer (`user`) | Benutzer, Mitarbeiter und Administratoren |
| Mitarbeiter (`staff`) | Mitarbeiter und Administratoren |
| Administrator (`admin`) | ausschließlich Administratoren |

Die Ordnung `user < staff < admin` gilt für diesen **Einstiegszugriff**.
Gäste und deaktivierte Konten erhalten niemals Zugang. Der Administrator kann
den niedrigsten Level tatsächlich festlegen; eine fest codierte `roles`-Liste
darf die Auswahl nicht unsichtbar wieder einschränken. Dafür wird der bisherige
`<id>.access`-Vertrag gezielt erweitert bzw. migriert, nicht nur die UI ergänzt.

Weitere Aktionen wie Freigabe, Verwaltung, Datenexport oder fremde Downloads
behalten ihre expliziten Einzelrechte. Effektiver Aktionszugriff bedeutet:
**Plugin aktiv + Mindestlevel erfüllt + Aktionsrecht + gegebenenfalls Besitzerprüfung**.
Ein niedrigeres Einstiegslevel erteilt kein `manage`, `approve` oder `read_all`.
Die neue Hierarchie erzeugt keinen Admin-Wildcard für sämtliche Plugin-Aktionen.
Ein höheres Einstiegslevel sperrt auch bisher berechtigte Einzelaktionen unterhalb
der Schwelle. Diese Schranke gilt in allen öffentlichen Dienstzugängen, nicht nur
im Menü oder Blueprint. Abhängigkeiten vererben keine Zugangsrechte.

Beispiel CheckDesign: Vorschlag bei Neuinstallation **Mitarbeiter**. Wählt der
Admin **Administrator**, verschwindet der Menüpunkt für Mitarbeiter und direkte
Aufrufe werden gesperrt. Wählt er **Benutzer**, dürfen auch normale Benutzer die
Vorschau öffnen. Die Core-Administration bleibt ausschließlich administrativ.

Speicherung nur durch Admin mit passendem Core-Recht; CSRF, erneute Rechteprüfung
in der Transaktion und Audit-Ereignis. Die Einstellung bleibt bei Neustart und
Paketupdate erhalten. Ein Paketupdate darf die gewählte Schwelle nicht absenken.
Geplantes Verhalten: Änderungen greifen ab der nächsten Anfrage in allen
Prozessen, ohne Neuanmeldung/Neustart; Aktivierung und Codewechsel behalten ihren
Neustartablauf. Bereits laufende Antworten können nicht zurückgenommen werden.
Eine globale veraltende Rechtekopie in der Registry muss dafür ersetzt werden.

Navigation, direkte GET/POST-Aufrufe, API, Dateien, Ressourcen und benutzerbezogene
Jobs verwenden dieselbe Schranke. Hintergrundaufgaben ohne Benutzer benötigen
einen expliziten Systemauftrag und Aktivierungsprüfung; keine erfundene Benutzerrolle.
Fehlende Einstellung: erklärter Manifest-Standard. Beschädigte Werte: Zugriff
sperren und administrativ reparierbar machen, nicht auf `user` zurückfallen.

Bestandsübernahme: `core_test` → Administrator, `management_test` → Benutzer,
`checkdesign` → Mitarbeiter. Andere, nicht hierarchische API-1-Rollenmengen
(beispielsweise nur `staff`, ohne `admin`) dürfen nicht automatisch erweitert
werden. Sie benötigen eine ausdrückliche Vertragsanpassung; bis dahin bleibt
die alte Prüfung aktiv und die Mindestlevel-Auswahl ist mit Erklärung gesperrt.
Version/API-Kompatibilität und eine nötige Datenmigration vor Umsetzung festlegen.

## 5. Deaktivierung, Deinstallation und Datenlöschung

Diese Vorgänge erhalten getrennte Aktionen und Zustände:

| Vorgang | Wirkung und Vorgabe |
|---|---|
| Deaktivieren | keine Seiten/Jobs nach geregeltem Neustart; Paket und Daten bleiben |
| Deinstallieren | ausführbares Paket entfernen; Plugin-Daten standardmäßig behalten |
| Plugin-Daten endgültig löschen | eigener destruktiver Ablauf mit Vorschau und gesonderter Bestätigung |

Geplanter Deinstallationsablauf: Abhängigkeiten und Datenreferenzen prüfen,
betroffene Jobs/Dateien/Migrationen auflisten, Backup anbieten und prüfen,
Deaktivierung aller Prozesse bestätigen, Jobs anhalten bzw. abschließen,
erst dann das installierte Paket entfernen. Benötigende installierte Plugins
einschließlich deaktivierter abhängiger Pakete blockieren zunächst die Entfernung;
keine automatische Kaskade. Historie, Plugin-ID, Schemazustand und Aufbewahrungsstatus
bleiben im Core-Installationsjournal erhalten.

Keine pauschalen SQL-Drops, kein rekursives Löschen eines geratenen Verzeichnisses
und kein automatisches Alembic-Downgrade beim Deinstallieren. Migrationen, die der
Core für seine Historie benötigt, dürfen nicht mit dem Code verschwinden. Bei
behaltenen Daten muss eine kompatible Neuinstallation dieselbe ID eindeutig
wiedererkennen. Modul-/Besitzerzuordnung, geteilte Tabellen, Fremdschlüssel,
Dateien und Jobs müssen über einen dokumentierten Ressourcenvertrag bekannt sein.

Eine spätere ausdrückliche Datenlöschung zeigt Anzahl und Umfang, Ausschlüsse,
fremde Referenzen und Backup-Hinweis. Core-Benutzer, fremde Plugin-Daten und
Backups werden nicht mitgelöscht. Fehlerfälle sind wiederaufnehmbar. Der technische
Ressourcenvertrag kann N06 unterstützen, ersetzt aber keine Freigabe zur jährlichen
oder produktiven Datenlöschung. Zurückrollen oder endgültiges Löschen ist heute
weder implementiert noch mit diesem Dokument beauftragt.

## 6. Umsetzungspakete und Nachweise

Die Pakete werden im [Core-Arbeitsplan](Core_Naechste_Schritte.md) eingeordnet.
Jedes benötigt einen späteren Umsetzungsauftrag; jetzt ist ausschließlich Planung
abgeschlossen. Zunächst nur synthetische Plugins und Daten verwenden.

| Paket | Umfang | Abnahmekriterien |
|---|---|---|
| P1 | Eigene Plugin-Ordner und Ressourcenvertrag | Drei Testplugins umziehen; IDs/URLs/Aktivierungen erhalten; Wheel/sdist enthalten Icons/Bilder/PDF; Ressourcen per Modul/Recht geschützt; Core startet ohne Plugins |
| P2 | Mindestlevel und Admin-Auswahl | Rollenmatrix mit allen drei Schwellen, bestehende Einzelrechte/Besitzerprüfung, Menü und Direktzugriffe, mehrere Prozesse, Widerruf und Bestandsmigration geprüft |
| P3 | Paketmanifest und Installations-/Migrationsjournal | Deklarative Prüfung ohne Codeimport, eindeutige IDs/Versionen, Core/API-/Abhängigkeitskonflikte, zentraler Recovery-Weg und modularer Migrationsplan nachgewiesen |
| P4 | ZIP-Annahme und kontrollierte Installation/Update | Schädliche Archivpfade/Links/Übergrößen abweisen; erneute Prüfung, Backup, konkurrierende Vorgänge, Abbruch und Wiederanlauf, keine Ausführung beim Upload; Core-Update erhält externe Plugins |
| P5 | Deinstallation mit Datenerhalt | Abhängigkeiten blockieren, alle Prozesse/Jobs ruhen, fremde Ressourcen geschützt, Daten bleiben, Neuinstallation und Restore geprüft; endgültige Datenlöschung weiterhin gesondert |

Offene Detailentscheidungen vor P3/P4: endgültige Paketpfade/Manifestfelder,
Vertrauens-/Signaturverfahren, API-Versionierung, Archivlimits, Python-Abhängigkeiten,
modulare Migrationen und Zuständigkeit des Installationsprozesses. Vor P5:
Aufbewahrungs-/Wiederinstallationsregeln und Ressourcennachweise je Plugin.
Diese offenen Details hindern die Dokumentation und Einplanung nicht.
