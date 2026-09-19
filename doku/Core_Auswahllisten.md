# Benutzer-Auswahllisten und Feldhilfen – v0.1.13

Umfang: U05, S01/S02, S04 und X07. Position, Studiengang und Kostenstelle sind
optionale Auswahlfelder in den Formularen zum Anlegen und Bearbeiten von Konten.
Die drei Listen werden getrennt im Backend gepflegt. Sie enthalten organisatorische
Benutzerangaben, keine Finanz-/Auftragsverwaltung und keine Fachplugin-Abhängigkeit.

## Listen pflegen

Zentraler Einstieg: **Administration → System settings → Master data** (Deutsch:
**Administration → Systemeinstellungen → Stammdaten**), Adresse `/admin/master-data`.
Die Übersicht verlinkt Positionen, Studiengänge und Kostenstellen jeweils auf
ihre eigene Liste mit Anlage- und Bearbeitungsformular. Weitere Serien können
später eigene Zielseiten erhalten. Seit 0.1.9 ist der Einstieg ein Button mit
Datenbank-Icon; die Direktlinks in Benutzerliste und Benutzerformularen entfallen.

Ausführungsbenutzer: **angemeldeter NeoFab2-Administrator**. Unter **Administration → System settings**
den Button **Master data** und anschließend die gewünschte Liste öffnen:

| Liste | Backend-Adresse | Namensgrenze |
|---|---|---|
| Positions | `/admin/user-options/position` | 1–150 Zeichen |
| Study programs | `/admin/user-options/study_program` | 1–150 Zeichen |
| Cost centers | `/admin/user-options/cost_center` | 1–100 Zeichen |

1. Unter **Add option** einen Namen eingeben. **Active** ist standardmäßig gesetzt.
2. **Save option** betätigen. Der Eintrag erscheint unter **Saved options** und
   steht in beiden Benutzerformularen zur Auswahl.
3. Mit **Edit** Namen oder Aktivstatus ändern. Umbenennen aktualisiert die
   vorhandenen Benutzerzuordnungen derselben Liste in derselben Transaktion.
4. **Active** abwählen, um neue Zuordnungen zu verhindern. Bereits zugeordnete
   Konten behalten den Wert; dort kann er beibehalten, geändert oder geleert werden.

Die Listen starten **leer**, ohne Beispielwerte. **Not specified** ist die leere
Vorgabe im Benutzerformular. Gleiche Namen innerhalb einer Liste werden abgewiesen;
Groß-/Kleinschreibung wird unterschieden. Die gleichen Namen dürfen in verschiedenen
Listen vorkommen. Eingaben werden außen von Leerzeichen bereinigt. HTML wird maskiert.
Es gibt in diesem Arbeitspaket keine Löschfunktion; Deaktivieren erhält Zuordnungen.

Nur `core.users.manage` erlaubt die Verwaltung. Benutzer und Mitarbeiter haben
keinen direkten Zugriff. Schreibzugriffe benötigen CSRF-Schutz; die Rechte und
Auswahlwerte werden innerhalb der Schreibtransaktion geprüft. Manipulierte,
unbekannte oder neu zugeordnete inaktive Werte werden auch per direktem POST
abgewiesen. Ein Fehler verhindert die gesamte Kontospeicherung.

## Speicherung und Update

Die explizite Schema-Revision `0007_user_options` ergänzt ausschließlich die
leere Tabelle `core_user_options` mit Kennung, Listentyp, Name und Aktivstatus.
Die Benutzerzuordnung verwendet weiterhin die vorhandenen Textspalten und wird
im Core gegen die verwalteten Listen geprüft. Umbenennen und Kontospeicherung
werden serialisiert; es wird keine Benutzertabelle neu aufgebaut.

**Auf Benutzerwunsch keine Übernahme bisheriger Freitextwerte.** Es gibt keine
Befüllung aus Altdaten und keine fachliche Datenmigration. Alte Werte werden
nicht als Auswahl angeboten. Beim nächsten Speichern über das Benutzerformular
wird die ausgewählte Option bzw. der leere Wert gespeichert. Die Schemaänderung
erfolgt ausschließlich über den normalen expliziten Migrationsschritt.

Nach manuellem Commit/Push des Stands 0.1.13 als **root im NeoFab2-Testcontainer**:

```bash
bash /opt/neofab2/script/upDateNeoFabService
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version 0.1.13 in der Abschlussübersicht und `Database and schema ready.`.
Anschließend je einen synthetischen Eintrag in allen drei Listen anlegen,
einem Testkonto zuweisen, erneut öffnen und die Auswahl kontrollieren.
Umbenennen und Deaktivieren ebenfalls nur mit synthetischen Daten prüfen.

Fehlerhilfe: Bei leerer Auswahl zuerst unter **Administration → System settings → Master data** einen aktiven
Eintrag anlegen. Bei doppeltem Namen vorhandenen Eintrag bearbeiten. Wird ein
zwischenzeitlich deaktivierter oder umbenannter Wert beim Speichern abgewiesen,
Formular neu laden und Auswahl prüfen. Bei HTTP 503 zuerst die Update-Ausgabe
und `neofab2 check` prüfen; keine Datenbank löschen.

## Englische Feldhilfen und spätere Übersetzung

Login, Sprachwahl, Profil/Passwortwechsel, Benutzerformulare, Systemeinstellungen
und Listenpflege zeigen kurze englische Hinweise direkt am Feld. Eingaben sind
über `aria-describedby` mit den Hinweisen verknüpft. Die neuen Hilfetexte verwenden
bereits die zentrale Übersetzungsfunktion `_()` und englische Ausgangstexte.
Deutsch/Französisch für diese neuen Texte ist noch nicht geliefert; fehlende
Übersetzungen fallen auf Englisch zurück. Später passende Einträge unter den
identischen Schlüsseln in `core/i18n.py` ergänzen. Gespeicherte Listennamen sind
individuelle Daten und werden nicht automatisch übersetzt.
