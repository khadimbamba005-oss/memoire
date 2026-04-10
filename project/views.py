from django.shortcuts import render , redirect , get_list_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from .models import Emargement,Enseignant,Absence,Etudiant,Classe , Cahier
from datetime import datetime
from django.db.models.functions import TruncDate
from django.db.models import Count
import json

def connexion(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print("Nom d'utilsateur:", username)
        print("Mot de passe", password)

        user = authenticate(request , username=username , password=password)


        if user is not None:
            print("Connexion reussie")
            login(request,user)


            if user.role  == 'admin':
                return redirect('dashboard_admin')
            
            elif user.role == 'enseignant':
                return redirect('dashboard_enseignant')
            
            elif user.role == 'responsable':
                return redirect('dashboard_responsable')
            
            else:
                return render(request , 'login.html', {
                    'error':'Identifiants incorrects'
                })
            
    return render(request,'login.html')


def dashboard_enseignant(request):
    enseignant  = Enseignant.objects.get(user=request.user)

    stats = ((
        Emargement.objects
        .filter(enseignant=enseignant)
        .annotate(jour=TruncDate('date'))
        .values('jour')
        .annotate(total=Count('id')))
        .order_by('jour')
    )

    labels = [str(s['jour']) for s in stats]
    data = [s['total'] for s in stats]

    emargements = Emargement.objects.filter(
        enseignant=enseignant
    ).order_by('-date')[:5]

    total_emargements  = Emargement.objects.filter(
        enseignant = enseignant
    ).count()

    cahiers = Cahier.objects.filter(
        enseignant = enseignant
    ).order_by('-date')[:5]

    total_cours = Cahier.objects.filter(
        enseignant = enseignant
    ).count()

    return render(request,'enseignants/dashboard_enseignant.html',
                  {
                      'emargemens':emargements,
                      'cahiers':cahiers,
                      'total_emargements':total_emargements,
                      'total_cours':total_cours,
                      'labels':labels,
                      'data':data
                  })

@login_required
def emarger(request):
    enseignant = Enseignant.objects.get(user = request.user)

    Emargement.objects.create(
        enseignant = enseignant,
        date = datetime.today(),
        arrivee = datetime.now().time(),
        depart = datetime.now().time()
    )
    
    return redirect('dashboard_enseignant')

@login_required
def absence(request):
    if request.method == 'POST':
        etudiant_id  = request.POST.get('etudiant'),
        motif = request.POST.get('motif')

        Absence.objects.create(
            etudiant_id = etudiant_id,
            date = datetime.today(),
            motif = motif
        )

        return redirect('dashboard_enseignant')
    
@login_required
def remplir(request):
    
    if request.method == 'POST':
        enseignant = Enseignant.objects.get(user=request.user)
        contenu = request.POST.get('contenu')

        Cahier.objects.create(
            enseignant = enseignant,
            date = datetime.today(),
            contenu = contenu
        )
    return redirect('dashboard_enseignant')

def list(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Acces refuse")
    
    absences = Absence.objects.all()

    return render(request , 'absences.html', {'absences':absences})


def justifier(request , id):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Acces refuse")

    absence = get_list_or_404(Absence,id=id)

    if request.method == 'POST':
        motif = request.POST.get('motif')
        absence.justifier(motif)
        return redirect('liste_absences')
    
    return render(request , 'justifier.html', {'absence':absence})
