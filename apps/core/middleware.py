# ==============================================================================
# MIDDLEWARE DE SÉCURITÉ ET CONTRÔLE D'ACCÈS GLOBAL
# ==============================================================================
# Ce middleware intercepte TOUTES les requêtes HTTP arrivant sur le serveur.
# Il autorise les visiteurs anonymes à consulter la vitrine publique, mais
# bloque et redirige vers la page de connexion dès qu'un utilisateur essaie
# d'accéder à la réservation, à l'espace membre employé ou aux tableaux de bord.
# ==============================================================================

from django.shortcuts import redirect


class RequireLoginMiddleware:
    """
    Middleware de restriction d'accès aux URLs protégées.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si l'utilisateur n'est pas encore connecté
        if not request.user.is_authenticated:
            path = request.path_info
            
            # Liste des préfixes d'URL exigeant obligatoirement une authentification
            protected_prefixes = [
                '/reservation/',
                '/mes-reservations/',
                '/dashboard/',
                '/employee/',
            ]
            
            # Si l'URL demandée commence par un des préfixes protégés -> Redirection vers Login
            if any(path.startswith(prefix) for prefix in protected_prefixes):
                return redirect(f"/accounts/login/?next={path}")

        # Sinon, l'accès est autorisé et la requête continue normalement
        response = self.get_response(request)
        return response
