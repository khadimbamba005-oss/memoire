from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Emargement, Enseignant, Absence, Etudiant, Classe, Cahier, Module, Affectation
from datetime import datetime , timedelta ,date
from django.db.models.functions import TruncDate
from django.db.models import Sum,F , ExpressionWrapper ,DurationField
from django.utils import timezone

def connexion(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
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
                logout(request)
                return render(request,'login.html', {
                    'error': "Ce compte n'a pas de rôle valide."
                })
        return render(request, 'login.html', {
            'error': "Nom d'utilisateur ou mot de passe incorrect."
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

    modules = Module.objects.filter(affectation__enseignant=enseignant).distinct()

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

        pourcentage = (total_module / m.volHoraire * 100) if m.volHoraire else 0
       
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

@login_required
def dashboard_responsable(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Cette page est réservée aux responsables pédagogiques.")
    
    type_operation = request.GET.get("type") or None
    enseignant_id = request.GET.get("enseignant") or None
    classe_id = request.GET.get("classe") or None
    date_debut = request.GET.get("date_debut") or None
    date_fin = request.GET.get("date_fin") or None

    enseignants = Enseignant.objects.all()
    classes = Classe.objects.all()

    resultat = []

    if type_operation == "emargement":
        resultat = Emargement.objects.select_related(
            "enseignant",
            "module",
            "classe"
        ).all()
        if enseignant_id:
            resultat = resultat.filter(
                enseignant_id = enseignant_id
            )

        if date_debut:
            resultat = resultat.filter(
                date__gte=date_debut
            )
        if date_fin:
            resultat = resultat.filter(date__lte=date_fin)

    elif type_operation == "absence":
        resultat = Absence.objects.select_related(
            "etudiant",
            "etudiant__filiere"
        ).all()
        if classe_id:
            resultat = resultat.filter(
                etudiant__filiere_id = classe_id
            )
        if date_debut:
            
            resultat = resultat.filter(date__gte=date_debut)
                    
        if date_fin:
            resultat = resultat.filter(date__lte=date_fin)
            
    elif type_operation == "cahier":
        resultat = Cahier.objects.select_related(
            "enseignant",
            "module",
            "classe"
        ).all()

        if enseignant_id:
            resultat = resultat.filter(
                enseignant_id = enseignant_id
            )

        if date_debut:
            resultat = resultat.filter(
            date__gte=date_debut
            )
        if date_fin:
            resultat = resultat.filter(date__lte =date_fin)

    context = {
        "modules_count":Module.objects.count(),
        "enseignants_count":Enseignant.objects.count(),
        "affectations_count":Affectation.objects.count(),

        "enseignants":enseignants,
        "classes":classes,

        "type_operation":type_operation or "",
        "enseignant_id":enseignant_id or "",
        "classe_id":classe_id or "",
        "date_debut":date_debut or "",
        "date_fin":date_fin or "",
        "resultat":resultat
    }

    return render(
        request,
        'responsables/dashboard_responsable.html',
        context
    )

@login_required
def gestion_classes(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Cette action est réservée aux responsables pédagogiques.")

    if request.method == 'POST':
        filiere = request.POST.get('filiere', '').strip()
        niveau = request.POST.get('niveau', '').strip()
        if not filiere or not niveau:
            messages.error(request, "La filière et le niveau sont obligatoires.")
        else:
            classe, cree = Classe.objects.get_or_create(filiere=filiere, niveau=niveau)
            if cree:
                messages.success(request, f"La classe {classe} a été créée.")
            else:
                messages.warning(request, "Cette classe existe déjà.")
            return redirect('gestion_classes')

    return render(request, 'responsables/gestion_classes.html', {
        'classes': Classe.objects.prefetch_related('etudiants').order_by('filiere', 'niveau'),
    })


@login_required
def ajouter_etudiant(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Cette action est réservée aux responsables pédagogiques.")

    classes = Classe.objects.order_by('filiere', 'niveau')
    if request.method == 'POST':
        champs = {nom: request.POST.get(nom, '').strip() for nom in ('nom', 'prenom', 'adresse', 'telephone', 'email')}
        classe_id = request.POST.get('classe')
        if not classe_id or not all(champs.values()):
            messages.error(request, "Tous les champs sont obligatoires.")
        else:
            Etudiant.objects.create(filiere_id=classe_id, **champs)
            messages.success(request, "L'étudiant a été ajouté à la classe.")
            return redirect('gestion_classes')
    return render(request, 'responsables/ajouter_etudiant.html', {'classes': classes})

@login_required
def creer_module(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Cette action est réservée aux responsables pédagogiques.")
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        volume_horaire = request.POST.get('vol_horaire', '').strip()
        if not nom or not volume_horaire:
            messages.error(request, "Le nom et le volume horaire sont obligatoires.")
        else:
            try:
                volume_horaire = int(volume_horaire)
                if volume_horaire <= 0:
                    raise ValueError
            except ValueError:
                messages.error(request, "Le volume horaire doit être un nombre entier positif.")
            else:
                Module.objects.create(nom=nom, volHoraire=volume_horaire)
                messages.success(request, f"Le module « {nom} » a été créé.")
                return redirect('dashboard_responsable')
    return render(request, 'responsables/creer_module.html')
    
def emarger(request):
    
    enseignant = Enseignant.objects.get(user=request.user)
    jour = date.today()
    modules = Module.objects.filter(affectation__enseignant=enseignant).distinct()

    if request.method == 'POST':
        arrivee = request.POST.get('arrivee')
        depart = request.POST.get('depart')
        module_id = request.POST.get('module')

        Emargement.objects.create(
            enseignant=enseignant,
            date = jour,
            arrivee = arrivee,
            depart = depart,
            module_id=module_id or None,
        )
        return redirect('dashboard_enseignant')
    return render(request,'enseignants/emarger.html',
                  {
                      'enseignant':enseignant,
                      'jour':jour,
                      'modules': modules,
                  })


def absence(request):
    classe_id = request.GET.get('classe')
    etudiants = []
    classes = Classe.objects.all()
    today = date.today()

    if classe_id:
        etudiants = Etudiant.objects.filter(filiere_id=classe_id).order_by('nom', 'prenom')
    if request.method == 'POST':
        classe_id = request.POST.get('classe')
        presents = set(request.POST.getlist('presents'))
        etudiants_classe = Etudiant.objects.filter(filiere_id=classe_id)
        absents = [etudiant for etudiant in etudiants_classe if str(etudiant.id) not in presents]
        for etudiant in absents:
            Absence.objects.get_or_create(etudiant=etudiant, date=today)
        messages.success(request, f"Présences enregistrées : {etudiants_classe.count() - len(absents)} présent(s), {len(absents)} absent(s).")
        return redirect('dashboard_enseignant')
    return render(request,'enseignants/absence.html',
                  {
                      'classes':classes,
                      'etudiants':etudiants,
                      'selected_classe':classe_id,
                      'today':today
                  })
   
   
def cahier(request):
    classes = Classe.objects.all()
    enseignant = Enseignant.objects.get(user=request.user)

    if request.method == 'POST':
        classe_id = request.POST.get('classe')
        contenu = request.POST.get('contenu')

        Cahier.objects.create(
            enseignant=enseignant,
            classe_id=classe_id or None,
            contenu=contenu,
            date=date.today(),
        )

        return redirect('dashboard_enseignant')
    return render(request,'enseignants/cahier.html',{
        'classes':classes
    })

def justifier(request,id):
   absence = Absence.objects.all().get(id=id)
   if request.method == 'POST':
       absence.justifie = True
       absence.save()

       return redirect('dashboard_responsable')
   
   return render(request,'justifier.html',
                 {
                     'absence':absence
                 })

@login_required
def affecter_module(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Cette action est réservée aux responsables pédagogiques.")

    modules = Module.objects.order_by('nom')
    enseignants = Enseignant.objects.order_by('nom', 'prenom')

    if request.method == "POST":
        module_id = request.POST.get('module')
        enseignant_id = request.POST.get('enseignant')
        annee_universitaire = request.POST.get('annee_universitaire', '').strip()
        if not module_id or not enseignant_id or not annee_universitaire:
            messages.error(request, "Tous les champs sont obligatoires.")
        else:
            module = get_object_or_404(Module, id=module_id)
            enseignant = get_object_or_404(Enseignant, id=enseignant_id)
            _, cree = Affectation.objects.get_or_create(module=module, enseignant=enseignant, annee_universitaire=annee_universitaire)
            if cree:
                messages.success(request, f"{module.nom} a été affecté à {enseignant}.")
            else:
                messages.warning(request, "Cette affectation existe déjà pour cette année universitaire.")
            return redirect("dashboard_responsable")
    
    return render(request,"responsables/affecter_module.html",{
        "modules":modules,
        "enseignants":enseignants
    })


def deconnexion(request):
    logout(request)
    return redirect('login')
        
