# Systemeinstellungen und Darstellung – v0.1.13

Seit 0.1.13 führt ein weiterer Button zu [Registrierung und
Kontowiederherstellung](Core_Registrierung_und_Reset.md). Beide Verfahren sind
zunächst abgeschaltet; Freigabe und Domain-Regeln werden dort getrennt von den
öffentlichen Darstellungswerten verwaltet. Aktuelle Schema-Revision:
`0010_account_flows`.

Ab 0.1.7 sind die App und CLI standardmäßig englisch. Deutsche Bezeichnungen
in dieser Anleitung gelten bei gewählter deutscher Kontosprache.
[Sprachwahl und Migration 0006](Core_Sprachen.md).

Umfang: S04/S01 und der Darstellungsteil von U07. Seit 0.1.6 gibt es eine
[Sprachwahl für Navigation, Login und Profil](Core_Sprachen.md). Weitere
Übersetzungen, Import/Export von Einstellungen sowie Impressum/Datenschutz
werden in späteren Core-Schritten ergänzt.

Seit 0.1.12 führt ein eigener Button zur [SMTP-Konfiguration und Versandwarteschlange](Core_SMTP_und_Versand.md).
Diese Werte sind getrennt vom öffentlichen Darstellungsformular; SMTP-Secrets
werden weiterhin ausschließlich in der geschützten TOML-Datei verwaltet.

## Update und Migration

Voraussetzung: Änderungen zu 0.1.13 manuell in GitHub Desktop committen und
auf den verwendeten Remote-Branch übertragen. Danach als **root im Container**:

```bash
bash /opt/neofab2/script/upDateNeoFabService
```

Das Skript sichert den bisherigen Stand und führt fehlende Migrationen bis
`0010_account_flows` aus. Die Darstellungsmigration `0003_user_theme`
ergänzt `core_users.theme`; vorhandene Konten
erhalten `system` (Systemvorgabe). Konten, Passwort-Hashes, Sitzungen und
vorhandene Einstellungen bleiben erhalten. Die vorhandene Tabelle
`core_settings` nimmt die öffentlichen Darstellungswerte auf; kein Umbau nötig.
Weder Anwendungsstart noch Seitenaufrufe führen Schemaänderungen aus.

Ergebnis als root prüfen:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
systemctl status neofab2.service --no-pager
```

Erwartet: Version 0.1.13, `Database and schema ready.`, aktiver Dienst.
Die HTTP-Einstellung `SESSION_COOKIE_SECURE = false` im isolierten Testnetz
und die Plugin-Aktivierung werden durch diesen Schritt nicht verändert.

## Systemeinstellungen verwenden

Als Administrator anmelden und **Administration → Systemeinstellungen** (`/admin/settings`)
öffnen. Das Recht `core.settings.manage` ist ausschließlich Administratoren
zugewiesen; direkter Zugriff von Benutzern/Mitarbeitern wird mit 403 abgewiesen.

| Einstellung | Standard | Grenze / Verwendung |
|---|---|---|
| Werkstattname | NeoFab2 | 1–80 Zeichen, Überschrift der Startseite |
| Kurzbeschreibung | Workshop & Makerspace | 1–160 Zeichen, Kopfzeile |
| Begrüßungstext | The new starting point for our workshop and makerspace. | 1–2000 Zeichen, Startseite; Zeilenumbrüche bleiben sichtbar |
| Standarddarstellung | Dunkel | Hell oder Dunkel; für Gäste und Konten mit Systemvorgabe |

Alle Textfelder sind öffentlich sichtbar. Sie unterstützen Klartext; HTML
wird maskiert. Das NeoFab2-Logo und die technische Versionsanzeige bleiben
Produktkennzeichnungen. Keine Passwort-, SMTP-, Cookie-, Plugin- oder sonstigen
Servereinstellungen über dieses Formular bearbeiten.

Nach **Einstellungen speichern** erscheint eine Bestätigung. Änderungen wirken
mit der nächsten Seitenanfrage, ohne Neustart. Die vier Werte werden gemeinsam
validiert und in einer Transaktion gespeichert; ein ungültiger Wert verhindert
die gesamte Speicherung. Bei paralleler Bearbeitung gilt die zuletzt gespeicherte
Formularfassung. Andere Schlüssel in `core_settings` bleiben unangetastet und
werden nicht an die Oberfläche ausgegeben. Beschädigte bekannte Einzelwerte
fallen bei der Anzeige auf den jeweiligen Standard zurück.

Prüfung: Werkstattname ändern und die Startseite in einem privaten Fenster
öffnen. Der neue Name muss dort erscheinen. Standard auf **Hell** setzen:
Das private Fenster soll jetzt die helle Darstellung verwenden.

## Persönliche Darstellung

Unter **Mein Profil** (`/profile`) stehen **Systemvorgabe**, **Dunkel** und
**Hell** zur Auswahl. **Profil speichern** übernimmt Anzeigename und Darstellung.
Systemvorgabe meint die NeoFab2-Einstellung der Administration, nicht die
Einstellung des Betriebssystems. Standard für vorhandene und neue Konten:
Systemvorgabe; bei unveränderten Systemeinstellungen bleibt die Oberfläche dunkel.

Eine persönliche Auswahl überschreibt die Systemvorgabe und gilt nach erneuter
Anmeldung auch auf anderen Geräten. Sie wird in der Datenbank gespeichert,
nicht nur in einem Browser-Cookie. Der Wechsel beendet keine Sitzung.
Die Darstellung gilt ebenso für die Plugin-Übersicht und das Testplugin,
da diese das gemeinsame Layout verwenden.

Prüfung: Im Profil **Dunkel** wählen, während der Systemstandard **Hell** ist.
Das eigene Konto muss dunkel bleiben, Gäste sehen weiterhin hell. Nach Abmelden
und erneutem Anmelden muss die persönliche Auswahl erhalten sein. Mit
**Systemvorgabe** folgt das Konto wieder dem Admin-Standard.

## Fehlerhilfe

- Menü fehlt: Als aktiver Administrator anmelden; Benutzer und Mitarbeiter
  haben nur ihre persönliche Darstellung im Profil.
- Anzeige bleibt unverändert: Persönliche Auswahl prüfen. Eine feste Auswahl
  überschreibt die Systemvorgabe; außerdem Stylesheet per vollständigem Neuladen
  aktualisieren.
- Schema nicht bereit: Update-Log prüfen. Nach vorhandener Sicherung und bei
  gestopptem Dienst `neofab2 migrate` im dokumentierten Dienstbenutzer-Kontext
  ausführen; keine Spalten manuell ergänzen.
- Ungültige Eingabe: Angegebene Textgrenzen und Auswahlwerte einhalten.
  Unbekannte Formulareinstellungen werden abgewiesen.

Automatisiert geprüft: Rechte, CSRF, Maskierung, Speicherung über App-Neustart,
Isolation fremder Einstellungen/Konten und Upgrade von 0.1.3. Eine interaktive
visuelle Browserprüfung und der Container-Test dieses Schritts stehen noch aus.
