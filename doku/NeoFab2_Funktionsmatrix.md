# NeoFab → NeoFab2: Funktionsbestand und Umsetzungszuordnung

Stand: 17.09.2026. Referenz: NeoFab 0.9.62, Git-Stand `2673096675db2ccfb824abca0946607e87416819`.

Diese Matrix ergänzt die [Projektbeschreibung](NeoFab2_Projektbeschreibung.md) und den [Projektstart für Codex](NeoFab2_Projektstart_Codex.md). Sie inventarisiert die im Quellcode und in der Dokumentation erkennbaren Funktionsbereiche. Sie ist kein Nachweis einer Laufzeitprüfung und keine Zusage, sämtliche Bestandsfunktionen bereits in der ersten NeoFab2-Version zu liefern.

## Verwendung durch Codex

1. Vor einem Arbeitspaket die betroffenen IDs auswählen und die genannten Quellstellen im alten Repository lesen. Die Quellverweise unten beziehen sich auf NeoFab, nicht auf noch vorhandene Dateien in NeoFab2.
2. Die Zuordnung als Zielarchitektur verwenden. Mit **Vorschlag** gekennzeichnete Modulgrenzen vor ihrer Implementierung dokumentiert entscheiden; die bestehende Core-Abgrenzung nicht stillschweigend erweitern.
3. Vor Implementierung den Erstumfang festlegen. Nicht eingeplante Bestandsfunktionen ausdrücklich als zurückgestellt erfassen, statt sie unbemerkt wegzulassen.
4. Im Umsetzungsnachweis am Dateiende je bearbeiteter ID Zielpfad, Status und tatsächliche Prüfergebnisse ergänzen. Die stabilen IDs auch in Arbeitspaketen und Tests verwenden.
5. Fertig bedeutet implementiert und gegen die relevanten Prüfkriterien geprüft. Reine Datei- oder Menüexistenz genügt nicht. Ein Abweichungsentscheid enthält Grund und Auswirkungen.
6. Zuerst nur die Core-Ausbaustufe aus der Projektbeschreibung umsetzen. Diese Bestandsliste ist kein Auftrag, alle Plugins gleichzeitig zu bauen.

**Initialstatus:** Alle NeoFab2-Zuordnungen in dieser Datei sind geplant, nicht implementiert oder abgenommen. Spätere Statusänderungen stehen im Umsetzungsnachweis. Neue Funktionen sind getrennt vom NeoFab-Bestand aufgeführt.

## Zielbereiche und Abhängigkeiten

| Ziel | Verantwortung und Abhängigkeit |
|---|---|
| Core | Benutzer, Rechte, Systemkonfiguration, gemeinsame Oberfläche und Plugin-Lifecycle; lauffähig ohne Fachplugins |
| Core-Dienst | Technischer Dienst innerhalb der Core-Ausbaustufe, keine eigenständige Fachanwendung; zum Beispiel Versand, Dateien, Zeit, Logs |
| Plugin `orders` | Gemeinsame Auftragsbasis; benötigt Core |
| Plugins `printing3d`, `plotting`, `procurement`, `milling`, `transfer_printing` | Eigenständige Fachplugins; benötigen Core und `orders`, keine pauschalen gegenseitigen Abhängigkeiten |
| Plugin `workshops` | Veranstaltungen und Teilnehmer; benötigt Core, nicht `orders` |
| Plugin `order_appointments` – Vorschlag | Auftragsbezogene Terminabstimmung; benötigt `orders`, unabhängig von Workshops |
| Plugin `learning` – Vorschlag | Lernvideos, Playlists und Unterlagen; benötigt Core, nicht Workshops |
| Plugin `announcements` – Vorschlag | Redaktionelle Mitteilungen und deren Gelesen-Status; benötigt Core; technische Systemmeldungen bleiben im Core |
| Betrieb/Entwicklung | Installationsskripte, Dokumentation, Versionspflege und Prüfwerkzeuge |

Ein gemeinsamer technischer Dienst besitzt keine fachlichen Rechteentscheidungen: zum Beispiel entscheidet das jeweilige Plugin, wer einen Anhang lesen darf und an wen eine Status-E-Mail geht. Der Core darf keine aktiven Fertigungsplugins voraussetzen.

## A. Benutzer und Zugang

| ID | Aktuell in NeoFab | Ziel in NeoFab2 | Quellbezug | Prüfkriterium / Umsetzungshinweis |
|---|---|---|---|---|
| U01 | Anmeldung, Abmeldung und Passwort-Hashing | Core | APP: `login`, `logout`; MODELS: `User` | Gültige und ungültige Anmeldung prüfen; keine Klartextpasswörter speichern |
| U02 | Registrierung mit konfigurierbarer Domain-Beschränkung | Core | APP: `register`; CONFIG | Zulässige und abgelehnte Domains sowie deaktivierte Registrierung prüfen |
| U03 | Optionale E-Mail-Aktivierung und Aktivierungslinks | Core + Versanddienst | APP: `activate_user`, `create_user_activation_token`; MODELS: `UserActivationToken` | Abgelaufene und verbrauchte Tokens zurückweisen; Kontostatus beachten |
| U04 | Passwort vergessen / Self-Service-Reset | Core + Versanddienst | APP: `password_reset_request`, `password_reset_confirm`; MODELS: `UserPasswordResetToken` | Tokenablauf und Einmalnutzung prüfen; vorhandene Sitzungen nach definierter Regel behandeln |
| U05 | Benutzer anlegen, bearbeiten, aktivieren, deaktivieren und löschen | Core | ADMIN: `admin_user_*`; MODELS: `User` | Zugriff nur mit Recht; deaktivierte Konten bleiben gesperrt; Löschwirkung auf spätere Plugins definieren |
| U06 | Rollen und rollenbasierter Zugriff | Core; fachliche Rechte durch Plugins | AUTH: `roles_required`; MODELS: `User.role` | Direkte HTTP-Zugriffe ebenso schützen wie Navigation; alte Rollen explizit zuordnen |
| U07 | Profilfelder, Sprache und helles/dunkles Erscheinungsbild | Core | APP: `profile`; MODELS: `User`; UI | Speichern und erneutes Laden prüfen; fachliche Profilfelder als Erweiterungen abgrenzen |
| U08 | Inaktivitätszeitlimit und Sitzungsverhalten | Core | AUTH: `register_session_timeout` | Timeout beendet Zugriff zuverlässig; Konfiguration und Sonderfälle prüfen |
| U09 | Benutzerimport und -export im Admin-Bereich | Core; Altimport gesonderter Ablauf | ADMIN: `admin_user_import`, `admin_user_export` | Format und Zugriffsrechte dokumentieren; vorhandener Export ist nicht ungeprüft ein vollständiger Migrationsvertrag |
| U10 | E-Mail-Empfängerfavoriten pro Benutzer | Core-Dienst für persönliche Empfängerpräferenzen | MODELS: `UserEmailFavorite`; APP: `save_user_email_favorites`, `profile` | Nur eigene Favoriten verwalten; Versandberechtigung entsteht nicht durch einen Favoriten |
| U11 | Benutzerbezogene Abholzeiten und Kontaktinformationen | Plugin `orders`, an Benutzer gebundene Einstellungen | MODELS: `User.pickup_*`; NOTIFY: `_append_completion_pickup_info` | In fachlichen Abholinformationen verfügbar, keine Pflichtfelder des schlanken Cores |

## B. Oberfläche, System und technische Dienste

| ID | Aktuell in NeoFab | Ziel in NeoFab2 | Quellbezug | Prüfkriterium / Umsetzungshinweis |
|---|---|---|---|---|
| S01 | Startseite, Navigation, Admin-Einstieg und Infoseite | Core; Plugin-Beiträge | APP: `landing`, `info`; UI: `base.html`; ADMIN: `admin_panel` | Oberfläche ohne Fachplugins nutzbar; nur zugängliche aktive Plugins anzeigen |
| S02 | Deutsch, Englisch, Französisch und Fallback | Core-Dienst + Plugin-Übersetzungen | I18N; APP: `inject_globals`; `i18n/` | Fehlende Schlüssel führen zu definiertem Fallback; Plugins besitzen eigene Übersetzungen |
| S03 | UTC-/Lokalzeitbehandlung, Datumsformatierung und Dashboard-Uhr | Core-Dienst | TIME; APP: `format_local_datetime`; UI | Zeitzone in Oberfläche, E-Mails und Exporten konsistent; Sommerzeitfälle prüfen |
| S04 | Systemeinstellungen einschließlich Import/Export | Core; fachliche Einstellungen in Plugins | CONFIG; ADMIN: `admin_settings`, `admin_settings_import`, `admin_settings_export` | Geheimnisse gesondert behandeln; unbekannte oder ungültige Werte validieren |
| S05 | SMTP-Konfiguration und Testversand | Core-Dienst | CONFIG; ADMIN: `admin_settings`; NOTIFY: `_send_message` | Erfolg und Fehler sichtbar; keine Zugangsdaten protokollieren |
| S06 | Willkommens-, Aktivierungs- und Reset-E-Mails | Core + Versanddienst | NOTIFY: `send_user_welcome_notification`, `send_user_activation_notification`, `send_password_reset_notification` | Sprache und Kontostatus berücksichtigen; technischer Versandfehler nachvollziehbar |
| S07 | Steuerung fachlicher E-Mails und Benutzerpräferenzen | Core-Dienst für Versand/Präferenzen; Inhalte und Auslöser in Plugins | CONFIG: `EMAIL_ACTION_DEFS`; NOTIFY; MODELS: `User.status_email_enabled` | Keine globale Abschaltung versehentlich als Verbot notwendiger Kontowiederherstellung interpretieren; Kategorien klar definieren |
| S08 | Impressum und Datenschutz als konfigurierbare Markdown-Inhalte | Core | APP: `imprint`, `privacy`; `legal_markdown.py`; CONFIG | Inhalte sicher rendern und öffentlich erreichbar halten |
| S09 | Aktivitäts-/Audit-Logs, Anzeige, Löschen und zeitgesteuerte Bereinigung | Core-Dienst; fachliche Ereignisse durch Plugins | AUDIT; ADMIN: `admin_logs`, `admin_log_delete`; CONFIG | Berechtigungen, Aufbewahrung und verständliche Ereignisse prüfen; Geheimnisse ausschließen |
| S10 | Dateiablage, Downloads, Größenlimits und grundlegende Vorschauen | Core-Dateidienst + fachliche Plugin-Regeln | APP: Upload-/Download-Routen, `handle_request_entity_too_large`, `save_image_thumbnail` | Pfad- und Zugriffsprüfung; Grenzen serverseitig erzwingen; Dateitypen je Plugin festlegen |
| S11 | PDF-Erzeugung und Ersatzdarstellung bei fehlenden Möglichkeiten | Technischer Exportdienst bei Bedarf; Inhalte in Plugins | APP: `render_pdf_with_template`, `_build_text_rows_pdf`, `_build_order_pdf` | Fehlende Renderer verständlich behandeln; keinen auftragsabhängigen Core erzeugen |
| S12 | Anwendungsversionsanzeige | Core | `neofab/version.py`; APP: `show_version`; UI | Eine zentrale Versionsquelle; Core-/Plugin-Versionen unterscheidbar |

## C. Gemeinsame Auftragsfunktionen

| ID | Aktuell in NeoFab | Ziel in NeoFab2 | Quellbezug | Prüfkriterium / Umsetzungshinweis |
|---|---|---|---|---|
| O01 | Auftrag anlegen und ändern, Besitzer, Titel, Beschreibung und Status | Plugin `orders` | MODELS: `Order`; APP: `new_order`, `order_detail` | Besitzer-/Mitarbeiterrechte prüfen; Stammdaten der Fertigung nicht in den Basiskopf einbauen |
| O02 | Projektinformationen, öffentliche Nutzungsfreigaben und Beschreibungen | Plugin `orders` | MODELS: `Order`; APP: `new_order`, `order_detail` | Bestehende Feldbedeutung sichten; Freigaben explizit speichern und korrekt anzeigen |
| O03 | Kategorien, konfigurierbare Reiter und Bearbeiterrollen | Plugin `orders` + Fachplugin-Registrierung | MODELS: `OrderCategory`; APP: `get_visible_order_tabs`, `can_manage_order_category` | Kategorien und aktive Plugins zuordnen; deaktivierte Plugins nicht nur im Menü verbergen |
| O04 | Benutzerbezogene Kategorie-Bearbeitungsrechte | Core-Rechteprüfung + Regeln in `orders`/Fachplugin | MODELS: `UserOrderCategoryPermission`; APP: `can_view_order` | Fachliche Berechtigungen explizit abbilden; keine unkontrollierte Übernahme alter Kategorie-IDs |
| O05 | Auftragsbereiche, Import/Export und persönliche Bereichsfilter | Plugin `orders` | MODELS: `OrderArea`, `UserOrderAreaPreference`; ADMIN: `admin_area_import`, `admin_area_export` | Bereichsverwaltung und persönliche Auswahl prüfen; nicht mit allgemeiner Mandantenfähigkeit gleichsetzen |
| O06 | Stabile Auftragsnummern und administrativer Sequenzreset | Plugin `orders` | SCHEMA: `reserve_next_order_id`, `reset_order_id_sequence`; ADMIN: `admin_orders_delete_all` | Nummern unter Parallelzugriff eindeutig; Reset nur bei erfüllten Voraussetzungen |
| O07 | Dashboard-Suche, kombinierte Filter, Sortierung, Pagination und Spaltenauswahl | Plugin `orders`; Core stellt Oberfläche bereit | APP: `dashboard`; CONFIG: `DASHBOARD_COLUMN_DEFS`; UI | Such-/Filterzustand bleibt erhalten; nur berechtigte Aufträge sichtbar |
| O08 | Nachrichten je Auftrag, Gelesen-Status und Aktualisierung von Nachrichtenfragmenten | Plugin `orders` + Versanddienst | MODELS: `OrderMessage`, `OrderReadStatus`; APP: `order_messages_fragment`, `order_detail` | Verlauf, ungelesene Nachrichten und Versandregeln pro Benutzer prüfen |
| O09 | Projektbilder, Dokumentationsdateien und Videos mit Notizen | Plugin `orders` + Dateidienst | MODELS: `OrderImage`, `OrderVideo`, `OrderFile`; APP: `order_detail` | Allgemeine Dokumentation von druckspezifischen Modelldaten trennen; bisherige Videoformate und 200-MB-Grenze bewusst bestätigen oder ändern |
| O10 | Statuswechsel und Stornierung, Statusbeschriftungen | Plugin `orders`; spezifische Regeln in Fachplugins | APP: `order_detail`; `status_messages.py`; NOTIFY: `send_order_status_change_notification` | Zulässige Übergänge und Auslöser definieren; ungültige Wechsel zurückweisen |
| O11 | Archivieren, einzelne Aufträge mit Dateien löschen und Gesamtbereinigung | Plugin `orders` + Datei-/Bereinigungsdienste | ADMIN: `admin_order_archive`, `admin_order_delete`, `admin_orders_delete_all` | Abhängige Daten und Dateien konsistent behandeln; Fehlerwiederaufnahme und Rechte prüfen |
| O12 | Auftrags-PDF mit Projektdaten und Fachinformationen | Plugin `orders` + Beiträge der Fachplugins | APP: `build_order_context`, `admin_order_pdf`; `doku/pdf_template.html` | Export enthält nur zugängliche Daten; deaktivierte Fachmodule geregelt behandeln |
| O13 | Kostenstellenverwaltung, Import/Export und Kostenstellen-PDF | Zunächst Plugin `orders`; späterer eigenständiger Finanzbereich nur bei Bedarf | MODELS: `CostCenter`; ADMIN: `admin_cost_center_*` | Fachplugins liefern Kostenpositionen über Schnittstelle; Summen gegen Beispiele prüfen |
| O14 | Allgemeine Arbeitsaufträge mit Maschine, Materialnotiz, Kosten und Dauer | Plugin `orders` als gemeinsame Basis; CNC-spezifische Ausprägung in `milling` | MODELS: `OrderWorkJob`; APP: `order_detail` | Tatsächlich nutzbaren Bestand sichten; kein vollständiges CNC-System aus dem Datenmodell ableiten |

## D. Fachplugins für Fertigung und Beschaffung

| ID | Aktuell in NeoFab | Ziel in NeoFab2 | Quellbezug | Prüfkriterium / Umsetzungshinweis |
|---|---|---|---|---|
| D01 | 3D-Modell-Uploads, Mengen, Material-/Farbzuordnung und Dateiverwaltung | Plugin `printing3d` | MODELS: `OrderFile`; APP: `order_detail`, `set_file_color` | Fachmetadaten im Plugin; Dateien nur mit Berechtigung lesbar und änderbar |
| D02 | STL-/3MF-Viewer, Anzeigeoptionen und Modell-Thumbnails | Gemeinsame interne 3D-Viewer-Komponente; fachliche Einbindung durch `printing3d` | APP: `order_file_preview`, `generate_stl_thumbnails`; UI und `neofab/static/` | STL für ersten MVP; 3MF/OBJ und weitere Formate später separat prüfen. Rechte/Fehlerfälle testen; kein eigenständiges sichtbares Viewer-Plugin |
| D03 | Druckaufträge, G-Code-Dateien, Maschinenzuordnung, Zeiten und Druckstatus | Plugin `printing3d` | MODELS: `OrderPrintJob`; APP: Aktionen `upload_print_job`, `update_print_job`, `delete_print_job` | Druckstatus und Auftragstatus getrennt modellieren; Zugriffe und Löschverhalten prüfen |
| D04 | G-Code-Analyse für Druckdauer, Filamentlänge/-gewicht und Ergänzung fehlender Werte | Plugin `printing3d` | APP: `extract_gcode_metadata`, `apply_gcode_metadata_to_job`; `doku/GCode_Druckparameter_Automatik.md` | Mehrere Slicer-Kommentare und fehlende Daten prüfen; manuelle Eingaben nicht unbeabsichtigt überschreiben |
| D05 | Druckerprofile, Materialien, Filamente und Farben einschließlich Import/Export | Plugin `printing3d` | MODELS: `PrinterProfile`, `Material`, `FilamentMaterial`, `Color`; ADMIN: zugehörige CRUD-/Import-/Export-Routen | Fachliche Stammdaten und aktive Referenzen prüfen; Materialkatalog nicht vorsorglich in Core verschieben |
| D06 | 3D-Druck-Kosten aus Maschine, Material, Menge, Zeit und Rüstkosten | Plugin `printing3d`; Kostenschnittstelle zu `orders` | MODELS: `OrderPrintJob`; APP: `order_detail`; `doku/Kostenermittlung_3D_Druck.md` | Bekannte Rechenbeispiele, Einheiten und Rundung prüfen |
| D07 | Druckstatus-Zusammenfassungen und automatische Auftragsstatus-Anpassung | Plugin `printing3d`; Dashboard-Beitrag zu `orders` | APP: `sync_3d_order_status_from_print_jobs`, `dashboard` | Gemischte laufende, fertige und fehlgeschlagene Drucke korrekt zusammenfassen |
| P01 | JPG-/PNG-/PDF-Plakate, Bemerkung, Anzahl und gewünschtes Druckdatum | Plugin `plotting` | MODELS: `OrderPosterFile`; APP: Aktionen `upload_poster_file`, `update_poster_file` | Mehrere Plakate je Auftrag und sichere Dateioperationen prüfen |
| P02 | Bild- und PDF-Vorschauen mit Ersatzvorschau | Plugin `plotting` + technischer Vorschaudienst | APP: `save_poster_thumbnail`, `poster_file_thumbnail` | Erste PDF-Seite bei vorhandenem Renderer; verständlicher Fallback bei fehlender Unterstützung |
| P03 | Papiere, Plottertypen, Standardpapier und Import/Export | Plugin `plotting` | MODELS: `PlotterPaper`, `PlotterType`; ADMIN: `admin_plotter_*` | Standardpapier und in Nutzung befindliche Stammdaten konsistent behandeln |
| P04 | Formate, Deckungsgradanalyse und Plakatkosten | Plugin `plotting` | `neofab/plotter_utils.py`; APP: `analyze_poster_coverage`; `doku/Plakat_Kostenermittlung.md` | Papier-, Tinten-, Maschinen-, Wartungs-, Mengen- und Rüstkosten gegen Referenzfälle prüfen |
| P05 | Als gedruckt markieren, Auftragsstatus und E-Mail dazu | Plugin `plotting` + Versanddienst | APP: `mark_poster_printed`-Aktion, `sync_plotter_order_status_from_posters`; NOTIFY: `send_poster_printed_notification` | Teilfertige und vollständig fertige Aufträge korrekt behandeln |
| B01 | Beschaffungsartikel mit Lieferant, Link, Beschreibung, Menge, Preis und Positionsnummer | Plugin `procurement` | MODELS: `OrderProcurementArticle`; APP: Artikelaktionen, `ensure_procurement_article_position_numbers` | Positionen, Mengen und Preisangaben validieren; stabile Reihenfolge |
| B02 | Notizanhänge für Artikel | Plugin `procurement` + Dateidienst | APP: `download_procurement_article_note_file`, Artikelaktionen | Unterstützte Dokumenttypen und Rechte prüfen; Austausch/Löschung räumt zugehörige Datei auf |
| B03 | Bestellt-/Geliefert-Status und automatische Auftragsstatus-Aktualisierung | Plugin `procurement` | APP: `sync_procurement_order_status_from_articles`, Artikelstatusaktionen | Gemischte Artikelstatus und vollständige Lieferung prüfen |
| B04 | Artikelliste per E-Mail an ausgewählte Empfänger | Plugin `procurement` + Versand-/Favoritendienst | APP: Aktion `send_procurement_article_list`; NOTIFY: `send_procurement_article_list_email` | Inhalt, berechtigte Empfängerauswahl und Versandfehler prüfen |
| F01 | CNC/Fräsen als Auftragskategorie mit allgemeinem Arbeitsablauf | Plugin `milling` | MODELS: `OrderCategory`, `OrderWorkJob`; APP: Kategorien/Reiter | Vor Umsetzung benötigte Maschinen-, Datei-, Status- und Kostenfunktionen bestimmen; Bestand nicht als vollständigen Fräsworkflow ausweisen |

## E. Termine, Mitteilungen und Lernmaterialien

| ID | Aktuell in NeoFab | Ziel in NeoFab2 | Quellbezug | Prüfkriterium / Umsetzungshinweis |
|---|---|---|---|---|
| T01 | Terminanfrage zu einem Auftrag mit Nachricht | Plugin `order_appointments` – Vorschlag | MODELS: `OrderAppointmentRequest`; APP: Aktion `request_appointment` | Nur berechtigte Auftragsbeteiligte; kein Workshop-Modell daraus ableiten |
| T02 | Vorschläge mit Dauer, Auswahl, Ablehnung aller Vorschläge und Bestätigung | Plugin `order_appointments` – Vorschlag | APP: `appointment_detail`, Aktion `select_appointment_time`; MODELS: `OrderAppointmentRequest` | Zustandswechsel, geänderte Vorschläge und notwendige erneute Bestätigung prüfen |
| T03 | Terminliste, Wochenkalender und mehrere Termine im Dashboard | Plugin `order_appointments`; Beitrag zu `orders` | APP: `appointments`, `dashboard`; UI: `appointments.html` | Bestätigte und zusätzlich offene Vorschläge gleichzeitig korrekt anzeigen |
| T04 | Terminbenachrichtigungen und Kalenderanhang | Plugin `order_appointments` + Versanddienst | NOTIFY: `send_appointment_proposal_notification`, `send_appointment_confirmation_notification` | Empfänger, Zeitangaben und Kalenderdaten prüfen |
| A01 | Mitteilungen erstellen, bearbeiten, löschen, importieren und exportieren | Plugin `announcements` – Vorschlag | MODELS: `Announcement`; APP: `announcement_update`, `dashboard`; ADMIN: `admin_announcement_*` | Sichtbarkeit, redaktionelle Rechte und definierte Anzeigepunkte prüfen |
| A02 | Mitteilungen als gelesen markieren, wichtige Mitteilungen per E-Mail | Plugin `announcements` + Versanddienst | MODELS: `AnnouncementRead`; APP: `mark_announcement_read`-Aktion; NOTIFY: `send_announcement_attention_notification` | Gelesen-Status je Benutzer; Empfänger und Wiederholungsregeln prüfen |
| L01 | Trainingsvideos/YouTube-Einbindung und PDF-Unterlagen | Plugin `learning` – Vorschlag | MODELS: `TrainingVideo`; APP: `tutorials`, `tutorial_pdf`, `extract_youtube_id` | Linkvalidierung, Anzeige und Downloadrechte prüfen; keine Teilnahmeverwaltung unterstellen |
| L02 | Playlists, Sortierung, Videoverwaltung und Videoimport/-export | Plugin `learning` – Vorschlag | MODELS: `TrainingPlaylist`; ADMIN: `admin_training_*` | Zuordnungen und Reihenfolge bleiben konsistent; Importformat dokumentieren |

## F. Installation, Wartung und Entwicklung

| ID | Aktuell in NeoFab | Ziel in NeoFab2 | Quellbezug | Prüfkriterium / Umsetzungshinweis |
|---|---|---|---|---|
| X01 | Interaktive Basisinstallation mit optionalem Teststart | Betrieb, bereits Core-Lieferumfang | `script/setupNeoFab`, `script/README.md` | Vertraute Fragen/Vorgaben; eigene NeoFab2-Pfade; Installation auf sauberer Testumgebung |
| X02 | Gunicorn-/systemd-Service einrichten | Betrieb, bereits Core-Lieferumfang | `script/setupNeoFabService` | Start, Stop und Neustart prüfen; erforderliche Worker/Timer dokumentieren |
| X03 | Aktualisierung aus Git, Abhängigkeiten und Service-Neustart | Betrieb, bereits Core-Lieferumfang | `script/upDateNeoFabService` | Explizite Migrationen und Sicherung integrieren; Updatefehler dürfen nicht als Erfolg gemeldet werden |
| X04 | Admin-Passwort lokal wiederherstellen | Betrieb/Core-Wiederherstellungszugang | `script/resetAdminPassword` | Admin-Auswahl und verdeckte Passworteingabe; ohne Webanmeldung nutzbar; keine Passwortprotokollierung |
| X05 | Deutsche Schritt-für-Schritt-Anleitungen, Schnellstart und Fachbeschreibungen | Betrieb/Entwicklung; Dokumentation je Plugin | `script/README.md`, `doku/SETUP.md`, fachliche Dateien unter `doku/` | Befehle, Benutzer, Pfade, Standardwerte und Ergebnisprüfung stimmen mit Implementierung überein |
| X06 | Versionsquelle, README-Versionsangaben und Versionshistorie | Betrieb/Entwicklung + Core-Anzeige | `neofab/version.py`, `README*.md`, `doku/Version_Timeline.md` | Angeforderte Version konsistent aktualisieren; neue Historie für NeoFab2; Commit-Titel/-Beschreibung liefern, Commit manuell in GitHub Desktop |
| X07 | Schema-Ergänzungen und initiale Datenanlage | Core-Migrationen und pluginbezogene Migrationen | APP: `ensure_*`, `init_db`, `init_stammdaten`; SCHEMA | Bestehenden Mechanismus durch explizite versionierte Migrationen ersetzen; keine Schemaänderung bei Seitenaufrufen |
| X08 | Administrativer Design-Smoke-Test | Entwicklungs-/Prüfwerkzeug, bei Bedarf | ADMIN: `admin_design_smoke_test`; UI: `admin_design_smoke_test.html` | Gemeinsame UI und Plugin-Komponenten prüfbar; kein Pflichtbestandteil produktiver Fachnavigation |

## G. Neue Anforderungen ohne entsprechenden vollständigen NeoFab-Bestand

| ID | Neu für NeoFab2 | Ziel und Abhängigkeit | Nachweis für die spätere Umsetzung |
|---|---|---|---|
| N01 | Plugin-Registrierung, API-Versionen, Abhängigkeiten und Aktivierung | Core; Testplugin zuerst | Core ohne Fachplugins; Deaktivierung sperrt direkte Zugriffe und Aufgaben; keine Datenlöschung |
| N02 | Workshops/Schulungen mit Veröffentlichung und Teilnehmeranmeldung | Plugin `workshops`; nur Core | Rechte für eigene/alle Veranstaltungen, Kapazitätsprüfung unter Parallelzugriff, An-/Abmeldung und Änderungs-/Absageinformationen |
| N03 | Transferdruck | Plugin `transfer_printing`; Core + `orders` | Verfahren, Artikel/Trägermaterial, Motive, Mengen, Status und Kosten vor Umsetzung spezifizieren; nicht vom Plotter-Plugin abhängig machen |
| N04 | Gezielte einmalige Benutzerübernahme aus NeoFab | Core-Importwerkzeug | Lesende Quelle; wiederholbarer Import; Hash-Kompatibilität prüfen; keine Übernahme alter Aufträge, Dateien oder Sitzungen |
| N05 | Persistente Versandaufträge mit Wiederholungen und minimale Hintergrundausführung | Core-Dienst | SMTP-Fehler, Neustart und Wiederholungen prüfen; keine Zusage exakt einmaliger SMTP-Zustellung |
| N06 | Gemeinsame jährliche Bereinigung über Plugin-Grenzen | Core-Vertrag + Löschregeln der Plugins, tatsächliche Bereinigung später | Vorschau/Stichtag, berechtigte Bestätigung, zugehörige Dateien, Fehlerwiederaufnahme; Benutzer/Stammdaten getrennt |
| N07 | Gemeinsame Kalenderanzeige verschiedener Fachbereiche | Spätere Erweiterung, Grenze noch offen | Auftrags- und Workshop-Termine bleiben getrennte Fachmodelle; noch kein Auftrag für ein allgemeines Kalenderplugin |
| N08 | Wartelisten, Erinnerungen, Serientermine und Qualifikationsnachweise | Spätere Erweiterung von `workshops` | Erstumfang separat vereinbaren; Aufbewahrung von Qualifikationen unabhängig von Veranstaltungsdaten regeln |
| N09 | Übergabe freigegebener 3D-Druckaufträge an PrintFleet und lesender Statusrückkanal | Anschlussausbau von `printing3d`, nach lokalem MVP | Tatsächliche API erst klären; externe Druckerauswahl/Steuerung, Job-Zuordnung, Wiederholung, Timeout, Statusmapping und Deaktivierung mit Testadapter prüfen |

## Ergänzte Plugin-Planung vom 18.09.2026

Maßgeblich ist der [Plugin-Umsetzungsplan](Plugin_Umsetzungsplan.md): `printing3d`
als erstes Fach-/Referenzplugin nach vollständiger Core-Abnahme, davor minimale
`orders`-Basis und gemeinsame Datei-/Viewer-Komponenten. Workshops folgen später.
`employee` entspricht dem bestehenden `staff`; API-1-Ausbau mit mehreren Rechten
und Besitzerprüfung wurde mit Paket 0 in 0.1.10 umgesetzt. Kein React-Wechsel, keine automatische
Freigabe von Laser-/Scan-Plugins. G-Code-Analyse und lokale Kosten/Status gehören
zum MVP, PrintFleet erst zum Anschlussausbau.

## Migrationsregeln

- **Funktionen übernehmen bedeutet nicht Bestandsdaten übernehmen.** Alte Aufträge, Nachrichten, Termine, Mitteilungen, Lernmaterialien und Auftragsdateien gehören nicht zur zugesagten Benutzerübernahme.
- Nur Benutzer werden gemäß Importvertrag übernommen. Fachliche Benutzerpräferenzen und Berechtigungen benötigen eine explizite Zuordnung; alte Tokens und Sitzungen werden verworfen.
- Stammdaten wie Drucker, Papiere oder Kostenstellen können später nach gesonderter Entscheidung importiert werden. Ihre Datenübernahme ist nicht durch diese Matrix beauftragt.
- Bewährte Berechnungen und Validierungen dürfen nach Prüfung wiederverwendet werden. Direkte Importe aus dem alten monolithischen `app.py` sind keine dauerhafte NeoFab2-Schnittstelle.
- Deaktivierung, Archivierung, Löschung und jährliche Bereinigung sind unterschiedliche Vorgänge. Ein Plugin-Ausbau darf vorhandene Daten nicht stillschweigend löschen.

## Quellverzeichnis für Codex

Die Kürzel beziehen sich auf den oben genannten Git-Stand. Funktions- und Modellnamen sind als Suchanker angegeben, damit spätere Zeilenverschiebungen die Verweise nicht entwerten.

| Kürzel | Pfad im bisherigen Repository |
|---|---|
| APP | `neofab/app.py` |
| MODELS | `neofab/models.py` |
| ADMIN | `neofab/routes/admin.py` |
| AUTH | `neofab/auth_utils.py` |
| CONFIG | `neofab/config.py` |
| NOTIFY | `neofab/notifications.py` |
| SCHEMA | `neofab/schema_utils.py` |
| TIME | `neofab/time_utils.py` |
| I18N | `neofab/i18n_utils.py` |
| AUDIT | `neofab/audit_logs.py` |
| UI | `neofab/templates/` und `neofab/static/` |

## Umsetzungsnachweis – während der Entwicklung fortführen

Zulässige Statuswerte: **geplant**, **in Arbeit**, **implementiert**, **geprüft**, **zurückgestellt**, **entfällt nach Entscheidung**. Eine ID kann mehrere Teilnachweise erhalten, wenn Core und Plugin beteiligt sind. Für die gesamte ID gilt „geprüft“ erst nach Prüfung aller eingeplanten Teile; ausgenommene Teile ausdrücklich nennen.

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| X06 | geprüft | `src/neofab2/version.py`, `pyproject.toml`, `README.md`, `doku/Version_Timeline.md` | Version 0.1.8 in Paket, CLI und Oberfläche; Commit-Texte vorhanden | Kein Commit/Push ausgeführt |
| X05 | in Arbeit | `doku/SETUP.md`, `doku/operations.md`, `script/README.md` | Links und Übereinstimmung mit Skripten geprüft | Echte Debian-/LXC-Erprobung offen |
| S01 | in Arbeit | `src/neofab2/core/routes.py`, `core/accounts.py`, `core/plugins.py`, `templates/`, `static/core.css` | Startseite, Login, Profil, Benutzerverwaltung und rechteabhängige Core-/Plugin-Navigation per HTTP-Test geprüft | Infoseite und interaktive visuelle Browserprüfung offen |
| S12 | in Arbeit | `src/neofab2/version.py`, `templates/base.html`, `templates/plugins.html` | Core-Versionsanzeige, Paketmetadaten und separate Plugin-Versionen geprüft | Weiterer Ausbau der Systeminformationen offen |
| X07 | in Arbeit | `src/neofab2/database.py`, `migrations/versions/0001_core_settings.py`, `0002_core_users.py`, `tests/integration/test_accounts_cli.py` | Migration vom vorherigen Schema mit Erhalt der Einstellungen, Wiederholung, fehlendes Schema und Start ohne implizite Migration geprüft | Weitere Core-/Plugin-Schemata folgen |
| X01 | implementiert | `script/setupNeoFab`, `tests/integration/test_setup_teststart.py` | Nutzer meldet laufendes Grundsystem; Teststart-CWD korrigiert. HTTPS-Auswahl und interaktiven Erstadmin ergänzt; CLI und Shell-Syntax geprüft | Kein eigener LXC-Erstlauf des neuen Benutzer-Schritts; feste NeoFab2-Pfade/Benutzer |
| X02 | implementiert | `script/setupNeoFabService` | Bash-Syntax und ShellCheck bestanden | systemd-Echttest offen; noch keine Hintergrundaufgaben |
| X03 | implementiert | `script/upDateNeoFabService`, `src/neofab2/cli.py`, `tests/integration/` | Simulierte Update-Steuerung inkl. Fehlerfällen und SQLite-Backup/Restore geprüft | Echter Service-/LXC-Update- und Vollrestore-Test offen |
| X04 | implementiert | `script/resetAdminPassword`, `src/neofab2/cli.py`, `core/users.py`, `tests/integration/test_accounts_cli.py` | Admin-Auswahl, verdeckte Eingabe, Sperrstatus, explizite Reaktivierung und Sitzungswiderruf per CLI geprüft | Echter Skriptlauf im LXC noch offen |
| U01 | geprüft | `src/neofab2/core/auth.py`, `accounts.py`, `tests/core/test_accounts.py` | Gültige/falsche/unbekannte/deaktivierte Logins, Logout, scrypt-Hashing, CSRF und serverseitige Anmeldebegrenzung geprüft | Keine Selbstregistrierung/E-Mail-Verfahren in diesem Teilumfang |
| U05 | in Arbeit | `src/neofab2/core/users.py`, `accounts.py`, `tests/core/test_accounts.py` | Anlegen/Bearbeiten/Aktivieren/Deaktivieren, doppelte E-Mail, serverseitige Rechte und paralleler Letzter-Admin-Schutz geprüft | Benutzerlöschung mit Auswirkungen auf Plugins bleibt offen |
| U06 | in Arbeit | `src/neofab2/core/users.py`, `auth.py`, `plugins.py`, `plugin_api/` | Rollen Benutzer/Mitarbeiter/Administrator, explizite Plugin-Rechte, Direktzugriff und Profil-Eskalation geprüft | Rollenpflege, feinere Plugin-Rechte und Altrollen-Zuordnung folgen |
| U07 | in Arbeit | `src/neofab2/core/accounts.py`, `core/users.py`, `core/i18n.py`, `templates/profile.html`, `static/core.css` | Anzeigename, Passwortwechsel, dauerhafte Darstellung und Sprachwahl geprüft; seit 0.1.7 englische Ausgangssprache und Fallback | Vollständige Übersetzungen und visuelle Abnahme offen |
| U08 | geprüft | `src/neofab2/core/auth.py`, `config.py`, `tests/core/test_accounts.py` | Server-Inaktivitätsfrist, absolute Laufzeit, Cookie-Replay nach Logout und unveränderte Frist bei Health-/Static-Anfragen geprüft | Keine dauerhaften Remember-me-Sitzungen vorgesehen |
| N01 | in Arbeit | `src/neofab2/plugin_api/`, `src/neofab2/core/plugins.py`, `core/plugin_state.py`, `src/neofab2/plugins/`, `tests/plugin_contract/` | API 1: Metadaten, Abhängigkeiten, Rechte, Navigation, Backend-Auswahl und Aktivierung nach Neustart; zwei Testplugins und lokale Aufgaben geprüft | Weitere Dienstverträge, fachliche Plugin-Einstellungen und persistente Aufgaben offen |

### Nachbesserung Anmeldung und Erstadmin (17.09.2026, weiterhin 0.1.2)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| U01, U05, U07, X04 | geprüft (Teilumfang) | `src/neofab2/core/users.py`, `src/neofab2/cli.py`, `src/neofab2/templates/profile.html`, `src/neofab2/templates/user_form.html`, `tests/core/test_accounts.py`, `tests/integration/test_accounts_cli.py` | Einheitlich 8–128 Zeichen; Grenzen 7/8/128/129 sowie Anlage, Anmeldung, Wechsel und CLI-Reset mit 8 Zeichen geprüft; insgesamt 53 Tests bestanden | Keine Schemaänderung; vorhandene Passwörter bleiben gültig; übrige offene Teile der IDs unverändert |
| U01 | geprüft (Teilumfang) | `src/neofab2/__init__.py`, `src/neofab2/templates/error.html`, `tests/core/test_accounts.py` | Fehlendes Sitzungscookie reproduziert; eigener Cookie-/HTTPS-Hinweis und Link zur Anmeldung; CSRF bleibt aktiv | Secure-Cookie bei HTTP ist eine mögliche Ursache im Nutzercontainer, dort nicht selbst geprüft |
| X01, X04, X05 | implementiert (Dokumentation) | `doku/SETUP.md`, `doku/Core_Zugang.md`, `script/README.md` | Automatische Erstadmin-Abfrage, erste Anmeldung, lokaler Passwort-Reset und HTTP-Cookie-Fehlerhilfe dokumentiert; Nutzer bestätigt funktionierendes Admin-Skript | Neuer Stand nicht selbst im LXC geprüft; frühere Aussage zum offenen Skriptlauf durch Nutzerrückmeldung ergänzt |

### Weitere Eingrenzung des Loginfehlers (17.09.2026)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| U01, U08 | geprüft | `tests/core/test_accounts.py` | Sechs zusätzliche Fälle mit echtem HTTP-Server und CookieJar: Secure bei HTTP führt mit richtigen/falschen Passwörtern und unbekannter E-Mail zu 400; ohne Secure erfolgreiche Anmeldung bzw. 401. Alle 34 Tests dieser Datei bestanden | Teilnachweis; konkrete Ursache im Nutzercontainer weiterhin unbestätigt, keine Änderung der Authentifizierung auf Verdacht |
| X05 | implementiert | `doku/SETUP.md` | Diagnose des ausgelieferten Cookie-Attributs mit ausgeblendetem Wert, Prüfung von Browser und Dienstkonfiguration dokumentiert | Antwortheader des betroffenen Dienstes zur weiteren Eingrenzung erforderlich |

### Plugin-Grundsystem 0.1.3 und bestätigter Container-Zugang (17.09.2026)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| N01 | in Arbeit | `src/neofab2/plugin_api/`, `src/neofab2/plugins/`, `tests/plugin_contract/test_plugins.py` | 14 Vertragstests: Aktivierung/Deaktivierung, Abhängigkeiten inklusive Zyklen und Mindestversionen, API-Kompatibilität und Aufgaben; alle bestanden | Ein Recht je Plugin, keine persistenten Jobs oder weiteren Dienstverträge; kein eigener LXC-Test dieses Schritts |
| U06, S01, S12 | in Arbeit | `src/neofab2/core/plugins.py`, `core/users.py`, `templates/base.html`, `templates/plugins.html` | Rollenabhängige Navigation, direkte Zugriffe mit Benutzer/Mitarbeiter/Admin, CSRF und Plugin-Versionen geprüft | Rollenpflege, weitere Oberfläche und interaktive Browserprüfung offen |
| U01, U07, X05 | geprüft (Teilumfang) | `doku/Core_Zugang.md`, `doku/SETUP.md` | Nutzer bestätigt Login und Passwortwechsel im Container; ausgelieferter Secure-Cookie und HTTP-Zugang belegten Ursache; Umstellung auf false erfolgreich | Gilt für diese Zugangsfunktionen, keine vollständige LXC-/Core-Abnahme; ersetzt vorherige offene Ursacheneingrenzung |
| X05, X06 | geprüft (Teilumfang) | `doku/plugin-development.md`, `script/README.md`, `doku/Version_Timeline.md`, `src/neofab2/version.py` | Version 0.1.3, Betriebsablauf und Commit-Texte ergänzt; 73 Gesamttests, danach 14 Plugin-Tests erneut; Wheel/sdist und installiertes Wheel geprüft | Keine neue Schema-Revision, kein Commit/Push |

### Systemeinstellungen und Darstellung 0.1.4 (17.09.2026)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| S04, S01 | in Arbeit | `src/neofab2/core/settings.py`, `templates/settings.html`, `templates/index.html`, `tests/core/test_settings.py` | Admin-Recht, CSRF, Textgrenzen, HTML-Maskierung, transaktionale Speicherung, Neustart-Persistenz und Isolation fremder Schlüssel geprüft | Öffentliche Darstellungseinstellungen; Import/Export, SMTP und weitere Einstellungen offen |
| U07 | in Arbeit | `src/neofab2/core/users.py`, `core/accounts.py`, `templates/profile.html`, `static/core.css`, `tests/core/test_settings.py` | Persönliche Darstellung bleibt nach neuer Anmeldung erhalten, überschreibt Standard und verändert keine fremden Konten | Sprachwahl/Übersetzungen offen; kein Browser für visuelle Prüfung verbunden |
| X07 | geprüft (Teilumfang) | `migrations/versions/0003_user_theme.py`, `src/neofab2/database.py`, `tests/core/test_settings.py` | Explizites Upgrade von 0002 mit Benutzer-/Hash-/Einstellungserhalt; Wiederholung und Ablehnung des alten Schemas geprüft | Nur Testdaten; keine produktive Migration durch Codex |
| X05, X06 | geprüft (Teilumfang) | `doku/Core_Einstellungen.md`, `doku/SETUP.md`, `script/README.md`, `doku/Version_Timeline.md` | Version 0.1.4; 84 Tests bestanden, Wheel/sdist gebaut und installiertes Wheel geprüft; Update-/Prüfbefehle dokumentiert | Neuer Container-Test und visuelle Prüfung offen; kein Commit/Push |
| N01, X03 | implementiert | `doku/plugin-development.md`, `doku/Version_Timeline.md` | Nutzer meldet Schritt 0.1.3 als erfolgreich | Rückmeldung ersetzt keinen vollständigen Einzeltest aller Abhängigkeiten oder einen Vollrestore-Test |

### Plugin-Verwaltung 0.1.5 (17.09.2026)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| N01, U06 | in Arbeit | `src/neofab2/core/plugin_state.py`, `core/plugins.py`, `core/users.py`, `tests/plugin_contract/test_management.py` | Backend-Auswahl, Rechte/CSRF, Abhängigkeitsprüfung vor Speicherung, Parallelität, TOML-Ausgangswert, Neustart und Wiederherstellung geprüft; 95 Gesamttests bestanden | Laufende Prozesse übernehmen Änderungen erst beim Neustart; weitere Dienstverträge offen |
| N01, S01, S12 | geprüft (Teilumfang) | `src/neofab2/plugins/management_test.py`, `plugins/templates/management_test/index.html`, `templates/plugins.html` | Zweites Testplugin mit deklarierter Abhängigkeit und Formular; aktuelle und gespeicherte Zustände getrennt; Pakettest mit Backend-Aktivierung und neuem App-Start bestanden | Testplugin 0.1.0, API 1; keine Fachfunktion; keine globale Prozessüberwachung |
| X05, X06 | geprüft (Teilumfang) | `doku/plugin-development.md`, `doku/SETUP.md`, `script/README.md`, `doku/Version_Timeline.md`, `src/neofab2/cli.py` | Version 0.1.5, manuellen Proxmox-Neustart und bestätigte lokale Wiederherstellung dokumentiert; Wheel/sdist und CLI geprüft | Kein eigener Container-Neustart oder interaktiver Browsertest; keine neue Schema-Revision; kein Commit/Push |
| S04, U07 | implementiert | `doku/Core_Einstellungen.md` | Nutzer meldet vorherigen Schritt 0.1.4 als lauffähig | Keine zusätzliche vollständige Core-Abnahme aus dieser Rückmeldung abgeleitet |

### Abschluss des Arbeitspakets 0.1.6 (18.09.2026)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| U05 | in Arbeit | `src/neofab2/templates/user_form.html`, `core/users.py`, `core/accounts.py`, `tests/core/test_user_details.py` | Screenshot-Felder in beiden Formularen, Sprache/Aktivstatus, optionales neues Passwort, Grenzen, Datenerhalt, Maskierung und Sitzungswiderruf geprüft | Benutzerlöschung offen; Aktivierungslink benötigt Versanddienst. Kostenstelle ausdrücklich als Benutzer-Freitext, keine Fachplugin-Abhängigkeit |
| S02, U07 | in Arbeit | `src/neofab2/core/i18n.py`, `core/accounts.py`, `core/users.py`, `templates/base.html`, `templates/login.html`, `templates/profile.html`, `tests/core/test_i18n.py` | Navigation, Login, Profil und Zugangsfehler DE/EN/FR; Persistenz, CSRF, Priorität und Fallback geprüft; 114 Gesamttests bestanden | Weitere Admin-Seiten, Startseiten- und Plugin-Inhalte noch nicht vollständig übersetzt |
| X07 | geprüft (Teilumfang) | `migrations/versions/0004_user_locale.py`, `0005_user_details.py`, `tests/core/test_i18n.py`, `tests/core/test_user_details.py` | Explizite Upgrades, Wiederholung und Erhalt von Hash/Darstellung/Sprache geprüft; Zusatzfelder standardmäßig leer | Keine Übernahme realer Daten aus Screenshot oder NeoFab |
| X05, X06 | geprüft (Teilumfang) | `doku/Core_Sprachen.md`, `doku/Benutzerverwaltung.md`, `doku/Version_Timeline.md`, `src/neofab2/version.py` | 0.1.6 dokumentiert; Paketbau, installiertes Wheel einschließlich neuer Benutzerfelder und CLI geprüft | Eigener Container-Test und interaktive visuelle Abnahme offen; kein Commit/Push |
| N01 | implementiert | `doku/plugin-development.md` | Nutzer meldet 0.1.5 als funktionierend | Keine vollständige Core-Abnahme daraus abgeleitet |

### Englische Ausgangssprache und Core-Arbeitsplan 0.1.7 (18.09.2026)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| S02, U07 | geprüft (Teilumfang) | `src/neofab2/core/i18n.py`, `core/accounts.py`, `core/users.py`, `templates/`, `tests/core/test_i18n.py` | Englische Ausgangsschlüssel, Standard/Fallback, deutsche Übersetzung, bestehendes Französisch, Kontovorrang, Persistenz, CSRF und Platzhalter-Maskierung geprüft | Vollständiges Französisch und eigene Plugin-Kataloge offen; individuelle Inhalte unverändert |
| S01, U05, S04, N01 | geprüft (Teilumfang) | `src/neofab2/templates/`, `core/settings.py`, `core/plugins.py`, `core/plugin_state.py`, `plugin_api/registry.py`, `plugins/`, `cli.py`, `config.py` | Englische Core-/Admin-/Testplugin-Seiten und CLI; bestehende Rechte-/Formular-/Plugin-Tests auf englische Meldungen aktualisiert | Technische dynamische Plugin-Diagnosen teils nur englisch; weitere Funktionsumfänge der IDs bleiben offen |
| X07 | geprüft (Teilumfang) | `migrations/versions/0006_english_default.py`, `tests/core/test_i18n.py` | Upgrade von 0005, Wiederholung, Datenbank-Standard en, Erhalt DE/EN/FR, Hashes, Zusatzdaten, Einstellungen und Sitzungen sowie E-Mail-Eindeutigkeit/Fremdschlüssel geprüft | Nur synthetische SQLite-Daten, kein Produktivupdate |
| X05, X06, S12 | geprüft (Teilumfang) | `src/neofab2/version.py`, `README.md`, `doku/Core_Sprachen.md`, `doku/SETUP.md`, `script/README.md`, `doku/Version_Timeline.md` | 117 Gesamttests, danach 10 Sprach-/Migrationstests und 16 Plugin-/CLI-Tests; Wheel/sdist und separat installiertes Wheel geprüft; Version 0.1.7 | Keine Container-/interaktive Browser-Abnahme; kein Commit/Push |
| S05, S06, N05, U02–U04, S09, U09, N04, N01, X01–X07 | geplant (weitere Pakete) | `doku/Core_Naechste_Schritte.md`, `doku/NeoFab2_Projektbeschreibung.md`, `doku/architecture.md` | Reihenfolge, Abhängigkeiten, Funktions-IDs und Prüfkriterien dokumentiert | Planung; keine Implementierung dieser weiteren Pakete in 0.1.7; Fachplugins erst nach Core-Abnahme |

### Plugin-Spezifikation ergänzt (18.09.2026, weiterhin 0.1.7)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| X05 | geprüft (Dokumentation) | `doku/Plugin_Umsetzungsplan.md`, `NeoFab2_Projektstart_Codex.md`, `NeoFab2_Projektbeschreibung.md`, `Core_Naechste_Schritte.md`, `plugin-development.md`, `architecture.md`, `README.md` | Eingefügtes Planungsgespräch abgeglichen; Querverweise und widerspruchsfreie neue Reihenfolge geprüft | Reine Planung; keine Versions-/Code-/Schemaänderung in diesem Nachtrag |
| N01, U06, S10, D01–D07, O01, O10 | geplant (Präzisierung) | `doku/Plugin_Umsetzungsplan.md` | Rollenmatrix, API-1-Lücke, gemeinsame STL-Komponente, MVP-Grenzen und Abnahmekriterien dokumentiert | `staff` bleibt gespeicherter Rollenwert; konkrete Kosten-/Status-/Formatregeln offen; Core-Abnahme bleibt Pflicht |
| N09 | geplant | `doku/Plugin_Umsetzungsplan.md` | PrintFleet als Anschlussausbau mit lesendem Statusrückkanal abgegrenzt | Keine geprüfte API, kein Adapter und keine echte Druckersteuerung implementiert |
| N02 | geplant (nachrangig) | `doku/NeoFab2_Projektbeschreibung.md`, `doku/Plugin_Umsetzungsplan.md` | Workshops bleiben erhalten; 3D-Druck ersetzt ihre frühere Erstpriorität | Weitere Reihenfolge offen; Laser/Scan nur Modulideen |

### Betriebsskripte, Feldhilfen und Auswahllisten 0.1.8 (19.09.2026)

| Funktions-ID | Status | Zielpfad / Arbeitspaket | Prüfung und Ergebnis | Abweichung / offene Punkte |
|---|---|---|---|---|
| X01–X04 | geprüft (Teilumfang) | `script/common.sh`, `setupNeoFab`, `setupNeoFabService`, `upDateNeoFabService`, `resetAdminPassword`, `src/neofab2/cli.py`, `tests/integration/test_script_summaries.py`, `test_update_script.py`, `test_setup_teststart.py` | Zusammenfassungen für Erfolg/Abbruch/Fehler, Exit-Code-Erhalt, optionalen Test, IPv4/IPv6, Sicherungsstatus und lesende Admin-/Versionsinformationen ohne Secrets geprüft | Betriebssystembefehle simuliert; echter Debian-/LXC-/systemd-Lauf bleibt offen |
| U05, S04 | geprüft (Teilumfang) | `src/neofab2/core/user_options.py`, `core/users.py`, `core/accounts.py`, `templates/user_options.html`, `templates/user_form.html`, `tests/core/test_user_options.py` | Eigene Formulare für drei Listen; Persistenz, Rechte/CSRF, Grenzen, Duplikate, Maskierung, atomare Umbenennung und Auswahlvalidierung geprüft | Keine Freitextübernahme auf Benutzerwunsch; Kostenstellen nur organisatorische Benutzerangaben, keine O13-Finanzfunktion; keine Listen-Löschung |
| S01, S02, U05, U07 | geprüft (Teilumfang) | `src/neofab2/templates/`, `core/accounts.py`, `static/core.css`, `tests/core/test_user_options.py` | Englische Hilfen an sichtbaren Eingaben, eindeutige IDs und `aria-describedby` sowie spätere Übersetzbarkeit geprüft | DE-/FR-Übersetzungen der neuen Texte und interaktive visuelle Abnahme offen |
| X07 | geprüft (Teilumfang) | `migrations/versions/0007_user_options.py`, `src/neofab2/database.py`, `tests/core/test_user_options.py` | Explizites Upgrade von 0006, Wiederholung, leere Listen ohne Datenübernahme und Readiness-Prüfung auf neue Tabelle bestanden | Nur Testdaten; kein produktives Schema ausgeführt |
| X05, X06, S12 | geprüft (Teilumfang) | `doku/Core_Auswahllisten.md`, `doku/Benutzerverwaltung.md`, `doku/SETUP.md`, `script/README.md`, `doku/Version_Timeline.md`, `src/neofab2/version.py`, `tests/wheel_smoke.py` | 132 Tests, Bash-Syntax, 69 Dokumentationslinks, Wheel/sdist und installiertes Wheel geprüft; Version 0.1.8 | Kein Commit/Push; keine vollständige Core-Abnahme |

Alle übrigen IDs bleiben geplant. U02–U04 (Registrierung/E-Mail-Verfahren),
Benutzerlöschung, weitere Sprachabdeckung und Plugin-Dienste sind offen.
Keine vollständige Core-Abnahme.

Bei jeder abgeschlossenen Umsetzung diesen Nachweis aktualisieren. Versionsänderungen zusätzlich gemäß Projektbeschreibung in `doku/Version_Timeline.md` dokumentieren, einschließlich Commit-Titel und Commit-Beschreibung für den manuellen Commit. Diese Matrix allein ersetzt weder Tests noch die Versionshistorie.
### Nachbesserung 0.1.8 – Stammdaten-Einstieg und Konsolenausgaben (19.09.2026)

| IDs | Status | Umsetzungsnachweis | Prüfungen | Abweichungen/offen |
|---|---|---|---|---|
| U05, S04, S01/S02 | geprüft (Teilumfang) | `src/neofab2/core/user_options.py`, `templates/master_data.html`, `templates/settings.html`, `templates/user_options.html`, `core/i18n.py`, `tests/core/test_user_options.py` | Einstellungen → Stammdaten → drei getrennte Listen/Formulare; Rücklinks, Persistenz/Umbenennung und Zugriffsschutz geprüft | Keine neue Schemaänderung, keine Freitextmigration; visuelle Browserprüfung nicht durchgeführt |
| X01–X04 | geprüft (Teilumfang) | `script/common.sh`, `script/setupNeoFab`, `script/upDateNeoFabService`, `tests/integration/test_script_summaries.py` | Trennlinien, erkannte IPv4-/IPv6-URLs, fehlende IP ohne Platzhalter, ursprüngliche Exit-Codes; alle fünf Shell-Dateien mit `bash -n` geprüft | OS-Aufrufe simuliert; Nutzer bestätigt vorheriges Update auf 0.1.8, neue Nachbesserung noch nicht auf Debian/LXC geprüft |
| X05, X07 | dokumentiert | `script/README.md`, `doku/SETUP.md`, `doku/Core_Auswahllisten.md`, `doku/Version_Timeline.md` | Gesamtsuite: 133 bestanden; nach ergänzter Rechteprüfung Benutzerlisten-Suite erneut: 8 bestanden; `git diff --check` bestanden | Weiterhin Version 0.1.8, kein Commit/Push; keine vollständige Core-Abnahme |

### Buttons und Stammdaten-Navigation 0.1.9 (19.09.2026)

| IDs | Status | Umsetzungsnachweis | Prüfungen | Abweichungen/offen |
|---|---|---|---|---|
| U05, S01, S04 | geprüft (Teilumfang) | `src/neofab2/templates/users.html`, `user_form.html`, `settings.html` | HTML-Prüfung: Stammdaten-Links aus Liste und beiden Benutzerformularen entfernt; Einstellungen mit Stammdaten-Button; bestehende Rechte-/CSRF-Tests bestanden | Keine Schemaänderung; Funktionsrestumfang unverändert |
| S01 | geprüft (HTML/CSS-Teilumfang) | `src/neofab2/templates/ui_icons.html`, `base.html`, weitere Button-Templates, `src/neofab2/plugins/templates/management_test/index.html`, `src/neofab2/static/core.css` | 14 Seiten mit 28 beschrifteten Buttons und dekorativen SVG-Icons geprüft; 133 Gesamttests bestanden | Interaktive visuelle Abnahme offen, kein Browser verbunden; keine vollständige Core-Abnahme |
| S12, X05, X06 | dokumentiert / geprüft (Teilumfang) | `src/neofab2/version.py`, `doku/UI_Gestaltungsregeln.md`, `doku/Version_Timeline.md`, Bedienungs-/Betriebsanleitungen, `README.md` | Version 0.1.9, deutsche Gestaltungsregeln und kopierbarer Commit-Text; temporäre Testdaten ausschließlich im Projekt | Kein Commit/Push, keine Produktivdaten geändert |

### Paket 0 und Administration 0.1.10 (19.09.2026)

| IDs | Status | Umsetzungsnachweis | Prüfungen | Abweichungen/offen |
|---|---|---|---|---|
| N01, U06 | geprüft (Paket 0) | `src/neofab2/plugin_api/__init__.py`, `registry.py`, `src/neofab2/plugins/management_test.py`, `tests/plugin_contract/test_files.py` | Mehrere Rechte, Namespace-/Rollenvalidierung, Besitzer + Eigenrecht, kein Admin-Wildcard, Aktionsrechte, Navigation und bestehende Aktivierungs-/Aufgabensperren; API-1-Altverträge funktionieren | Rollenpflege und weitere Dienstverträge folgen; `staff` unverändert |
| S10, N01 | geprüft (Minimalvertrag) | `src/neofab2/services/files.py`, `plugin_api/files.py`, `plugins/templates/management_test/index.html`, `tests/plugin_contract/test_files.py` | Eigene/fremde Downloads, Mitarbeiter/Admin, Modulfilter, CSRF, frischer Kontostatus, leere/falsche/zu große Dateien, Pfad-/Namensprüfung, Anhang-Header, Neustart und Datenerhalt bei Deaktivierung | Kleine SQLite-BLOBs statt großer Dateisystemablage; TXT-Testplugin bis 256 KiB; keine Inhaltsprüfung, Viewer, Löschung oder fachliche Objektbindung |
| S01, U06 | geprüft (Teilumfang) | `src/neofab2/core/routes.py`, `core/i18n.py`, `templates/base.html`, `administration.html`, `ui_icons.html`, `tests/plugin_contract/test_files.py` | Administrationseinstieg, drei Buttons mit Icons, ausgeblendete direkte Hauptmenülinks, direkter Zugriff für Gäste/Benutzer/Mitarbeiter/Admin geprüft | Interaktive visuelle Browser-Abnahme offen |
| X07 | geprüft (Teilumfang) | `migrations/versions/0008_core_files.py`, `src/neofab2/database.py`, `tests/plugin_contract/test_files.py`, `tests/core/test_foundation.py` | Explizites Upgrade von 0007, Wiederholung, Kontenerhalt, leere Dateitabelle, fehlende Migration nicht bereit; SQLite-Sicherung mit Dateiinhalt geprüft | Nur synthetische Daten; kein Produktivupdate oder echter LXC-Lauf |
| S12, X05, X06 | geprüft (Teilumfang) | `src/neofab2/version.py`, `pyproject.toml`, `doku/Core_Dateien_und_Rechte.md`, `Core_Naechste_Schritte.md`, `Version_Timeline.md`, `script/README.md`, `doku/SETUP.md` | Version 0.1.10; 160 Tests bestanden, Wheel/sdist gebaut, installiertes Wheel einschließlich Administration/Icons/Upload/Download geprüft; `git diff --check` bestanden; Paket 1 als nächster Schritt dokumentiert | Kein Commit/Push; vollständige Core-Abnahme bleibt offen |

### CheckDesign 0.1.0 in NeoFab2 0.1.11 (19.09.2026)

Entscheidung: Auf ausdrücklichen Benutzerauftrag neues technisches Core-Testplugin
zur Designprüfung; kein produktives Fachplugin. Auswahl als Menüpunkt für
Mitarbeiter/Admins, Aktivierung weiterhin durch Administratoren.

| IDs | Status | Umsetzungsnachweis | Prüfungen | Abweichungen/offen |
|---|---|---|---|---|
| S01, U07 | geprüft (Galerie/HTML) | `src/neofab2/plugins/checkdesign.py`, `plugins/templates/checkdesign/index.html`, `plugins/static/checkdesign/gallery.css`, `templates/base.html`, `templates/ui_icons.html` | 15 Designfarben und alle Icons aus gemeinsamen Quellen; Komponenten/Zustände, Beschriftungen und Hilfen; Hell/Dunkel nur im Renderkontext; Konten/Einstellungen unverändert | Keine interaktive visuelle Abnahme, kein Browser verbunden; native Browsercontrols variieren; Themewechsel setzt Beispiele zurück |
| N01, U06 | geprüft (Teilumfang) | `src/neofab2/plugin_api/__init__.py`, `plugins/checkdesign.py`, `tests/plugin_contract/test_checkdesign.py` | API 1, keine Abhängigkeiten, Rollen staff/admin, normale Benutzer 403, Gäste Login, geschützte Assets, Menü und Direktzugriffe nach Deaktivierung/Neustart gesperrt | Keine automatische Aktivierung; technische Galerie, keine Fachfunktionen |
| S02 | geprüft (Teilumfang) | `src/neofab2/core/i18n.py`, `plugins/templates/checkdesign/index.html` | Englische Ausgangstexte, deutsche Bereichs-/Bedienbezeichnungen im gerenderten Plugin geprüft | Weitere Detailtexte und Französisch weiterhin englischer Fallback |
| S12, X05, X06 | geprüft (Teilumfang) | `src/neofab2/version.py`, `plugins/checkdesign.py`, `pyproject.toml`, `tests/wheel_smoke.py`, `doku/CheckDesign.md`, `UI_Gestaltungsregeln.md`, `Version_Timeline.md` | Core 0.1.11, Plugin 0.1.0; 166 Tests bestanden, Wheel/sdist gebaut und installiertes Wheel einschließlich Galerie/Stylesheet geprüft | Keine neue Migration; kein eigener LXC-Lauf, kein Commit/Push; Core-Abnahme weiter offen |

### Planung Plugin-Pakete und Lifecycle (19.09.2026, weiterhin 0.1.11)

Benutzerauftrag: untersuchen, dokumentieren und Schritte einplanen; ausdrücklich
noch keine Implementierung. ZIP-Bereitstellung ist ein künftiger Ausbau des
bisher bewusst geschlossenen Lieferkatalogs, kein bereits verfügbares Merkmal.

| IDs | Status | Zielpfad / Nachweis | Prüfung / Prüfkriterien | Abweichungen/offen |
|---|---|---|---|---|
| X05 | geprüft (Dokumentation) | `doku/Plugin_Pakete_und_Lifecycle.md`, `Core_Naechste_Schritte.md`, `NeoFab2_Projektbeschreibung.md`, `plugin-development.md`, `architecture.md`, `README.md` | Vorhandenen Katalog, Registry-Rechte und Blueprint-Schutz gelesen; Ist/Ziel getrennt, Querverweise und `git diff --check` geprüft | Keine Code-, Schema- oder Versionsänderung; keine Anwendungstests für diesen Dokumentationsnachtrag |
| N01, S10, X03 | geplant (P1) | `doku/Plugin_Pakete_und_Lifecycle.md`, Abschnitte 2/6 | Vollständige Plugin-Ordner samt Icons/Bildern/PDF, gemeinsame Core-Ressourcen, eigene Laufzeitdaten; Paketierung und geschützte Ressourcen als spätere Nachweise | Tatsächliche Verzeichnisse unverändert; endgültige Installationspfade offen |
| U06, S01, S09, N01 | geplant (P2) | dieselbe Spezifikation, Abschnitt 4 | Admin-Auswahl des niedrigsten Levels, hierarchischer Einstieg, getrennte Aktions-/Besitzerrechte, pro Anfrage wirksame Speicherung, sichere Altvertragsübernahme | Noch kein Auswahlfeld oder Rechteumbau; API-/Migrationsentscheidung vor Umsetzung |
| N01, S09/S10, X03/X07 | geplant (P3/P4) | dieselbe Spezifikation, Abschnitt 3 | Manifest/Journal, ZIP-Staging ohne Codeimport, Archivprüfung, kontrollierter Installer, Abhängigkeiten, Migrationen und Wiederherstellung | Vertrauensmodell, Limits und Installerzuständigkeit offen; kein Upload/Installer implementiert |
| N01, N06 als Vertrag, X03/X07 | geplant (P5) | dieselbe Spezifikation, Abschnitt 5 | Deaktivieren/Deinstallieren/Löschen getrennt; Abhängigkeiten/Jobs prüfen, Daten standardmäßig erhalten, Wiederinstallation/Restore | Keine Löschung autorisiert; endgültige Datenbereinigung bleibt gesonderter Auftrag |

### Paket 1: SMTP und Versandaufträge 0.1.12 (19.09.2026)

| IDs | Status | Umsetzungsnachweis | Prüfungen | Abweichungen/offen |
|---|---|---|---|---|
| S05 | geprüft (technischer Umfang) | `src/neofab2/core/mail.py`, `services/mail.py`, `templates/mail.html`, `core/i18n.py`, `tests/core/test_mail.py` | Admin-/CSRF-Schutz, validierte persistente SMTP-Einstellungen, Passwort nur TOML, Testauftrag, Status/Paginierung, DE-Texte und feste Fehlerkategorien; simulierte TLS-/Relay-Transporte einschließlich Hostnamenübergabe | Kein echter SMTP-Anbieter oder Postfacheingang geprüft; keine visuelle Browserabnahme |
| N05, S06 | geprüft (Versandinfrastruktur) | `src/neofab2/services/mail.py`, `src/neofab2/cli.py`, `tests/core/test_mail.py` | Idempotenz, Rollback, Neustart, begrenzte Wiederholung, exklusive parallele Übernahme, ungeklärte Übertragungen, manuelle Bestätigung, Schutz gegen verspätete Ergebnisse, keine Wiederholung angenommener Jobs | S06-Kontoverfahren folgen in Paket 2; CLI läuft einmalig, kein automatisch installierter Scheduler, keine exakt einmalige Zustellgarantie, keine automatische Aufbewahrung/Löschung |
| N01, U06 | geprüft (additiver API-1-Teilumfang) | `src/neofab2/plugin_api/__init__.py`, `registry.py`, `notifications.py`, `tests/core/test_mail.py` | Deklariertes Versandrecht plus Einstieg, kein Admin-Wildcard, frischer Kontostatus, gemeinsame Transaktion, gespeicherte Plugin-Pause verhindert neue Übernahmen ohne Versuchsverbrauch | Nur synthetischer Vertragsfixture, keine produktiven Fachplugins; fachliche Empfänger-/Objektberechtigungen bleiben Plugin-Aufgabe |
| X07 | geprüft (Teilumfang) | `migrations/versions/0009_mail_outbox.py`, `src/neofab2/database.py`, `tests/core/test_mail.py`, `tests/core/test_foundation.py` | Upgrade 0008 → 0009, wiederholte Migration, Bestandswerterhalt, Readiness, SQLite-Sicherung mit wartendem Auftrag und unveränderter Start ohne Schemaanlage | Nur synthetische Daten; kein Produktivupdate oder echter Debian/LXC-Lauf |
| S01, S12, X05, X06 | geprüft / dokumentiert (Teilumfang) | `src/neofab2/version.py`, `templates/settings.html`, `ui_icons.html`, `tests/wheel_smoke.py`, `doku/Core_SMTP_und_Versand.md`, `SETUP.md`, `script/README.md`, `Version_Timeline.md` | Core 0.1.12, Testplugins 0.1.0; 194 Tests einschließlich 28 Versandtests bestanden; Wheel/sdist gebaut, installiertes Wheel geprüft; 120 Dokumentationslinks und Diff geprüft; Paket 2 ist nächster Schritt | P1–P5 bleiben Planung; kein Commit/Push und keine vollständige Core-Abnahme |
