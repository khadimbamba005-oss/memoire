from django.shortcuts import render , redirect , get_list_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from .models import Emargement,Enseignant,Absence,Etudiant,Classe,Cahier,Responsable,Module
from datetime import datetime , timedelta ,date
from django.db.models.functions import TruncDate
from django.db.models import Sum,F , ExpressionWrapper ,DurationField
from django.utils import timezone

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

#dashboard pour enseignant 
def dashboard_enseignant(request):
    enseignant  = Enseignant.objects.get(user=request.user)

    semaine = timezone.now().date() - timedelta(days=7)

    cahiers = Cahier.objects.filter(
        enseignant = enseignant,
        date__gte = semaine
    ).order_by('-date')

    emargements = Emargement.objects.filter(
        enseignant=enseignant
    )

    duree = emargements.annotate(
        duree = ExpressionWrapper(
            F('depart') - F('arrivee'),
            output_field=DurationField()
        )
    )


    modules = Module.objects.filter(enseignant=enseignant)

    modules_data = []

    for m in modules:
        heures =  Emargement.objects.filter(
            enseignant=enseignant,
            module = m
        )
        
        heures = heures.annotate(
            duree = ExpressionWrapper(
                F('depart')-F('arrivee'),
                output_field=DurationField()
            )
        )

        total_module = sum(
            [h.duree.total_seconds() / 3600 for h in heures if h.duree]
        )

        pourcentage = (total_module / m.volHoraire * 100) if m.VolHoraire else 0
       
        modules_data.append(
            {
                'nom':m.nom,
                'heures':round(total_module, 2),
                'volHoraire':m.volHoraire,
                'pourcentage':round(pourcentage , 2),
                
            }
        )

    classes = Classe.objects.all()
    etudiants = Etudiant.objects.filter(filiere__in =classes)
    return render(request,'enseignants/dashboard_enseignant.html',
                  {
                     'cahiers':cahiers,
                     'enseignant':enseignant,
                     'modules_data':modules_data,
                     'etudiants':etudiants
                     
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
    jour = date.today()

   

    if request.method == 'POST':
        arrivee = request.POST.get('arrivee')
        depart = request.POST.get('depart')
        module = request.POST.get('module')
        contenu = request.POST.get('contenu')

        Emargement.objects.create(
            enseignant=enseignant,
            date = jour,
            arrivee = arrivee,
            depart = depart,
            contenu = contenu,
            module = module
        )
        return redirect('dashboard_enseignant')
    return render(request , 'enseignants/emarger.html',
                  {
                      'enseignant':enseignant,
                      'jour':jour
                  })


def absence(request):
    classe_id = request.GET.get('classe')
    etudiants = []

    if classe_id:
           etudiants = Etudiant.objects.filter(filiere_id = classe_id)

    classes = Classe.objects.all()

    return render(request,'enseignants/absence.html',
                  {
                      'classes':classes,
                      'etudiants':etudiants,
                      'selected_classe':classe_id
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