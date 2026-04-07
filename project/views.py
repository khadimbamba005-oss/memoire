from django.shortcuts import render


def connexion(request):
    return render(request , 'login.html')