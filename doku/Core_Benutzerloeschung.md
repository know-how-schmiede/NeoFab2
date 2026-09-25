# Benutzeraktionen und bestätigte Kontolöschung – 0.1.20

Betroffene Funktions-IDs: S01, U05/U06/U09, N04, S09/S12, X05–X07.

## Bedienung

Als angemeldeter Administrator die Benutzerverwaltung öffnen. Oberhalb der Liste
stehen „Benutzer anlegen“, „Benutzer exportieren“ und „Benutzer importieren“ in
einer gemeinsamen, auf kleinen Bildschirmen umbrechenden Buttonleiste.
Der Exporthinweis bleibt sichtbar; das Exportformat bleibt unverändert.

1. Das gewünschte Konto bearbeiten, deaktivieren und speichern.
2. Erneut bearbeiten und „Benutzer löschen“ wählen. Aktive Konten und das eigene
   Konto sind serverseitig geschützt.
3. Die Sicherheitsabfrage zeigt Name, E-Mail und betroffene Sitzungen, Kontocodes,
   Versanddatensätze und Importzuordnungen. Hinweise sorgfältig prüfen.
4. Erst nach gesetzter Bestätigungs-Checkbox und erneutem Klick auf
   „Benutzer löschen“ erfolgt die Löschung. „Abbrechen“ lässt das Konto bestehen.

Die Bestätigung gilt zehn Minuten und ist an Administrator, Konto und Datenstand
gebunden. Ändert sich der Stand, muss die Vorschau erneut geöffnet werden.
GET-Aufrufe löschen nichts; der abschließende POST benötigt CSRF und Adminrechte.

## Umfang und Grenzen

Gelöscht werden der Kontodatensatz mit Profil/Passwort-Hash, Sitzungen,
Aktivierungs-/Resetcodes, zugehörige Core-Kontomails und kontobezogene
Anmelde-/Selfservice-Begrenzungen. Die Transaktion schreibt `user.deleted` mit
Akteur- und Ziel-ID ins Audit, ohne Profil oder Passwort. Bei Fehlern erfolgt
keine Teillöschung. Audit-Einträge und vorhandene Sicherungen bleiben erhalten.

Importzuordnungen bleiben mit leerer `user_id` erhalten: Derselbe Quellschlüssel
kann das Konto nicht unbemerkt wieder anlegen (`target_deleted`). Andere Quellen
oder eine bewusste manuelle Neuanlage sind keine globale Identitätssperre.
Der Zähler `core.users.id_high_water` verhindert Wiederverwendung gelöschter
Konto-IDs bei Anlage, Registrierung und Import. Lücken in IDs sind beabsichtigt.

Dateibesitz, unbekannte Datenbanktabellen oder Plugins sperren die Löschung.
Auch fremde Versandbezüge und Versand im Status `sending`/`uncertain` blockieren.
Deaktivierte Plugins werden dabei nicht ignoriert. Es gibt keine automatische
Dateilöschung, jährliche Bereinigung oder allgemeine Fachplugin-Lösch-Hooks.
Solche Bezüge brauchen vor einer Erweiterung einen geprüften Fachvertrag.

## Update und Ergebnisprüfung

Neue explizite Migration: `0013_user_deletion` nach `0012_user_import`.
Sie erlaubt leere Ziel-IDs in Importzuordnungen; bestehende Zuordnungen bleiben
bestehen. Anwendung starten legt kein Schema an. Den normalen gesicherten
[Updateablauf](../script/README.md) verwenden; Standardpfade sind `/opt/neofab2`
und `/etc/neofab2/config.toml`. Kein Update oder Löschen produktiver Daten wurde
für diese Umsetzung ausgeführt.

Als **root**, Befehlsausführung durch **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version **0.1.20**, Schema bereit. Danach mit einem synthetischen
Testkonto Buttonleiste, Abbrechen und bestätigte Löschung prüfen.
Bei fehlendem Schema Update/Migration prüfen, nicht Tabellen von Hand ändern.
Bei abgelaufener/geänderter Abfrage neu öffnen. Bei Versandblockade zunächst
Versandstatus klären; bei Datei-/Pluginblockade Referenzen fachlich klären.
Bei Speicherfehlern bleibt das Konto bestehen; Betriebsprotokolle prüfen.

Eine vollständige Sicherung muss Datenbank einschließlich Importmarkierungen
und ID-Zähler enthalten. Ältere Sicherungen können gelöschte Konten wiederherstellen.
Rückmigration auf 0012 wird bei vorhandenen Löschmarkierungen verweigert;
passende vollständige Sicherung und Codeversion nach dem
[Wiederherstellungsverfahren](operations.md) verwenden.

## Prüfungen

405 automatisierte Tests bestanden, davon 26 neue Löschtests: Rechte/CSRF,
Bestätigung/Ablaufzeit/Datenänderung, Rollback, Referenzsperren, Migration,
Wiederimport, ID-Schutz und Sicherungs-Restore mit ausschließlich synthetischen Daten.
Chromium prüft Hell/Dunkel bei 1440 und 390 Pixeln, Buttonhöhen und Umbruch sowie
Abbrechen und bestätigte Löschung (`tests/browser_user_management.py`).
Diese gezielte Browserprüfung ersetzt keine vollständige Core-/LXC-Abnahme.

Optionaler Browser-Test als **Entwicklungsbenutzer** im Projektverzeichnis,
in eigener virtueller Umgebung (Playwright ist keine Laufzeitabhängigkeit):

```bash
python3 -m venv /tmp/neofab2-ui-venv
/tmp/neofab2-ui-venv/bin/pip install -e '.[dev]' playwright
/tmp/neofab2-ui-venv/bin/python -m playwright install chromium
/tmp/neofab2-ui-venv/bin/python tests/browser_user_management.py
```

Erwartet: erfolgreiche Chromium-Meldung; bei fehlenden Browser-Systembibliotheken
zunächst die für die Entwicklungsmaschine benötigten Playwright-Abhängigkeiten
bereitstellen. Kein produktives Konto für diese Prüfung verwenden.
