# Plugin-Umsetzungsplan für Codex

Stand: 18.09.2026, Dokumentationsnachtrag zum Arbeitsstand 0.1.7.
Grundlage: vom Benutzer eingefügtes Planungsgespräch zu 3D-Druck, PrintFleet,
STL-Viewer und gemeinsamen Komponenten. Der ursprüngliche
[Freigabelink](https://chatgpt.com/share/6aad92bf-f514-83eb-9084-900bfed0fd2d)
war nicht abrufbar; maßgeblich ist der anschließend bereitgestellte Text.

Diese Spezifikation konkretisiert die [Projektbeschreibung](NeoFab2_Projektbeschreibung.md).
Sie ersetzt deren frühere Priorität „Workshops zuerst“. Sie ist ein Umsetzungsplan,
kein Nachweis implementierter Fachfunktionen. Die vollständige Core-Abnahme bleibt
Voraussetzung für produktive Fachplugins. Version, Anwendung und Schema werden
durch diesen Dokumentationsauftrag nicht geändert.

## 1. Festgelegte Richtung und Abgrenzung

- Erstes Fach- und Referenzplugin: **3D-Druck**, technische Kennung **`printing3d`**.
  Die Gesprächsnamen `3d_printing` und `printing` waren Alternativen; im Repository
  bleibt die bereits festgelegte Kennung einheitlich. Workshops bleiben geplant,
  ihre Umsetzung folgt später; die weitere Reihenfolge ist offen.
- Kleine erste Ausbaustufe: Auftrag erfassen → bearbeiten → Kosten ermitteln →
  Freigabe und Status nachvollziehen. Noch keine PrintFleet-API im MVP.
- Slicing erfolgt außerhalb von NeoFab2. NeoFab2 verarbeitet bereitgestellten
  G-Code, betreibt keinen eingebauten Slicer und steuert keine Drucker direkt.
- Der konkrete Drucker wird später in **PrintFleet** ausgewählt und betrieben.
  NeoFab2 übergibt freigegebene Aufträge und liest deren Ausführungsstatus zurück.
- Datei-Upload, Dateiverwaltung und STL-/3D-Vorschau sind technische Infrastruktur,
  keine einzeln aktivierbaren Fachplugins. Die Plugin-Verwaltung zeigt fachliche
  Bereiche wie 3D-Druck oder Plotten, keine Liste technischer Viewer.
- React/TSX im Gespräch war ein Strukturbeispiel, keine Entscheidung für einen
  Frontend-Wechsel. Der bestehende Flask-/Jinja-Aufbau bleibt die Grundlage.
- Laser und Scan sind lediglich spätere Modulideen, keine freigegebenen Plugins.
  „Thermotransfer“ wird dem geplanten `transfer_printing` zugeordnet; das konkrete
  Verfahren bleibt vor Umsetzung zu entscheiden.

## 2. Zuständigkeiten und geplante Ablage

| Bereich | Zuständigkeit | Grenze |
|---|---|---|
| `src/neofab2/core/` | Konten, Authentifizierung, Rollen, zentrale Rechteprüfung, Plugin-Verwaltung | Keine Druckparameter, Druckermodelle oder Fachplugin-Importe |
| `src/neofab2/services/` | Technische Dateiablage, Upload-/Downloadmechanik, Größenlimits, Modulzuordnung; bestehender Plan für Versand und Aufgaben | Das Fachmodul entscheidet über den fachlichen Zugriff und liefert Inhalte |
| `src/neofab2/plugin_api/` | Veröffentlichte Verträge für Navigation, Rechte und technische Dienste | Plugins greifen nicht beliebig auf interne Core-Implementierungen zu |
| `src/neofab2/static/shared/` und `templates/shared/` | Geplante wiederverwendbare UI-Module `FileUpload`, `FilePreview`, `Model3DViewer` | Interne Komponenten; konkrete Dateinamen beim Arbeitspaket festlegen, kein React-Zwang |
| `src/neofab2/plugins/orders/` | Minimale gemeinsame Auftragsbasis: Kennung, Besitzer, grundlegender Lebenszyklus und gemeinsame Kommunikation | Keine Drucker-, Material- oder Slicerlogik; nur den für den ersten Ablauf benötigten Teil aufbauen |
| `src/neofab2/plugins/printing3d/` | Modelle, Druckparameter/-typ, G-Code-Metadaten, Kalkulation, Freigabe und Druckstatus; später PrintFleet-Adapter | Deklarierte Abhängigkeit von `orders`, keine Abhängigkeit von Workshops/Plotten |

`orders` bleibt eine gemeinsame fachliche Basis außerhalb des Cores. Vor bzw.
zusammen mit `printing3d` wird nach der Core-Abnahme nur ihr minimal benötigter
Umfang umgesetzt. Die gesamte O01–O14-Liste ist keine Voraussetzung für den MVP.
Gemeinsamkeiten werden mit weiteren Plugins überprüft, nicht vorab vollständig
abstrahiert. Ein technischer G-Code-Parser bleibt zunächst bei `printing3d`;
erst nach belegtem Wiederverwendungsbedarf wird er als gemeinsamer Dienst
herausgelöst. Material-/Kostenregeln bleiben in jedem Fall Fachlogik.

## 3. Rollen und Rechte vor dem ersten Fachplugin

Das Gespräch bezeichnet die Mitarbeiterrolle als `employee`. Der vorhandene
Core verwendet die gespeicherten Werte `user`, `staff`, `admin`. **`employee`
entspricht für diese Planung `staff`**; es entsteht weder eine vierte Rolle noch
eine automatische Umbenennung. Eine spätere Änderung des gespeicherten Wertes
benötigt einen eigenen Auftrag, explizite Migration und Kompatibilitätsprüfung.

| Rolle | Geplanter Zugriff im 3D-Druck-Plugin |
|---|---|
| `user` | Auftrag anlegen, eigene Aufträge und deren freigegebene Informationen/Dateien ansehen; keine fremden Aufträge, Kalkulationsfreigabe oder Plugin-Konfiguration |
| `staff` / fachlich `employee` | Aufträge prüfen und bearbeiten, Druckparameter/-typ festlegen, G-Code zuordnen, kalkulieren und freigeben |
| `admin` | Explizit dieselben fachlichen Rechte sowie Plugin-Konfiguration und administrative Funktionen |

Geplante Rechte beispielsweise `printing3d.create`, `printing3d.view_own`,
`printing3d.manage`, `printing3d.approve`, `printing3d.configure` sind **noch kein
implementierter Fachplugin-Vertrag**. Seit 0.1.10 unterstützt API 1 neben
`<kennung>.access` mehrere Rechte und Besitzerprüfung, nachgewiesen mit
Testplugins ([Dateien und Rechte](Core_Dateien_und_Rechte.md)). Die konkreten
3D-Druck-Rechte bleiben geplant. Die Rechte werden ausdrücklich zugeordnet;
ein Admin erhält keinen pauschalen Zugriff auf beliebige fremde Plugins.
Navigation, Routen, Formularaktionen, Datei-Downloads und Vorschauen müssen
dieselbe serverseitige Prüfung verwenden. Die genaue Änderbarkeit eigener
Aufträge nach Einreichung wird vor dem MVP festgelegt.

## 4. Fachlicher Ablauf und Ausbaustufen

| Schritt | Geplantes Verhalten | Ausbaustufe |
|---|---|---|
| 1 | Benutzer erfasst Auftrag und lädt Modell bzw. benötigte Auftragsdaten hoch; Besitzerzuordnung bleibt überprüfbar | MVP |
| 2 | Mitarbeiter/Admin prüft den Auftrag und legt Druckparameter sowie Druckertyp fest; noch keine Auswahl eines konkreten PrintFleet-Druckers | MVP |
| 3 | G-Code wird extern erzeugt und dem Auftrag durch einen Berechtigten zugeordnet | MVP, kein integriertes Slicing |
| 4 | NeoFab2 analysiert Druckzeit und Materialmenge und berechnet Kosten anhand festgelegter Regeln | MVP; fehlende/unbekannte Metadaten sichtbar behandeln |
| 5 | Mitarbeiter oder entsprechend berechtigter Admin gibt den geprüften Auftrag frei | MVP |
| 6 | Berechtigter übergibt den freigegebenen Auftrag an PrintFleet; dort konkrete Druckerauswahl und Drucksteuerung | Anschlussausbau nach MVP |
| 7 | PrintFleet-Ausführungsstatus wird lesend zurückgeführt, etwa wartend/druckend/fertig/Fehler | Anschlussausbau nach MVP |

Auftragsstatus, Freigabe und Druckausführungsstatus sind getrennte Sachverhalte.
Ohne PrintFleet muss der MVP seinen Status lokal nachvollziehbar führen; dieser
darf keinen live gelesenen Druckerzustand vortäuschen. Konkrete Statuscodes und
Übergänge einschließlich Abbruch, Fehler und erneuter Freigabe sind vor der
Implementierung festzulegen. Zu prüfen ist insbesondere, wie Änderungen an
Modell, G-Code oder Kosten eine vorhandene Freigabe ungültig machen.

Kalkulationsformel, Einheiten, Rundung, freigegebene Slicerformate, Material-/
Druckertyp-Stammdaten und zulässige manuelle Korrekturen werden vor dem MVP
konkretisiert. Unlesbare Metadaten dürfen nicht stillschweigend als null Kosten
oder null Druckzeit gelten. Bestehende NeoFab-Logik nur nach Sichtung und mit
synthetischen Referenzfällen übernehmen; keine produktiven Dateien importieren.

## 5. Datei- und Viewer-Komponenten

Den vorhandenen STL-Viewer im alten NeoFab lesend sichten und für NeoFab2 in
eine wiederverwendbare `Model3DViewer`-Komponente herauslösen. Den Altcode nicht
im alten Repository umbauen. Die Komponente erhält eine durch den Dateidienst
autorisierte Datei; sie kennt keine Auftragsmodelle oder Druckkosten.

`FilePreview` dient als kleiner Auswahlpunkt für verfügbare Vorschauen. Geplanter
Einstieg ist STL. Die folgende Zuordnung ist eine spätere Erweiterungsrichtung,
keine bereits zugesagte Unterstützung aller Formate:

| Dateityp | Geplanter Vorschautyp / Status |
|---|---|
| `.stl` | `Model3DViewer`, für den ersten 3D-Druck-MVP vorzusehen |
| `.3mf`, `.obj` | 3D-Vorschau später nach eigener Format-/Parserprüfung |
| `.png`, `.jpg` | Gemeinsame Bildvorschau bei Bedarf |
| `.pdf` | PDF-Vorschau bei Bedarf |
| `.gcode` | Vorschau später; Metadatenanalyse im MVP ist keine grafische G-Code-Vorschau |

Die Dateiendung allein erteilt keine Freigabe: Dateityp, Größe und Zugriff
serverseitig prüfen. Nicht unterstützte oder beschädigte Dateien liefern eine
verständliche Ersatzanzeige, keine ungeprüfte Ausführung. Ein berechtigter
Download kann verfügbar bleiben, sofern die Datei selbst zulässig ist.
Datei-URL und Vorschau dürfen Besitzer-/Plugin-Rechte nicht umgehen.

## 6. PrintFleet: geplanter Anschluss, noch kein API-Vertrag

Die Integration liegt beim 3D-Druck-Plugin. In diesem Dokument werden keine
API-Endpunkte, Authentifizierungsverfahren oder Fähigkeiten von PrintFleet
behauptet. Vor dem Anschluss genaue Produkt-/API-Version, Dokumentation,
Authentifizierung und eine isolierte Testumgebung festlegen.

Zu spezifizieren und anschließend mit einem Testadapter zu prüfen:

- Übergabeinhalt: freigegebener Auftrag, passende G-Code-Datei, technische
  Metadaten und stabile Zuordnung zwischen NeoFab2-Auftrag und externem Job.
- Wiederholungen/Timeouts dürfen nicht unbemerkt doppelte Druckaufträge erzeugen;
  Idempotenz oder Abgleichverfahren anhand der tatsächlichen API festlegen.
- Statusmapping, Aktualisierungsverfahren und Verhalten bei unbekanntem,
  veraltetem oder fehlendem Status. Kommunikationsausfall von Druckfehler trennen.
- Druckerauswahl, Start/Stop und Maschinensteuerung verbleiben in PrintFleet;
  der Rückkanal aktualisiert den Status, nicht beliebige Auftragsdaten.
- Konfiguration nur mit Admin-Recht; Zugangsdaten nicht im Browser oder Log.
  Deaktivierung nach kontrolliertem Neustart sperrt Übergaben und Statusaufgaben,
  erhält aber Aufträge, Dateien und externe Zuordnungen.

## 7. Reihenfolge und Abnahmekriterien für Codex

1. Core-Vertrag und Rechte vervollständigen: Registry, Aktivierungs-/
   Abhängigkeitsprüfung, Navigation und mehrere Plugin-Rechte mit Testplugins.
2. Minimalen technischen Datei-/Upload-Vertrag mit Testplugin prüfen. Alle
   übrigen Core-Abnahmekriterien bleiben bestehen, einschließlich des geplanten
   Versanddienstes für Aktivierung und Passwort-Reset. „Kein großes Framework
   vorab“ hebt diese Core-Anforderungen nicht auf.
3. Vollständige Core-Abnahme dokumentieren. Anschließend minimale `orders`-Basis
   und benötigte gemeinsame UI-Komponenten vorbereiten. STL-Viewer spätestens
   beim Aufbau von `printing3d` gemeinsam herauslösen; kein vollständiger
   PDF-/G-Code-/QR-Code-Komponentenbaukasten als Vorbedingung.
4. `printing3d`-MVP ohne PrintFleet umsetzen und separat abnehmen.
5. PrintFleet-Anschluss nach eigener Schnittstellenklärung ergänzen.
6. Erfahrungen aus dem Referenzplugin für weitere Plugins und belegte gemeinsame
   Komponenten verwenden. Workshops bleiben im Plan; Laser/Scan erst nach Entscheidung.

| Nachweis | Funktions-IDs / Prüfumfang |
|---|---|
| Rechte | U06, N01: user kann keinen fremden Auftrag/Download lesen und nicht freigeben; staff kann Fachaktionen, aber keine Admin-Konfiguration; direkte HTTP-Aufrufe und CSRF prüfen |
| Dateien/Vorschau | S10, D01/D02: synthetische gültige, beschädigte und zu große STL-Dateien, verweigerte Zugriffe, Ersatzanzeige und Start ohne aktives Fachplugin |
| MVP | O01/O10, D03–D07: vollständiger lokaler Ablauf, nachvollziehbare Kalkulation, fehlende Metadaten, Freigabe und ungültige Statuswechsel; keine externe Drucksteuerung |
| Lebenszyklus | N01, X07: explizite Migration, Upgrade mit Datenerhalt, deaktivierte Routen/Aufgaben, fehlende Abhängigkeiten, Sicherung/Wiederherstellung |
| Integration | N09: autorisierte Übergabe, Wiederholung, Verbindungsfehler, Statuszuordnung und Deaktivierung zunächst mit synthetischem Testadapter |

Vor jedem Paket die [Funktionsmatrix](NeoFab2_Funktionsmatrix.md) fortführen.
Englische Ausgangstexte/-schlüssel und Übersetzungs-Fallback beibehalten.
Nur synthetische Testdaten verwenden. Geplante Pfade, Rechte, Formate und
Schnittstellen erst nach Implementierung und Nachweis als verfügbar melden.
