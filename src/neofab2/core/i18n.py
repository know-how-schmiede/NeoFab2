"""S02: Sprachwahl für Core-Zugang und Navigation, deutscher Text als Fallback."""

from flask import Blueprint, abort, g, redirect, request, session, url_for

LANGUAGES = {"de": "Deutsch", "en": "English", "fr": "Français"}
# Deutsche Ausgangstexte sind zugleich Fallback-Schlüssel. Keine HTML-Fragmente.
MESSAGES = {
    "Startseite": ("Home", "Accueil"),
    "NeoFab2 Startseite": ("NeoFab2 home", "Accueil NeoFab2"),
    "Hauptnavigation": ("Main navigation", "Navigation principale"),
    "Mein Profil": ("My profile", "Mon profil"),
    "Benutzerverwaltung": ("User management", "Gestion des utilisateurs"),
    "Systemeinstellungen": ("System settings", "Paramètres du système"),
    "Plugins": ("Plugins", "Extensions"),
    "Anmelden": ("Sign in", "Se connecter"),
    "Abmelden": ("Sign out", "Se déconnecter"),
    "Core im Aufbau": ("Core under development", "Socle en cours de développement"),
    "Anzeigename": ("Display name", "Nom affiché"),
    "E-Mail": ("Email", "E-mail"),
    "Passwort": ("Password", "Mot de passe"),
    "Sprache": ("Language", "Langue"),
    "Sprache übernehmen": ("Apply language", "Appliquer la langue"),
    "Darstellung": ("Appearance", "Apparence"),
    "Systemvorgabe": ("System default", "Valeur par défaut du système"),
    "Dunkel": ("Dark", "Sombre"),
    "Hell": ("Light", "Clair"),
    "Profil speichern": ("Save profile", "Enregistrer le profil"),
    "Passwort ändern": ("Change password", "Modifier le mot de passe"),
    "Aktuelles Passwort": ("Current password", "Mot de passe actuel"),
    "Neues Passwort": ("New password", "Nouveau mot de passe"),
    "Neues Passwort wiederholen": ("Repeat new password", "Confirmer le nouveau mot de passe"),
    "Benutzer": ("User", "Utilisateur"),
    "Mitarbeiter": ("Staff", "Personnel"),
    "Administrator": ("Administrator", "Administrateur"),
    "Hinweis": ("Notice", "Information"),
    "Aktion nicht möglich": ("Action unavailable", "Action impossible"),
    "Anmeldung neu öffnen": ("Open sign-in page", "Ouvrir la page de connexion"),
    "Zur Startseite": ("Back to home", "Retour à l’accueil"),
    "Deinen Zugang erhältst du von der Werkstatt-Administration.":
        ("Contact the workshop administration for an account.", "Contactez l’administration de l’atelier pour obtenir un compte."),
    "Passwort vergessen? Bitte die Administration kontaktieren.":
        ("Forgot your password? Please contact the administration.", "Mot de passe oublié ? Veuillez contacter l’administration."),
    "8 bis 128 Zeichen. Nach der Änderung musst du dich auf allen Geräten neu anmelden.":
        ("8 to 128 characters. After changing it, sign in again on all devices.",
         "De 8 à 128 caractères. Après la modification, reconnectez-vous sur tous vos appareils."),
    "Profil gespeichert.": ("Profile saved.", "Profil enregistré."),
    "Anmeldung nicht möglich. Zugangsdaten prüfen oder später erneut versuchen.":
        ("Unable to sign in. Check your credentials or try again later.",
         "Connexion impossible. Vérifiez vos identifiants ou réessayez plus tard."),
    "Die neuen Passwörter stimmen nicht überein.":
        ("The new passwords do not match.", "Les nouveaux mots de passe ne correspondent pas."),
    "Das aktuelle Passwort ist nicht korrekt.":
        ("The current password is incorrect.", "Le mot de passe actuel est incorrect."),
    "Das Passwort muss 8 bis 128 Zeichen enthalten.":
        ("The password must contain 8 to 128 characters.", "Le mot de passe doit contenir de 8 à 128 caractères."),
    "Der Anzeigename muss 1 bis 100 Zeichen enthalten.":
        ("The display name must contain 1 to 100 characters.", "Le nom affiché doit contenir de 1 à 100 caractères."),
    "Bitte eine gültige Darstellung wählen.":
        ("Please select a valid appearance.", "Veuillez choisir une apparence valide."),
    "Bitte eine gültige Sprache wählen.":
        ("Please select a valid language.", "Veuillez choisir une langue valide."),
    "Passwort geändert. Bitte neu anmelden; alle bisherigen Sitzungen wurden beendet.":
        ("Password changed. Please sign in again; all previous sessions have ended.",
         "Mot de passe modifié. Veuillez vous reconnecter ; toutes les sessions précédentes ont été fermées."),
    "Für diese Aktion fehlt die Berechtigung.":
        ("You do not have permission for this action.", "Vous n’avez pas l’autorisation d’effectuer cette action."),
    "Für diese Seite fehlt die Berechtigung.":
        ("You do not have permission to view this page.", "Vous n’avez pas l’autorisation de consulter cette page."),
    "Das System ist noch nicht bereit. Bitte die Administration informieren.":
        ("The system is not ready yet. Please contact the administration.",
         "Le système n’est pas encore prêt. Veuillez contacter l’administration."),
    "Die Formularsitzung ist abgelaufen oder ungültig. Bitte die Anmeldung neu öffnen und erneut versuchen.":
        ("The form session has expired or is invalid. Reopen the sign-in page and try again.",
         "La session du formulaire a expiré ou n’est pas valide. Rouvrez la page de connexion et réessayez."),
    "Die Sitzung zum Formular fehlt. Bitte Cookies für diese Website zulassen und die Anmeldung neu öffnen. Bei einem HTTP-Testzugang muss die Administration die Cookie-Einstellung prüfen; sichere Cookies benötigen HTTPS.":
        ("The form session is missing. Allow cookies for this site and reopen the sign-in page. For an HTTP test connection, the administration must check the cookie setting; secure cookies require HTTPS.",
         "La session du formulaire est absente. Autorisez les cookies pour ce site et rouvrez la page de connexion. Pour un accès de test HTTP, l’administration doit vérifier le réglage des cookies ; les cookies sécurisés nécessitent HTTPS."),
}

bp = Blueprint("language", __name__)


def current_language():
    user = g.get("current_user")
    value = user["locale"] if user else session.get("locale", "de")
    return value if value in LANGUAGES else "de"


def translate(message):
    language = current_language()
    pair = MESSAGES.get(message)
    if language == "de" or pair is None:
        return message
    return pair[0 if language == "en" else 1]


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
