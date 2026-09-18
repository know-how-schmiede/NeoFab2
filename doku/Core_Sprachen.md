# Sprachwahl – v0.1.6

Dieser Nachweis beschreibt den Sprachschritt (S02/U07). Zusätzlich können
Administratoren die Kontosprache in den [Benutzerformularen](Benutzerverwaltung.md) setzen.

## Umgesetzter Umfang

Deutsch, Englisch und Französisch für Navigation, Anmeldeseite, Profil,
Passwortwechsel und zentrale Zugangsfehlermeldungen. Die Administration,
Startseiteninhalte und Plugin-Inhalte sind noch nicht vollständig übersetzt.
Nicht im Katalog vorhandene Texte bleiben deutsch. Öffentlich konfigurierte
Texte werden unverändert ausgegeben und nicht automatisch übersetzt.
CLI und Betriebsanleitungen bleiben deutsch.

Unter `/login` kann ein Gast **Sprache / Language / Langue** wählen und mit
**Sprache übernehmen** bestätigen. Die Auswahl liegt im signierten Sitzungscookie.
Im angemeldeten Zustand gilt die im Konto gespeicherte Sprache. Unter **Mein Profil**
Sprache auswählen und **Profil speichern** betätigen. Nach erneuter Anmeldung
gilt diese Auswahl auch auf anderen Geräten. Eine Gast-Auswahl überschreibt
keine vorhandene Kontosprache. Nach Abmeldung oder eigenem Passwortwechsel
bleibt die zuletzt verwendete Sprache auf der Anmeldeseite erhalten.

Standard ist Deutsch. Unbekannte Sprachwerte werden beim Speichern abgewiesen;
fehlende Übersetzungen und unbekannte gespeicherte Sprachcodes fallen auf Deutsch
zurück. Es wird kein HTML aus Übersetzungstexten ausgeführt. Gast-Sprachwahl
und Profiländerung unterliegen dem CSRF-Schutz.

## Migration und spätere Container-Prüfung

Die explizite Migration `0004_user_locale` ergänzt `core_users.locale` mit
Standard `de`; Konten, Hashes und persönliche Darstellung bleiben erhalten.
Keine Migration beim Seitenaufruf. Das Update erfolgt
das Update über den vertrauten Weg als **root im Container**:

```bash
bash /opt/neofab2/script/upDateNeoFabService
```

Vorher muss der endgültige Stand manuell committed und auf den verwendeten
Remote-Branch übertragen sein.

Prüfablauf nach dem Update:

1. Ohne Anmeldung `/login` öffnen, Englisch wählen: Überschrift **Sign in**.
2. Anmelden und im Profil Französisch speichern: Überschrift **Mon profil**.
3. Abmelden: Anmeldeseite bleibt französisch. Erneut anmelden: Profil bleibt französisch.
4. Auf Deutsch zurückstellen. Benutzer- und Plugin-Rechte müssen unverändert gelten.

Die Attribute aus dem Screenshot sind in beiden Admin-Formularen ergänzt.
Eine vollständige S02-Abnahme
einschließlich aller Admin-Seiten und Plugin-Übersetzungen steht weiterhin aus.
