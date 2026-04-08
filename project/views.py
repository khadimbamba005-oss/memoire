from django.shortcuts import render , redirect , get_list_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from .models import Emargement,Enseignant,Absence,Etudiant,Classe , Cahier
from datetime import datetime


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

    emargements = Emargement.objects.filter(
        enseignant=enseignant
    ).order_by('-date')[:5]

    etudiants = Etudiant.objects.all()

    classes = Classe.objects.all()


    cahiers = Cahier.objects.filter(
        enseignant = enseignant
    ).order_by('-date')[:5]


    return render(request,'dashboard_enseignant.html',
                  {
                      'emargemens':emargements,
                      'etudiants': etudiants,
                      'classes':classes,
                      'cahiers':cahiers
                  })


def emarger(request):
    enseignant = Enseignant.objects.get(user = request.user)

    if request.method ==  'POST':
        Emargement.objects.create(
            enseignant = enseignant,
            date = datetime.today(),
            arrivee = datetime.now().time(),
            depart = datetime.now().time()
        )
    
    return redirect('dashboard_enseignant')


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
    

def remplir(request):
    enseignant = Enseignant.objects.get(user = request.user)

    if request.method == 'POST':
        classe_id  = request.POST.get('classe'),
        contenu = request.POST.get('contenu')
    
        Cahier.objects.create(
            enseignant = enseignant,
            classe_id = classe_id,
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
