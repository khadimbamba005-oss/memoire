from django.shortcuts import render , redirect , get_list_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from .models import Emargement,Enseignant,Absence,Etudiant,Classe,Cahier,Responsable
from datetime import datetime
from django.db.models.functions import TruncDate
from django.db.models import Count

def connexion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request,username=username, password=password)

        if user is not None:
            login(request,user)

            if user.role  == 'admin':
                return redirect('dashboard_admin')
            
            elif user.role == 'enseignant':
                return redirect('dashboard_enseignant')
            
            elif user.role == 'responsable':
                return redirect('dashboard_responsable')
            
            else:
                return render(request,'login.html', {
                    'error':'Identifiants incorrects'
                })
    return render(request,'login.html')

def dashboard_enseignant(request):
    enseignant  = Enseignant.objects.filter(user=request.user).first()

    if not enseignant:
        return redirect('login')

    emargements = Emargement.objects.filter(
        enseignant=enseignant
    ).order_by('-date')[:5]

    total_emargements = emargements.count()

    cahiers = Cahier.objects.filter(
        enseignant = enseignant
    ).order_by('-date')[:5]

    total_cours = cahiers.count()

    return render(request,'enseignants/dashboard_enseignant.html',
                  {
                     'emargements':emargements,
                     'cahiers':cahiers,
                     'total_emargements':total_emargements,
                     'total_cours':total_cours,
                  })

def dashboard_responsable(request):
    responsable = Responsable.objects.filter(user=request.user).first()

    if  not responsable:
        return redirect('login')
    
    emargements = Emargement.objects.filter().order_by('-date')[:10]

    absences = Absence.objects.all().order_by('-date')

    return render(request,'responsables/dashboard_responsable.html',{
        'emargements':emargements,
        'absences':absences
    })
    
def emarger(request):
    enseignant = Enseignant.objects.get(user=request.user)
    ens = Enseignant.objects.all()
    
    if request.method == 'POST':
        arrivee = request.POST.get('arrivee')
        depart = request.POST.get('depart')

        Emargement.objects.create(
            enseignant = enseignant,
            date = datetime.today(),
            arrivee = arrivee,
            depart = depart
    )
    
        return redirect('dashboard_enseignant')
    return render(request , 'enseignants/emarger.html',
                  {
                      'ens':ens
                  })

def absence(request):
    etudiants = Etudiant.objects.all()

    if request.method == 'POST':
            etudiant_id = request.POST.get('etudiant')
            motif = request.POST.get('motif')

            Absence.objects.create(
                etudiant_id = etudiant_id,
                date = datetime.today(),
                motif = motif
            )
            return redirect('dashboard_enseignant')
    return render(request, 'enseignants/absence.html',{
        'etudiants':etudiants
    })


def cahier(request):
    classes = Classe.objects.all()
    enseignant = Enseignant.objects.get(user=request.user)

    if request.method == 'POST':
        classe_id = request.POST.get('classe')
        contenu = request.POST.get('contenu')

        Cahier.objects.create(
            enseignant = enseignant,
            contenu = contenu,
            date = datetime.today(),
        )

        return redirect('dashboard_enseignant')
    return render(request,'enseignants/cahier',{
        'classes':classes
    })

def justifier(request,id):
   absence = Absence.objects.all().get(id=id)
   if request.method == 'POST':
       absence.justifie = True
       absence.save()

       return redirect('dashboard_responsable')
   
   return render(request,'responsables/dashboard_responsable.html',
                 {
                     'absence':absence
                 })