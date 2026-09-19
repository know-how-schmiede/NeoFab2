"""S02: English source messages; German and French translations."""

from flask import Blueprint, abort, g, has_request_context, redirect, request, session, url_for

LANGUAGES = {"en": "English", "de": "Deutsch", "fr": "Français"}
# English messages are stable lookup keys and the fallback. No HTML.
MESSAGES = {
    "Design preview": {"de": "Designvorschau"},
    "Preview appearance": {"de": "Vorschaudarstellung"},
    "Use current appearance": {"de": "Aktuelle Darstellung verwenden"},
    "Explore the shared interface elements in light and dark appearance.": {"de": "Gemeinsame Oberflächenelemente im hellen und dunklen Design prüfen."},
    "Preview only. Your profile and system settings are not changed. Sample controls do not save or upload data.": {"de": "Nur Vorschau. Profil und Systemeinstellungen bleiben unverändert. Beispiele speichern keine Daten und laden keine Dateien hoch."},
    "Switching appearance reloads the preview and resets sample inputs. Use Tab to inspect focus, hover with the pointer, and hold a button to inspect its pressed state.": {"de": "Der Designwechsel lädt die Vorschau neu und setzt Beispieleingaben zurück. Mit Tab den Fokus prüfen, den Mauszeiger über Elemente bewegen und Buttons für den gedrückten Zustand festhalten."},
    "Design sections": {"de": "Designbereiche"},
    "Typography": {"de": "Typografie"},
    "Colors and surfaces": {"de": "Farben und Flächen"},
    "Buttons and links": {"de": "Buttons und Links"},
    "Icons": {"de": "Icons"},
    "Form controls": {"de": "Formularelemente"},
    "Messages and badges": {"de": "Meldungen und Kennzeichnungen"},
    "Tables and navigation": {"de": "Tabellen und Navigation"},
    "Cards and layout": {"de": "Karten und Layout"},
    "Primary button": {"de": "Primärer Button"},
    "Secondary button": {"de": "Sekundärer Button"},
    "Disabled primary button": {"de": "Deaktivierter primärer Button"},
    "Disabled secondary button": {"de": "Deaktivierter sekundärer Button"},
    "Primary navigation button": {"de": "Primärer Navigationsbutton"},
    "Secondary navigation button": {"de": "Sekundärer Navigationsbutton"},
    "Disabled navigation button": {"de": "Deaktivierter Navigationsbutton"},
    "Text link": {"de": "Textlink"},
    "All shared icons, each with a visible label.": {"de": "Alle gemeinsamen Icons, jeweils mit sichtbarer Beschriftung."},
    "These swatches use the shared theme colors directly.": {"de": "Diese Farbmuster verwenden direkt die gemeinsamen Designfarben."},
    "Sample buttons have no action. Only the appearance controls change this preview.": {"de": "Beispielbuttons führen keine Aktion aus. Nur die Designauswahl ändert die Vorschau."},
    "Try typing, selecting and focusing these sample fields. There is no save action.": {"de": "Eingabe, Auswahl und Fokus an diesen Beispielfeldern prüfen. Es gibt keine Speicheraktion."},
    "Text field": {"de": "Textfeld"},
    "Password field": {"de": "Passwortfeld"},
    "Number": {"de": "Zahl"},
    "Selection": {"de": "Auswahl"},
    "Multiline input": {"de": "Mehrzeilige Eingabe"},
    "Checkbox": {"de": "Kontrollkästchen"},
    "Disabled checkbox": {"de": "Deaktiviertes Kontrollkästchen"},
    "Radio selection": {"de": "Optionsauswahl"},
    "File selection": {"de": "Dateiauswahl"},
    "Local selection only. The file is not uploaded or read.": {"de": "Nur lokale Auswahl. Die Datei wird weder hochgeladen noch gelesen."},
    "Read-only field": {"de": "Schreibgeschütztes Feld"},
    "Disabled field": {"de": "Deaktiviertes Feld"},
    "Invalid field": {"de": "Ungültiges Feld"},
    "Disabled selection": {"de": "Deaktivierte Auswahl"},
    "Additional native browser controls": {"de": "Weitere native Browser-Bedienelemente"},
    "Sample notification: your example action completed.": {"de": "Beispielhinweis: Die Beispielaktion wurde abgeschlossen."},
    "Sample error: this is a visual example, not a real failure.": {"de": "Beispielfehler: Dies ist eine Darstellungsvorlage, kein echter Fehler."},
    "Sample badge": {"de": "Beispielkennzeichnung"},
    "Synthetic records": {"de": "Synthetische Datensätze"},
    "Sample pagination": {"de": "Beispiel-Seitennavigation"},
    "Empty table": {"de": "Leere Tabelle"},
    "Sample card": {"de": "Beispielkarte"},
    "Inspect buttons": {"de": "Buttons prüfen"},
    "Back to top": {"de": "Zurück nach oben"},
    "Administration": {"de": "Administration", "fr": "Administration"},
    "Test files": {"de": "Testdateien", "fr": "Fichiers de test"},
    "Test file": {"de": "Testdatei", "fr": "Fichier de test"},
    "Upload test file": {"de": "Testdatei hochladen", "fr": "Téléverser un fichier de test"},
    "Test file saved.": {"de": "Testdatei gespeichert.", "fr": "Fichier de test enregistré."},
    "No test files available.": {"de": "Keine Testdateien vorhanden.", "fr": "Aucun fichier de test disponible."},
    "Master data": {"de": "Stammdaten", "fr": "Données de référence"},
    "Positions": {"de": "Positionen", "fr": "Postes"},
    "Study programs": {"de": "Studiengänge", "fr": "Programmes d’études"},
    "Cost centers": {"de": "Kostenstellen", "fr": "Centres de coûts"},
    "{label} must contain at most {limit} characters.": {
        "de": "{label} darf höchstens {limit} Zeichen enthalten."
    },
    "{label} must contain 1 to {limit} characters.": {
        "de": "{label} muss 1 bis {limit} Zeichen enthalten."
    },
    "8 to 128 characters. After changing it, sign in again on all devices.": {
        "de": "8 bis 128 Zeichen. Nach der Änderung musst du dich auf allen Geräten neu anmelden.",
        "fr": "De 8 à 128 caractères. Après la modification, reconnectez-vous sur tous vos appareils."
    },
    "A foundation for the next steps.": {
        "de": "Ein Fundament für die nächsten Schritte."
    },
    "Account active": {
        "de": "Konto aktiv"
    },
    "Account disabled. Use --reactivate to explicitly reactivate it.": {
        "de": "Konto deaktiviert. Nur mit --reactivate ausdrücklich wieder aktivieren."
    },
    "Account is not active.": {
        "de": "Konto nicht aktiv."
    },
    "Action": {
        "de": "Aktion"
    },
    "Action unavailable": {
        "de": "Aktion nicht möglich",
        "fr": "Action impossible"
    },
    "Active": {
        "de": "Aktiv"
    },
    "Address": {
        "de": "Adresse"
    },
    "Administrator": {
        "de": "Administrator",
        "fr": "Administrateur"
    },
    "Administrator not found.": {
        "de": "Administrator nicht gefunden."
    },
    "An administrator already exists. Use reset-admin-password if you cannot sign in.": {
        "de": "Ein Administrator existiert bereits. Bei Zugangsproblemen reset-admin-password verwenden."
    },
    "Appearance": {
        "de": "Darstellung",
        "fr": "Apparence"
    },
    "Apply language": {
        "de": "Sprache übernehmen",
        "fr": "Appliquer la langue"
    },
    "BRINGING IDEAS TO LIFE TOGETHER": {
        "de": "GEMEINSAM IDEEN VERWIRKLICHEN"
    },
    "Back to home": {
        "de": "Zur Startseite",
        "fr": "Retour à l’accueil"
    },
    "Back to user list": {
        "de": "Zur Benutzerübersicht"
    },
    "Change password": {
        "de": "Passwort ändern",
        "fr": "Modifier le mot de passe"
    },
    "Contact the workshop administration for an account.": {
        "de": "Deinen Zugang erhältst du von der Werkstatt-Administration.",
        "fr": "Contactez l’administration de l’atelier pour obtenir un compte."
    },
    "Core ready": {
        "de": "Grundsystem bereit"
    },
    "Core test plugin": {
        "de": "Core-Testplugin"
    },
    "Core under development": {
        "de": "Core im Aufbau",
        "fr": "Socle en cours de développement"
    },
    "Cost center": {
        "de": "Kostenstelle"
    },
    "Create user": {
        "de": "Benutzer anlegen"
    },
    "Current password": {
        "de": "Aktuelles Passwort",
        "fr": "Mot de passe actuel"
    },
    "Current selection from the server configuration. Saving for the first time transfers management to the administration panel.": {
        "de": "Bisherige Auswahl aus der Serverkonfiguration. Die erste Speicherung übernimmt die Verwaltung ins Backend."
    },
    "Cyclic plugin dependency:": {
        "de": "Zyklische Plugin-Abhängigkeit:"
    },
    "Dark": {
        "de": "Dunkel",
        "fr": "Sombre"
    },
    "Default appearance": {
        "de": "Standarddarstellung"
    },
    "Dependencies:": {
        "de": "Abhängigkeiten:"
    },
    "Disabled": {
        "de": "Deaktiviert"
    },
    "Display name": {
        "de": "Anzeigename",
        "fr": "Nom affiché"
    },
    "Duplicate dependency:": {
        "de": "Doppelte Abhängigkeit:"
    },
    "Duplicate plugin ID:": {
        "de": "Doppelte Plugin-Kennung:"
    },
    "ENABLED_PLUGINS contains duplicate IDs.": {
        "de": "ENABLED_PLUGINS enthält doppelte Kennungen."
    },
    "ENABLED_PLUGINS must be a list of plugin IDs.": {
        "de": "ENABLED_PLUGINS muss eine Liste von Plugin-Kennungen sein."
    },
    "Edit": {
        "de": "Bearbeiten"
    },
    "Edit user": {
        "de": "Benutzer bearbeiten"
    },
    "Email": {
        "de": "E-Mail",
        "fr": "E-mail"
    },
    "First name": {
        "de": "Vorname"
    },
    "Forgot your password? Please contact the administration.": {
        "de": "Passwort vergessen? Bitte die Administration kontaktieren.",
        "fr": "Mot de passe oublié ? Veuillez contacter l’administration."
    },
    "Home": {
        "de": "Startseite",
        "fr": "Accueil"
    },
    "ID:": {
        "de": "Kennung:"
    },
    "In the running web process:": {
        "de": "Im laufenden Webprozess:"
    },
    "Incompatible plugin API:": {
        "de": "Inkompatible Plugin-API:"
    },
    "Incorrect blueprint namespace:": {
        "de": "Falscher Blueprint-Namensraum:"
    },
    "Initial password (8–128 characters)": {
        "de": "Startpasswort (8–128 Zeichen)"
    },
    "Invalid account status.": {
        "de": "Ungültiger Kontostatus."
    },
    "Invalid plugin ID.": {
        "de": "Ungültige Plugin-Kennung."
    },
    "Invalid plugin contract:": {
        "de": "Ungültiger Plugin-Vertrag:"
    },
    "Invalid plugin task:": {
        "de": "Ungültige Plugin-Aufgabe:"
    },
    "Invalid role or account status.": {
        "de": "Ungültige Rolle oder ungültiger Kontostatus."
    },
    "Language": {
        "de": "Sprache",
        "fr": "Langue"
    },
    "Last name": {
        "de": "Nachname"
    },
    "Leave both password fields empty to keep the current password. Changes to the password, email, role or account status end all existing sessions for this account. The last active administrator remains protected.": {
        "de": "Beide Passwortfelder leer lassen, um das bisherige Passwort beizubehalten. Änderungen an Passwort, E-Mail, Rolle oder Aktivstatus beenden alle bisherigen Sitzungen dieses Kontos. Der letzte aktive Administrator bleibt geschützt."
    },
    "Light": {
        "de": "Hell",
        "fr": "Clair"
    },
    "Main navigation": {
        "de": "Hauptnavigation",
        "fr": "Navigation principale"
    },
    "Management test plugin": {
        "de": "Verwaltungs-Testplugin"
    },
    "Management test plugin: task completed successfully.": {
        "de": "Verwaltungs-Testplugin: Aufgabe erfolgreich ausgeführt."
    },
    "Management test successful: protected form submitted.": {
        "de": "Verwaltungstest erfolgreich: Geschützter Formularaufruf ausgeführt."
    },
    "My profile": {
        "de": "Mein Profil",
        "fr": "Mon profil"
    },
    "Name": {
        "de": "Name"
    },
    "NeoFab2 home": {
        "de": "NeoFab2 Startseite",
        "fr": "Accueil NeoFab2"
    },
    "New password": {
        "de": "Neues Passwort",
        "fr": "Nouveau mot de passe"
    },
    "New password (optional, 8–128 characters)": {
        "de": "Neues Passwort (optional, 8–128 Zeichen)"
    },
    "Next": {
        "de": "Weiter"
    },
    "No plugins installed.": {
        "de": "Keine Plugins installiert."
    },
    "Note": {
        "de": "Notiz"
    },
    "Notice": {
        "de": "Hinweis",
        "fr": "Information"
    },
    "Open sign-in page": {
        "de": "Anmeldung neu öffnen",
        "fr": "Ouvrir la page de connexion"
    },
    "Password": {
        "de": "Passwort",
        "fr": "Mot de passe"
    },
    "Password changed. Please sign in again; all previous sessions have ended.": {
        "de": "Passwort geändert. Bitte neu anmelden; alle bisherigen Sitzungen wurden beendet.",
        "fr": "Mot de passe modifié. Veuillez vous reconnecter ; toutes les sessions précédentes ont été fermées."
    },
    "Permission:": {
        "de": "Recht:"
    },
    "Please enter a valid email address.": {
        "de": "Bitte eine gültige E-Mail-Adresse eingeben."
    },
    "Please select a valid appearance.": {
        "de": "Bitte eine gültige Darstellung wählen.",
        "fr": "Veuillez choisir une apparence valide."
    },
    "Please select a valid default appearance.": {
        "de": "Bitte eine gültige Standarddarstellung wählen."
    },
    "Please select a valid language.": {
        "de": "Bitte eine gültige Sprache wählen.",
        "fr": "Veuillez choisir une langue valide."
    },
    "Plugin entry page missing:": {
        "de": "Plugin-Einstiegsseite fehlt:"
    },
    "Plugin is not active; task was not executed.": {
        "de": "Plugin ist nicht aktiv; Aufgabe nicht ausgeführt."
    },
    "Plugin not installed:": {
        "de": "Plugin nicht installiert:"
    },
    "Plugin selection saved. Changes take effect when the application processes next start.": {
        "de": "Plugin-Auswahl gespeichert. Änderungen werden beim nächsten Start der Anwendungsprozesse übernommen."
    },
    "Plugin version must use MAJOR.MINOR.PATCH.": {
        "de": "Plugin-Version muss MAJOR.MINOR.PATCH sein."
    },
    "Plugin {key} requires enabled plugin {dep}.": {
        "de": "Plugin {key} benötigt aktiviertes Plugin {dep}."
    },
    "Plugin {key} requires {dep} version {dependency.minimum_version} or later.": {
        "de": "Plugin {key} benötigt {dep} ab {dependency.minimum_version}."
    },
    "Plugins": {
        "de": "Plugins",
        "fr": "Extensions"
    },
    "Position": {
        "de": "Position"
    },
    "Previous": {
        "de": "Zurück"
    },
    "Profile saved.": {
        "de": "Profil gespeichert.",
        "fr": "Profil enregistré."
    },
    "Provide the initial password personally through a secure channel. No email is sent.": {
        "de": "Das Startpasswort über einen sicheren Weg persönlich übergeben. Es wird keine E-Mail verschickt."
    },
    "Repeat initial password": {
        "de": "Startpasswort wiederholen"
    },
    "Repeat new password": {
        "de": "Neues Passwort wiederholen",
        "fr": "Confirmer le nouveau mot de passe"
    },
    "Restart pending": {
        "de": "Neustart ausstehend"
    },
    "Restart required.": {
        "de": "Neustart erforderlich."
    },
    "Role": {
        "de": "Rolle"
    },
    "Salutation": {
        "de": "Anrede"
    },
    "Save changes": {
        "de": "Änderungen speichern"
    },
    "Save profile": {
        "de": "Profil speichern",
        "fr": "Enregistrer le profil"
    },
    "Save settings": {
        "de": "Einstellungen speichern"
    },
    "Saved selection:": {
        "de": "Gespeicherte Auswahl:"
    },
    "Schedule activation": {
        "de": "Aktivierung vormerken"
    },
    "Schedule deactivation": {
        "de": "Deaktivierung vormerken"
    },
    "Selection saved in the administration panel.": {
        "de": "Auswahl im Backend gespeichert."
    },
    "Settings must contain text.": {
        "de": "Einstellungen müssen Text enthalten."
    },
    "Setup is not complete yet. Please contact the administration.": {
        "de": "Die Einrichtung ist noch nicht abgeschlossen. Bitte wende dich an die Administration."
    },
    "Setup pending": {
        "de": "Einrichtung ausstehend"
    },
    "Short description": {
        "de": "Kurzbeschreibung"
    },
    "Sign in": {
        "de": "Anmelden",
        "fr": "Se connecter"
    },
    "Sign out": {
        "de": "Abmelden",
        "fr": "Se déconnecter"
    },
    "Staff": {
        "de": "Mitarbeiter",
        "fr": "Personnel"
    },
    "Status": {
        "de": "Status"
    },
    "Study program": {
        "de": "Studiengang"
    },
    "System default": {
        "de": "Systemvorgabe",
        "fr": "Valeur par défaut du système"
    },
    "System settings": {
        "de": "Systemeinstellungen",
        "fr": "Paramètres du système"
    },
    "System settings saved.": {
        "de": "Systemeinstellungen gespeichert."
    },
    "Test form access": {
        "de": "Formularzugriff testen"
    },
    "Test plugin: task completed successfully.": {
        "de": "Testplugin: Aufgabe erfolgreich ausgeführt."
    },
    "The core is running. Sign in with your workshop account to manage your profile.": {
        "de": "Das Grundsystem ist gestartet. Melde dich mit deinem Werkstattkonto an, um dein Profil zu verwalten."
    },
    "The current password is incorrect.": {
        "de": "Das aktuelle Passwort ist nicht korrekt.",
        "fr": "Le mot de passe actuel est incorrect."
    },
    "The display name must contain 1 to 100 characters.": {
        "de": "Der Anzeigename muss 1 bis 100 Zeichen enthalten.",
        "fr": "Le nom affiché doit contenir de 1 à 100 caractères."
    },
    "The form session has expired or is invalid. Reopen the sign-in page and try again.": {
        "de": "Die Formularsitzung ist abgelaufen oder ungültig. Bitte die Anmeldung neu öffnen und erneut versuchen.",
        "fr": "La session du formulaire a expiré ou n’est pas valide. Rouvrez la page de connexion et réessayez."
    },
    "The form session is missing. Allow cookies for this site and reopen the sign-in page. For an HTTP test connection, the administration must check the cookie setting; secure cookies require HTTPS.": {
        "de": "Die Sitzung zum Formular fehlt. Bitte Cookies für diese Website zulassen und die Anmeldung neu öffnen. Bei einem HTTP-Testzugang muss die Administration die Cookie-Einstellung prüfen; sichere Cookies benötigen HTTPS.",
        "fr": "La session du formulaire est absente. Autorisez les cookies pour ce site et rouvrez la page de connexion. Pour un accès de test HTTP, l’administration doit vérifier le réglage des cookies ; les cookies sécurisés nécessitent HTTPS."
    },
    "The last active administrator cannot be disabled or demoted.": {
        "de": "Der letzte aktive Administrator kann nicht deaktiviert oder herabgestuft werden."
    },
    "The new passwords do not match.": {
        "de": "Die neuen Passwörter stimmen nicht überein.",
        "fr": "Les nouveaux mots de passe ne correspondent pas."
    },
    "The new starting point for our workshop and makerspace.": {
        "de": "Der neue Ausgangspunkt für unsere Werkstatt und unseren Makerspace."
    },
    "The password must contain 8 to 128 characters.": {
        "de": "Das Passwort muss 8 bis 128 Zeichen enthalten.",
        "fr": "Le mot de passe doit contenir de 8 à 128 caractères."
    },
    "The passwords do not match.": {
        "de": "Die Passwörter stimmen nicht überein."
    },
    "The plugin is working. Your account has the required access permission.": {
        "de": "Der Plugin-Aufruf funktioniert. Dein Konto besitzt das erforderliche Zugriffsrecht."
    },
    "The saved plugin selection is invalid. Use the local recovery command.": {
        "de": "Gespeicherte Plugin-Auswahl ist ungültig. Lokalen Wiederherstellungsbefehl verwenden."
    },
    "The saved plugin selection must contain unique plugin IDs.": {
        "de": "Gespeicherte Plugin-Auswahl muss eindeutige Plugin-Kennungen enthalten."
    },
    "The saved selection differs from the running web process. Ask the Proxmox administrator to restart the container manually. This page does not trigger a restart.": {
        "de": "Die gespeicherte Auswahl weicht vom laufenden Webprozess ab. Bitte den Proxmox-Admin bitten, den Container manuell neu zu starten. Diese Seite löst keinen Neustart aus."
    },
    "The saved selection takes effect after a restart. Until then, plugins continue in their current state.": {
        "de": "Die gespeicherte Auswahl gilt nach dem Neustart. Bis dahin laufen Plugins in ihrem bisherigen Zustand weiter."
    },
    "The selection matches this web process. After changes, all application processes must be restarted; a container restart by the Proxmox administrator restarts them all.": {
        "de": "Die Auswahl stimmt mit diesem Webprozess überein. Nach Änderungen müssen alle Anwendungsprozesse neu gestartet werden; ein Container-Neustart durch den Proxmox-Admin übernimmt dies vollständig."
    },
    "The system is not ready yet. Please contact the administration.": {
        "de": "Das System ist noch nicht bereit. Bitte die Administration informieren.",
        "fr": "Le système n’est pas encore prêt. Veuillez contacter l’administration."
    },
    "The test only displays a confirmation; no business data is created.": {
        "de": "Der Test zeigt nur eine Bestätigung; es werden keine Fachdaten angelegt."
    },
    "These details appear on the public home page. The default appearance applies to guests and accounts without a personal preference.": {
        "de": "Diese Angaben erscheinen auf der öffentlichen Startseite. Die Standarddarstellung gilt für Gäste und Konten ohne eigene Auswahl."
    },
    "This additional test plugin requires the core test plugin. It checks activation, dependencies and protected forms.": {
        "de": "Dieses zusätzliche Testplugin benötigt das Core-Testplugin. Es prüft die Aktivierung, Abhängigkeiten und geschützte Formulare."
    },
    "This email address is already in use.": {
        "de": "Diese E-Mail-Adresse wird bereits verwendet."
    },
    "This test page checks the core extension. It does not store business data.": {
        "de": "Diese Testseite prüft die Core-Erweiterung. Sie speichert keine Fachdaten."
    },
    "Unable to sign in. Check your credentials or try again later.": {
        "de": "Anmeldung nicht möglich. Zugangsdaten prüfen oder später erneut versuchen.",
        "fr": "Connexion impossible. Vérifiez vos identifiants ou réessayez plus tard."
    },
    "Unknown or missing system setting.": {
        "de": "Unbekannte oder fehlende Systemeinstellung."
    },
    "Unknown plugin or invalid action.": {
        "de": "Unbekanntes Plugin oder ungültige Aktion."
    },
    "Unknown plugin task.": {
        "de": "Unbekannte Plugin-Aufgabe."
    },
    "Unknown role.": {
        "de": "Unbekannte Rolle."
    },
    "Unknown user attribute.": {
        "de": "Unbekanntes Benutzerattribut."
    },
    "User": {
        "de": "Benutzer",
        "fr": "Utilisateur"
    },
    "User accounts · Page": {
        "de": "Benutzerkonten · Seite"
    },
    "User created. Provide the initial password personally through a secure channel.": {
        "de": "Benutzer angelegt. Das Startpasswort persönlich über einen sicheren Weg übergeben."
    },
    "User management": {
        "de": "Benutzerverwaltung",
        "fr": "Gestion des utilisateurs"
    },
    "User not found.": {
        "de": "Benutzer nicht gefunden."
    },
    "User pages": {
        "de": "Benutzerseiten"
    },
    "User saved. Changes to credentials, role or account status end existing sessions.": {
        "de": "Benutzer gespeichert. Geänderte Zugangsdaten, Rolle oder Kontostatus beenden bisherige Sitzungen."
    },
    "Welcome text": {
        "de": "Begrüßungstext"
    },
    "Welcome to": {
        "de": "Willkommen bei"
    },
    "Welcome to {site_name}.": {
        "de": "Willkommen bei {site_name}."
    },
    "Workshop & Makerspace": {
        "de": "Werkstatt & Makerspace"
    },
    "Workshop name": {
        "de": "Werkstattname"
    },
    "Workshops and manufacturing areas will follow as separate extensions.": {
        "de": "Workshops und Fertigungsbereiche folgen später als eigenständige Erweiterungen."
    },
    "You do not have permission for this action.": {
        "de": "Für diese Aktion fehlt die Berechtigung.",
        "fr": "Vous n’avez pas l’autorisation d’effectuer cette action."
    },
    "You do not have permission to manage plugins.": {
        "de": "Keine Berechtigung zur Plugin-Verwaltung."
    },
    "You do not have permission to manage system settings.": {
        "de": "Keine Berechtigung für Systemeinstellungen."
    },
    "You do not have permission to manage users.": {
        "de": "Keine Berechtigung zur Benutzerverwaltung."
    },
    "You do not have permission to view this page.": {
        "de": "Für diese Seite fehlt die Berechtigung.",
        "fr": "Vous n’avez pas l’autorisation de consulter cette page."
    },
    "create": {
        "de": "anlegen"
    },
    "edit": {
        "de": "bearbeiten"
    },
    "from": {
        "de": "ab"
    },
    "none": {
        "de": "keine"
    }
}

bp = Blueprint("language", __name__)


def current_language():
    if not has_request_context():
        return "en"
    user = g.get("current_user")
    value = user["locale"] if user else session.get("locale", "en")
    return value if value in LANGUAGES else "en"


def translate(message, **values):
    language = current_language()
    translated = MESSAGES.get(message, {}).get(language, message)
    return translated.format(**values) if values else translated


@bp.post("/language")
def choose_language():
    value = request.form.get("locale")
    if value not in LANGUAGES:
        abort(400)
    if g.get("current_user"):
        return redirect(url_for("accounts.profile"))
    session["locale"] = value
    return redirect(url_for("accounts.login"))


def register_i18n(app):
    app.register_blueprint(bp)

    @app.context_processor
    def language_context():
        return {"_": translate, "locale": current_language(), "languages": LANGUAGES}
