from datetime import time
from django.shortcuts import render
from django.utils import timezone


class AccessHoursMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Heure locale du Sénégal
        maintenant = timezone.localtime()
        heure_actuelle = maintenant.time()

        heure_debut = time(8, 0)
        heure_fin = time(20, 0)

        # Pages accessibles même en dehors des horaires
        urls_autorisees = [
            '/login/',
            '/deconnexion/',
        ]

        # Si l'URL est autorisée, on laisse passer
        if request.path in urls_autorisees:
            return self.get_response(request)

        # Si l'utilisateur est connecté,
        # contrôler les horaires
        if request.user.is_authenticated:

            if not (heure_debut <= heure_actuelle < heure_fin):

                return render(
                    request,
                    'hors_service.html',
                    {
                        'heure_debut': '08h00',
                        'heure_fin': '20h00',
                        'heure_actuelle': maintenant.strftime('%H:%M'),
                    },
                    status=403
                )

        return self.get_response(request)