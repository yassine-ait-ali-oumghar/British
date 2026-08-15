from django.shortcuts import redirect

class RequireLoginMiddleware:
    """
    Middleware qui autorise l'accès public au site (Accueil, Services, Équipe, Boutique, Contact).
    Exige la connexion dès qu'un utilisateur tente de réserver, commander, ou d'accéder au tableau de bord / espace membre.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            protected_prefixes = [
                '/reservation/',
                '/mes-reservations/',
                '/dashboard/',
                '/employee/',
            ]
            if any(path.startswith(prefix) for prefix in protected_prefixes):
                return redirect(f"/accounts/login/?next={path}")

        response = self.get_response(request)
        return response
