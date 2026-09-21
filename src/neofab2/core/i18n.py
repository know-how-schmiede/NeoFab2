"""S02: English source messages; German and French translations."""

from flask import Blueprint, abort, g, has_request_context, redirect, request, session, url_for

LANGUAGES = {"en": "English", "de": "Deutsch", "fr": "Français"}
# English messages are stable lookup keys and the fallback. No HTML.
MESSAGES = {
    "access.denied": {"de": "Zugriff mangels Berechtigung verweigert"},
    "user.role_changed": {"de": "Kontorolle geändert"},
    "user.enabled": {"de": "Konto freigegeben"},
    "user.disabled": {"de": "Konto gesperrt"},
    "password.admin_reset": {"de": "Passwort administrativ neu gesetzt"},
    "Audit log": {"de": "Audit-Protokoll"},
    "Operational status": {"de": "Betriebsstatus"},
    "Events contain identifiers only, without passwords, tokens or message contents. Times are UTC.": {"de": "Ereignisse enthalten nur Kennungen, keine Passwörter, Tokens oder Nachrichteninhalte. Zeiten sind UTC."},
    "Event": {"de": "Ereignis"},
    "All events": {"de": "Alle Ereignisse"},
    "Filter": {"de": "Filtern"},
    "Time (UTC)": {"de": "Zeit (UTC)"},
    "Actor ID": {"de": "Ausführendes Konto (ID)"},
    "Target ID": {"de": "Ziel (ID)"},
    "Count": {"de": "Anzahl"},
    "No events found.": {"de": "Keine Ereignisse gefunden."},
    "Audit retention: preview and explicit cleanup through the local audit-prune command; default 180 days. No automatic deletion.": {"de": "Aufbewahrung: Vorschau und ausdrückliche Bereinigung über den lokalen Befehl audit-prune; Standard 180 Tage. Keine automatische Löschung."},
    "Core version": {"de": "Core-Version"},
    "Database schema": {"de": "Datenbankschema"},
    "Ready": {"de": "Bereit"},
    "Last observed mail worker": {"de": "Zuletzt beobachteter Versandworker"},
    "Started (UTC)": {"de": "Beginn (UTC)"},
    "Finished (UTC)": {"de": "Ende (UTC)"},
    "Worker observations do not confirm timer activation or mailbox delivery. No observation for over five minutes is marked stale. Reload to refresh.": {"de": "Die Worker-Beobachtung bestätigt weder Timer-Aktivierung noch Postfacheingang. Nach über fünf Minuten ohne Beobachtung wird der Stand als veraltet markiert. Zum Aktualisieren Seite neu laden."},
    "Saved plugin selection is invalid. Use local recovery.": {"de": "Gespeicherte Plugin-Auswahl ist ungültig. Lokale Wiederherstellung verwenden."},
    "Plugin selection changed. Restart web and worker processes.": {"de": "Plugin-Auswahl geändert. Web- und Worker-Prozesse neu starten."},
    "Loaded in this process": {"de": "In diesem Prozess geladen"},
    "Selected for next start": {"de": "Für nächsten Start ausgewählt"},
    "enabled": {"de": "Aktiviert"},
    "paused": {"de": "Pausiert"},
    "invalid": {"de": "Ungültig"},
    "never": {"de": "Noch kein Lauf beobachtet"},
    "running": {"de": "Läuft"},
    "finished": {"de": "Lauf beendet"},
    "failed": {"de": "Fehlgeschlagen"},
    "stale": {"de": "Beobachtung veraltet"},
    "queued": {"de": "Wartend"},
    "sending": {"de": "In Bearbeitung"},
    "retry": {"de": "Wiederholung geplant"},
    "sent": {"de": "Vom SMTP-Server angenommen"},
    "uncertain": {"de": "Ungeklärt"},
    "login.succeeded": {"de": "Anmeldung erfolgreich"},
    "login.failed": {"de": "Anmeldung fehlgeschlagen"},
    "logout": {"de": "Abmeldung"},
    "user.created": {"de": "Konto angelegt"},
    "user.updated": {"de": "Konto administrativ geändert"},
    "password.changed": {"de": "Passwort geändert"},
    "password.emergency_reset": {"de": "Lokaler Notfall-Passwort-Reset"},
    "account.activated": {"de": "Konto aktiviert"},
    "account.reset": {"de": "Passwort per Code zurückgesetzt"},
    "settings.changed": {"de": "Systemeinstellungen geändert"},
    "smtp.changed": {"de": "SMTP-Einstellungen geändert"},
    "accounts.changed": {"de": "Kontoverfahren geändert"},
    "plugins.changed": {"de": "Plugin-Auswahl geändert"},
    "plugins.recovered": {"de": "Plugin-Auswahl lokal wiederhergestellt"},
    "audit.pruned": {"de": "Audit-Protokoll bereinigt"},
    "Account registration and recovery": {"de": "Registrierung und Kontowiederherstellung"},
    "Register": {"de": "Registrieren", "fr": "S’inscrire"},
    "Forgot password": {"de": "Passwort vergessen", "fr": "Mot de passe oublié"},
    "Request a new activation code": {"de": "Neuen Aktivierungscode anfordern", "fr": "Demander un nouveau code d’activation"},
    "Activate account": {"de": "Konto aktivieren", "fr": "Activer le compte"},
    "Reset password": {"de": "Passwort zurücksetzen", "fr": "Réinitialiser le mot de passe"},
    "New accounts always require email activation and receive the User role. The password is set during activation.": {"de": "Neue Konten müssen per E-Mail aktiviert werden und erhalten die Rolle Benutzer. Das Passwort wird bei der Aktivierung festgelegt."},
    "Public site URL:": {"de": "Öffentliche Website-Adresse:"},
    "Not configured": {"de": "Nicht konfiguriert"},
    "Configure PUBLIC_BASE_URL in the protected server configuration and enable SMTP before enabling these services. Email is sent by the separate mail worker.": {"de": "Vor der Freischaltung PUBLIC_BASE_URL in der geschützten Serverkonfiguration hinterlegen und SMTP aktivieren. E-Mails werden vom separaten Versandworker verschickt."},
    "Allow self-registration": {"de": "Selbstregistrierung erlauben"},
    "Allow email password reset": {"de": "Passwort-Rücksetzung per E-Mail erlauben"},
    "Explicitly allow all email domains": {"de": "Ausdrücklich alle E-Mail-Domains erlauben"},
    "Allowed email domains": {"de": "Erlaubte E-Mail-Domains"},
    "Enter at most 100 exact domains, one per line, for example example.org. Subdomains need their own entry. This restriction applies to registration, not to existing accounts requesting a reset.": {"de": "Höchstens 100 genaue Domains, eine pro Zeile, etwa example.org. Subdomains benötigen einen eigenen Eintrag. Diese Einschränkung gilt für die Registrierung, nicht für das Zurücksetzen bestehender Konten."},
    "Changing registration rules invalidates pending activation codes. Disabling password reset invalidates pending reset codes. Accounts remain stored.": {"de": "Geänderte Registrierungsregeln machen offene Aktivierungscodes ungültig. Abschalten der Passwort-Rücksetzung macht offene Rücksetzcodes ungültig. Konten bleiben gespeichert."},
    "Save account settings": {"de": "Kontoeinstellungen speichern"},
    "Account settings saved.": {"de": "Kontoeinstellungen gespeichert."},
    "Invalid account settings.": {"de": "Ungültige Kontoeinstellungen."},
    "Enter at most 100 exact email domains, one per line.": {"de": "Höchstens 100 genaue E-Mail-Domains eingeben, eine pro Zeile."},
    "Enter exact email domains without wildcards or URLs.": {"de": "Genaue E-Mail-Domains ohne Platzhalter oder URLs eingeben."},
    "Choose allowed domains or explicitly allow all domains before enabling registration.": {"de": "Vor der Freischaltung erlaubte Domains festlegen oder ausdrücklich alle Domains erlauben."},
    "Configure PUBLIC_BASE_URL and enable SMTP before enabling account emails.": {"de": "Vor der Freischaltung der Konto-E-Mails PUBLIC_BASE_URL konfigurieren und SMTP aktivieren."},
    "You will receive an activation code by email. Set your password when activating your account.": {"de": "Sie erhalten einen Aktivierungscode per E-Mail. Legen Sie Ihr Passwort bei der Aktivierung fest.", "fr": "Vous recevrez un code d’activation par e-mail. Définissez votre mot de passe lors de l’activation."},
    "Use an address you can access. Delivery may take a few minutes. Check your spam folder.": {"de": "Verwenden Sie eine Adresse, auf die Sie Zugriff haben. Die Zustellung kann einige Minuten dauern. Prüfen Sie auch den Spamordner.", "fr": "Utilisez une adresse à laquelle vous avez accès. La livraison peut prendre quelques minutes. Vérifiez vos courriers indésirables."},
    "Request email": {"de": "E-Mail anfordern", "fr": "Demander un e-mail"},
    "Account access": {"de": "Kontozugang", "fr": "Accès au compte"},
    "I already have a code": {"de": "Ich habe bereits einen Code", "fr": "J’ai déjà un code"},
    "Code from the email": {"de": "Code aus der E-Mail", "fr": "Code reçu par e-mail"},
    "Copy the complete code from the email. Activation codes expire after 24 hours; reset codes after 30 minutes. Each code can be used only once.": {"de": "Kopieren Sie den vollständigen Code aus der E-Mail. Aktivierungscodes gelten 24 Stunden, Rücksetzcodes 30 Minuten. Jeder Code ist nur einmal verwendbar.", "fr": "Copiez le code complet de l’e-mail. Les codes d’activation expirent après 24 heures, ceux de réinitialisation après 30 minutes. Chaque code est à usage unique."},
    "Use 8 to 128 characters. Your password is never sent by email.": {"de": "Verwenden Sie 8 bis 128 Zeichen. Ihr Passwort wird niemals per E-Mail versendet.", "fr": "Utilisez entre 8 et 128 caractères. Votre mot de passe n’est jamais envoyé par e-mail."},
    "Request a new code": {"de": "Neuen Code anfordern", "fr": "Demander un nouveau code"},
    "If the address is eligible, an email will be queued. Check your inbox or try again later.": {"de": "Wenn die Adresse berechtigt ist, wird eine E-Mail eingeplant. Prüfen Sie Ihr Postfach oder versuchen Sie es später erneut.", "fr": "Si l’adresse est éligible, un e-mail sera mis en attente. Consultez votre boîte de réception ou réessayez plus tard."},
    "This code is invalid, expired or already used. Please request a new code.": {"de": "Dieser Code ist ungültig, abgelaufen oder bereits verwendet. Bitte fordern Sie einen neuen Code an.", "fr": "Ce code est invalide, expiré ou déjà utilisé. Demandez un nouveau code."},
    "This account service is currently disabled. Contact the administration.": {"de": "Dieser Kontodienst ist derzeit abgeschaltet. Wenden Sie sich an die Administration.", "fr": "Ce service est actuellement désactivé. Contactez l’administration."},
    "Your password is set. Please sign in; all previous sessions have ended.": {"de": "Ihr Passwort ist festgelegt. Bitte melden Sie sich an; alle bisherigen Sitzungen wurden beendet.", "fr": "Votre mot de passe est défini. Connectez-vous ; toutes les sessions précédentes ont été fermées."},
    "Awaiting email activation": {"de": "Wartet auf E-Mail-Aktivierung"},
    "This account is awaiting email activation. Saving this form ends that procedure and applies the administrator-selected active or disabled status. Set an initial password if activating it here.": {"de": "Dieses Konto wartet auf E-Mail-Aktivierung. Speichern beendet dieses Verfahren und übernimmt den hier gewählten aktiven oder gesperrten Status. Beim Aktivieren hier ein Anfangspasswort setzen."},
    "Set an initial password when activating a pending account as administrator.": {"de": "Beim administrativen Aktivieren eines wartenden Kontos ein Anfangspasswort setzen."},
    "Account request expired or no longer valid": {"de": "Kontoanfrage abgelaufen oder nicht mehr gültig"},
    "SMTP & mail queue": {"de": "SMTP & Versandaufträge"},
    "Messages are stored and sent by the worker. Saving settings does not send an email.": {"de": "Nachrichten werden gespeichert und vom Worker versendet. Speichern allein versendet keine E-Mail."},
    "Enable sending": {"de": "Versand aktivieren"},
    "SMTP host": {"de": "SMTP-Host"},
    "Server name without URL or credentials, for example smtp.example.org.": {"de": "Servername ohne URL oder Zugangsdaten, beispielsweise smtp.example.org."},
    "Transport": {"de": "Transport"},
    "STARTTLS (usually port 587)": {"de": "STARTTLS (üblicherweise Port 587)"},
    "TLS (usually port 465)": {"de": "TLS (üblicherweise Port 465)"},
    "Unencrypted, without authentication": {"de": "Unverschlüsselt, ohne Anmeldung"},
    "TLS verifies the server certificate. Unencrypted transport is intended only for a trusted local relay.": {"de": "TLS prüft das Serverzertifikat. Unverschlüsselter Transport ist nur für ein vertrauenswürdiges lokales Relay vorgesehen."},
    "Sender address": {"de": "Absenderadresse"},
    "SMTP username": {"de": "SMTP-Benutzername"},
    "Optional. Store the password as SMTP_PASSWORD in the protected server configuration; then restart the web service and worker. Password configured:": {"de": "Optional. Das Passwort wird als SMTP_PASSWORD in der geschützten Serverkonfiguration hinterlegt; danach Webdienst und Worker neu starten. Passwort vorhanden:"},
    "Save SMTP settings": {"de": "SMTP-Einstellungen speichern"},
    "Test email": {"de": "Testversand"},
    "Sending is paused. Jobs remain stored.": {"de": "Der Versand ist pausiert. Aufträge bleiben gespeichert."},
    "Test recipient": {"de": "Empfänger des Tests"},
    "Creates a test job. Automatic sending requires the mail timer installed by service setup. Reload this page to check the result.": {"de": "Erstellt einen Testauftrag. Automatischer Versand benötigt den durch die Service-Einrichtung installierten Versandtimer. Seite neu laden, um das Ergebnis zu prüfen."},
    "Queue test email": {"de": "Testnachricht einplanen"},
    "Mail queue": {"de": "Versandaufträge"},
    "Accepted means the SMTP server has taken over the message; it is not a receipt from the recipient. Times are UTC.": {"de": "„Angenommen“ bedeutet: Der SMTP-Server hat die Nachricht übernommen. Es ist keine Bestätigung des Empfängers. Zeiten sind UTC."},
    "Queued": {"de": "Wartend"},
    "Sending": {"de": "In Bearbeitung"},
    "Retry scheduled": {"de": "Wiederholung geplant"},
    "Accepted": {"de": "Angenommen"},
    "Failed": {"de": "Fehlgeschlagen"},
    "Uncertain": {"de": "Ungeklärt"},
    "Worker interrupted": {"de": "Worker unterbrochen"},
    "SMTP result unknown": {"de": "SMTP-Ergebnis unbekannt"},
    "Password missing": {"de": "Passwort fehlt"},
    "SMTP server rejected the message": {"de": "SMTP-Server hat abgelehnt"},
    "Connection failed": {"de": "Verbindungsfehler"},
    "SMTP protocol error": {"de": "SMTP-Protokollfehler"},
    "Transport error": {"de": "Transportfehler"},
    "Attempt limit reached": {"de": "Versuchslimit erreicht"},
    "Module / job": {"de": "Modul / Auftrag"},
    "Recipient": {"de": "Empfänger"},
    "Attempts": {"de": "Versuche"},
    "Action": {"de": "Aktion"},
    "Plugin paused": {"de": "Plugin pausiert"},
    "Unknown error": {"de": "Unbekannter Fehler"},
    "Due:": {"de": "Fällig:"},
    "Total:": {"de": "Gesamt:"},
    "Delivery checked; worker stopped; possible duplicate delivery accepted.": {"de": "Zustellung geprüft; Worker beendet; mögliche doppelte Zustellung akzeptiert."},
    "Queue again": {"de": "Erneut einplanen"},
    "No mail jobs yet.": {"de": "Keine Versandaufträge vorhanden."},
    "Mail queue pages": {"de": "Versandaufträge Seiten"},
    "Previous page": {"de": "Vorherige Seite"},
    "Next page": {"de": "Nächste Seite"},
    "Please enter a valid single email address.": {"de": "Bitte eine gültige einzelne E-Mail-Adresse eingeben."},
    "Unknown or missing SMTP setting.": {"de": "Unbekannte oder fehlende SMTP-Einstellung."},
    "Invalid SMTP activation or port.": {"de": "SMTP-Aktivierung oder Port ist ungültig."},
    "Invalid SMTP setting.": {"de": "Ungültige SMTP-Einstellung."},
    "Please select a valid transport.": {"de": "Bitte einen gültigen Transport auswählen."},
    "Enter an SMTP host without URL, path or credentials.": {"de": "SMTP-Host ohne URL, Pfad oder Zugangsdaten eingeben."},
    "SMTP authentication requires TLS.": {"de": "SMTP-Anmeldung erfordert TLS."},
    "SMTP host and sender are required to enable sending.": {"de": "Zum Aktivieren sind SMTP-Host und Absender erforderlich."},
    "Saved SMTP settings are invalid. Please save them again.": {"de": "Gespeicherte SMTP-Einstellungen sind ungültig. Bitte neu speichern."},
    "SMTP_PASSWORD is missing from the protected configuration file.": {"de": "SMTP_PASSWORD fehlt in der geschützten Konfigurationsdatei."},
    "Invalid mail module.": {"de": "Ungültiges Versandmodul."},
    "Invalid idempotency key.": {"de": "Ungültiger Idempotenzschlüssel."},
    "The subject must contain 1–200 characters without line breaks.": {"de": "Der Betreff muss 1–200 Zeichen ohne Zeilenumbruch enthalten."},
    "The message body must contain 1–65536 bytes.": {"de": "Der Nachrichtentext muss 1–65536 Bytes enthalten."},
    "The idempotency key has already been used for a different job.": {"de": "Der Idempotenzschlüssel wurde bereits für einen anderen Auftrag verwendet."},
    "The worker limit must be between 1 and 100.": {"de": "Worker-Limit muss zwischen 1 und 100 liegen."},
    "Only failed or uncertain jobs can be queued again.": {"de": "Nur fehlgeschlagene oder ungeklärte Aufträge können erneut gestartet werden."},
    "Uncertain delivery requires acknowledgement of possible duplicate delivery.": {"de": "Bei ungeklärtem Versand muss das Risiko einer doppelten Zustellung bestätigt werden."},
    "Unknown SMTP setting.": {"de": "Unbekannte SMTP-Einstellung."},
    "Please enter a port between 1 and 65535.": {"de": "Bitte einen Port zwischen 1 und 65535 eingeben."},
    "SMTP settings saved.": {"de": "SMTP-Einstellungen gespeichert."},
    "Please reopen the test form.": {"de": "Bitte das Testformular neu öffnen."},
    "Test job saved. Sending takes place on the next worker run.": {"de": "Testauftrag gespeichert. Der Versand erfolgt beim nächsten Worker-Lauf."},
    "Mail job queued again.": {"de": "Versandauftrag erneut eingeplant."},
    "Unknown action.": {"de": "Unbekannte Aktion."},
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
