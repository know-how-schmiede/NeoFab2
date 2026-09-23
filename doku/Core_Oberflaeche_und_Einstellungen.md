# Core-Oberfläche und Einstellungen – 0.1.16

Paket 4 (S01–S04, S08, U06/U07, N01). Nur Core und technische Testplugins.

## Bedienung

Als **Administrator** unter **Administration → Systemeinstellungen → Öffentliche
Inhalte und Zeitzone** die Infoseite, das Impressum und den Datenschutz bearbeiten.
Die Seiten `/info`, `/impressum` und `/datenschutz` sind ohne Anmeldung über den
Fußbereich erreichbar. Standard: leere Inhalte mit sichtbarem Hinweis. Die Infoseite
zeigt zusätzlich Core-Version und lokale Zeit. Veröffentlichung erfolgt mit Speichern;
inhaltlich zutreffende Rechtstexte stellt der Betreiber bereit.

Pro Seite höchstens 20000 Zeichen. Unterstütztes Markdown: Überschriften mit
`#` bis `######`, Absätze/Zeilenumbrüche, `**Fettdruck**` und Listen mit `- `.
HTML wird als Text ausgegeben; Bilder, Links, Tabellen und weitere Markdown-Syntax
werden nicht interpretiert. Diese bewusst kleine Teilmenge benötigt keine optionalen
Renderer und erlaubt keine fremden Skripte oder Bilder. Nach Speichern die öffentliche
Seite als Gast öffnen und Inhalte prüfen. Leere Seiten sind noch keine Rechtstexte.

Zeitzone: standardmäßig **UTC**, alternativ etwa **Europe/Berlin** oder
**America/New_York**. Gültige IANA-Namen verwenden; keine manuelle Stundenverschiebung.
Startseite, Infoseite, Audit und Versand-/Workerzeiten zeigen Datum, UTC-Abstand und
Zonenname. Sommerzeit wird automatisch berücksichtigt. Die angezeigte aktuelle Zeit
ist der Zeitpunkt des Seitenabrufs, keine laufende JavaScript-Uhr. Speicherung und
Audit-Bereinigungsgrenzen bleiben UTC. Kontomails nennen relative Gültigkeitsdauern;
SMTP-Date-Header bleiben standardkonforme absolute Zeiten. Es gibt noch keine
fachlichen Terminexporte. Technischer Formatter: `services/presentation.py`,
`format_datetime(epoch_oder_aware_datetime, zone)`; naive Datetimes werden abgewiesen.

## Einstellungen übertragen

Als **Administrator** auf derselben Seite **Einstellungen exportieren** wählen.
Format: UTF-8-JSON, `format=neofab2-public-settings`, Formatversion **1**.
Exportiert werden ausschließlich:

- Darstellung: Werkstattname, Kurzbeschreibung, Begrüßung, Standarddarstellung.
- Öffentliche Inhalte und Zeitzone.

Kein vollständiges Backup: Benutzer, Rollen, SMTP, Passwörter, Kontoverfahren,
Plugin-Auswahl und Serverkonfiguration sind ausdrücklich nicht enthalten.
Import über **Einstellungen importieren und ersetzen** ersetzt genau diese Werte.
Vorher bei Bedarf einen Export als Rückfall sichern. Kein Import von NeoFab-Dateien.

Maximal **256 KiB**. Alle Felder müssen vorhanden sein; unbekannte Felder, doppelte
JSON-Schlüssel, falsche Typen/Versionen, ungültige Zonen und überschrittene Textlimits
werden zurückgewiesen. Validierung erfolgt vor der gemeinsamen Transaktion; Darstellung,
Inhalte und Audit-Ereignis werden zusammen gespeichert oder vollständig zurückgerollt.
Ein Import löst weder Versand noch Konto-/Plugin-Freischaltungen aus.

Ergebnisprüfung: Seite erneut laden, Startseite und öffentliche Inhalte als Gast
öffnen; erneut exportieren und die Werte vergleichen. „Ungültige Einstellungsdatei“:
frischen NeoFab2-Export verwenden und Format, Felder und Dateigröße prüfen.
Bei abgelaufener Formularsitzung die Seite neu öffnen. Unbekannte Zeitzone: Schreibweise
und installierte Betriebssystem-Zeitzonendaten prüfen; `UTC` bleibt Standard.

## Rollen und Sprache

**Systemeinstellungen → Rollen und Berechtigungen** zeigt die drei bestehenden
Rollen und deren im Prozess geladene Core-/Plugin-Rechte. Rollen werden weiterhin
über **Benutzerverwaltung → Bearbeiten** vergeben. `staff` bedeutet Mitarbeiter;
kein zusätzliches `employee`. Rollenwechsel beenden die bisherigen Sitzungen.
Der letzte aktive Administrator kann nicht herabgestuft oder gesperrt werden.
Die Übersicht hebt weder die Pause eines Plugins noch dessen Objektberechtigungen auf.

Abgrenzung der Rollenpflege für Paket 4: Pflege der Kontozuordnung und transparente
Rechtebündel; keine frei erstellbaren Rollen oder Änderung der vom Plugin deklarierten
Aktionsrechte. Das geplante Mindestzugriffslevel P2 bleibt separat geplant.
Persönliche Sprache und Darstellung werden weiterhin im Profil gespeichert.

Englisch bleibt Quelle und Fallback. Die neuen Oberflächen besitzen deutsche und
französische Texte; der französische Katalog der allgemeinen Systemeinstellungen
wurde ergänzt. Ältere Detail-/Fehlermeldungen und Testgalerie-Texte sind noch teilweise
englisch. Vom Administrator geschriebene öffentliche Inhalte werden nicht automatisch
übersetzt; bei Bedarf mehrsprachig verfassen. Plugins besitzen eigene Kataloge über
[Plugin-Vertrag](plugin-development.md), ohne den Core-Katalog zu überschreiben.

## Update und Prüfung

Keine neue Migration; Schema bleibt **0011_audit_status**. Neue Werte liegen in der
bestehenden `core_settings`-Tabelle unter `core.site.*` und werden erst beim Speichern
angelegt. Vorhandene Installationen behalten ihre Darstellung, UTC und leere Seiten
als sichere Standards. Normaler Updateablauf gemäß [SETUP](SETUP.md).

Als **root**, Befehle ausgeführt durch **neofab2**, Standardpfade:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: **0.1.16**, Schema bereit. Bei fehlendem Schema normalen Update-/Migrationsweg
verwenden; Seitenaufrufe migrieren nicht. Rückfall: vorherigen Export importieren;
bei vollständigem Betriebsrückfall passende Sicherung gemäß [Betrieb](operations.md).

Entwicklungsprüfung als **Repository-Benutzer** nach Einrichtung gemäß SETUP:

```bash
python -m pytest -q
python -m build
```

Automatisierte HTTP-/Sicherheits-/Zeitzonen- und Paketprüfungen sind im
[Umsetzungsnachweis](NeoFab2_Funktionsmatrix.md) erfasst. Interaktive Browserprüfung
in Hell/Dunkel/schmaler Ansicht und echter Debian-/LXC-Lauf bleiben offen;
Paket 4 ist keine vollständige Core-Abnahme.
