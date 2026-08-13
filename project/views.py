from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden , HttpResponse  , JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Emargement, Enseignant, Absence, Etudiant, Classe, Cahier, Module, Affectation, ModuleForm , AffectationForm , ClasseForm , EtudiantForm
from datetime import datetime , timedelta ,date
from django.db.models.functions import TruncDate
from django.db.models import Sum,F , ExpressionWrapper ,DurationField
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Q

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
        "classes_count":Classe.objects.count(),
        "etudiants_count":Etudiant.objects.count(),
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

# liste des affectations 
def liste_affectations(request):
    if request.user.role != 'responsable':
            return HttpResponseForbidden("Cette page est réservée aux responsables pédagogiques.")
        
    affectations = Affectation.objects.select_related('enseignant','module','classe').order_by('annee_universitaire')
    
    paginator  = Paginator(affectations,10)
    page_number =  request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'responsables/liste_affectations.html',{'page_obj':page_obj})

def creer_affectation(request):
    
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Cette action est réservée à l'assistante pédagogique")
    
    if request.method == 'POST':
        # Récupération des identifiants depuis le formulaire
        enseignant_id = request.POST.get('enseignant', '').strip()
        module_id = request.POST.get('module', '').strip()
        classe_id = request.POST.get('classe', '').strip()
        annee_universitaire = request.POST.get('annee_universitaire', '').strip()
        
        # 2. Validation de la présence des champs obligatoires
        if not enseignant_id or not module_id or not classe_id or not annee_universitaire:
            messages.error(request, "Tous les champs sont obligatoires.")
            # Recharger la page en renvoyant les listes pour le formulaire
            enseignants = Enseignant.objects.all()
            modules = Module.objects.all()
            classes = Classe.objects.all()
            return render(request, 'responsables/creer_affectation.html', {
                'enseignants': enseignants, 'modules': modules, 'classes': classes
            })
            
        try:
            # 3. Récupération des instances d'objets pour tester leur existence
            enseignant = Enseignant.objects.get(id=enseignant_id)
            module = Module.objects.get(id=module_id)
            classe = Classe.objects.get(id=classe_id)
            
            # 4. Vérification d'unicité (unique_together) avant création
            deja_affecte = Affectation.objects.filter(
                enseignant=enseignant,
                module=module,
                annee_universitaire=annee_universitaire,
                classe=classe
            ).exists()
            
            if deja_affecte:
                messages.error(request, f"Cet enseignant est déjà affecté à ce module pour cette classe et cette année.")
            else:
                # 5. Création de l'affectation si tout est valide
                Affectation.objects.create(
                    enseignant=enseignant,
                    module=module,
                    classe=classe,
                    annee_universitaire=annee_universitaire
                )
                messages.success(request, f"L'affectation de {enseignant} sur le module {module} a été créée avec succès.")
                return redirect('dashboard_responsable')
                
        except (ValueError, Enseignant.DoesNotExist, Module.DoesNotExist, Classe.DoesNotExist):
            messages.error(request, "Une des entités sélectionnées (Enseignant, Module ou Classe) est invalide.")
            
    # Récupération des données pour alimenter les listes déroulantes (<select>) du formulaire
    context = {
        'enseignants': Enseignant.objects.all(),
        'modules': Module.objects.all(),
        'classes': Classe.objects.all(),
    }
    return render(request, 'responsables/affecter_module.html', context)

# Vue pour affectation
def modifier_affectation(request, pk):
    
    if request.user.role != 'responsable':
                return HttpResponseForbidden("Cette page est réservée à l'assistante pédagogiques.")
    
    affectation = get_object_or_404(Affectation, pk=pk)
    
    if request.method == 'POST':
        # Associe les données POST à l'instance existante
        form = AffectationForm(request.POST, instance=affectation)
        if form.is_valid():
            form.save()
            messages.success(request, "L'affectation a été modifiée avec succès.")
            return redirect('liste_affectations')
    else:
        # Pré-remplit le formulaire avec les valeurs actuelles de la base
        form = AffectationForm(instance=affectation)
        
    return render(request, 'responsables/modifier_affectation.html', {'form': form})

@require_POST
def supprimer_affectation(request,pk):
    affetation = get_object_or_404(Affectation, pk=pk)
    affetation.delete()
    return redirect('liste_affectations')

# Vue les modules
@login_required
def creer_module(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Cette action est réservée à l'assistante pédagogique")
    
    if request.method == 'POST':
        nom = request.POST.get('nom','').strip()
        
        try:
            cm = int(request.POST.get('heures_cm') or 0)
            td = int(request.POST.get('heures_td') or 0)
            tp = int(request.POST.get('heures_tp') or 0)
            
            if cm < 0 or td < 0 or tp < 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Les volumes doivent etre des entiers positifs")
            
            return render(request, 'responsables/creer_module.html')
        
        if not nom:
            messages.error(request, "Le nom du module est obligatoire")
        elif ( cm + td + tp ) == 0:
            messages.error(request,"Le volume horaire total ne peut à 0 heure.")
        else:
            Module.objects.create(nom=nom,heures_cm = cm, heures_td=td,heures_tp=tp)
            messages.success(request,f"Le module {nom} a été créé avec succès.")
            return redirect('dashboard_responsable')
    return render(request,'responsables/creer_module.html')
def liste_modules(request):
    if request.user.role != 'responsable':
            return HttpResponseForbidden("Cette action est réservée à l'assistante pédagogique.")
    modules = Module.objects.all().order_by('nom')
    paginator = Paginator(modules , 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,'responsables/liste_modules.html',{'page_obj':page_obj })

@require_POST
def modifier_module(request, pk):
    if request.user.role != 'responsable':
            return HttpResponseForbidden("Cette action est réservée à l'assistante pédagogique.")
        
    module = get_object_or_404(Module, pk=pk)
    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            return redirect('liste_modules')
        
    else:
        form = ModuleForm(instance=module)
            
    return render(request,'responsables/modifier_module.html',{'form':form,'module':module})

@require_POST
def supprimer_module(request, pk):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Cette action est réservée à l'assistante pédagogique.")
    
    module = get_object_or_404(Module, pk=pk)
    module.delete()
    return redirect('liste_modules')


    
# vue pour faire une nouvelle affectation 

# Vue pour les emargements 
def emarger(request):
    if request.user.role != 'enseignant':
        return HttpResponseForbidden("Acces refuse")
    
    enseignant = Enseignant.objects.get(user=request.user)
    jour = date.today()
    modules = Module.objects.filter(affectation__enseignant=enseignant).distinct()
    classes = Classe.objects.filter(affectation__enseignant=enseignant).distinct

    if request.method == 'POST':
        arrivee = request.POST.get('arrivee')
        depart = request.POST.get('depart')
        module_id = request.POST.get('module')
        classe_id = request.POST.get('classe')

        if module_id and not modules.filter(id=module_id).exists():
            messages.error(request,"Action non autorisee : Ce module ne vous est attibué.")
            return redirect('emarger')
        
        Emargement.objects.create(
            enseignant=enseignant,
            date = jour,
            arrivee = arrivee,
            depart = depart,
            module_id=module_id or None,
            classe_id=classe_id or None,
        )
        messages.success(request,"Votrs émargement a été bien enregistré.")
        return redirect('dashboard_enseignant')
    return render(request,'enseignants/emarger.html',
                  {
                      'enseignant':enseignant,
                      'jour':jour,
                      'modules': modules,
                      'classes':classes,
                  })


def absence(request):
    if request.user.role != 'enseignant':
        return HttpResponseForbidden("Accès refusé")
    
    enseignant = Enseignant.objects.get(user=request.user)
    classe_id = request.GET.get('classe')
    etudiants = []
    classes = Classe.objects.all()
    today = date.today()

    if classe_id:
        if classes.filter(id=classe_id).exists():
            etudiants = Etudiant.objects.filter(filiere_id=classe_id).order_by('nom', 'prenom')
        else:
            messages.error(request,"Vous n'intervenez pas dans cette classe.")
            classe_id = None
    if request.method == 'POST' and classe_id:
        classe_id = request.POST.get('classe')
        presents = set(request.POST.getlist('presents'))
        justifies = set(request.POST.getlist('justifies'))
        etudiants_classe = Etudiant.objects.filter(filiere_id=classe_id)
        absents = [etudiant for etudiant in etudiants_classe if str(etudiant.id) not in presents]
        for etudiant in absents:
            est_justifiie = str(etudiant.id) in justifies
            
            Absence.objects.get_or_create(etudiant=etudiant, date=today, defaults={'justifie': est_justifiie})
            
            messages.success(request, f"Presences enregistrees:{etudiants_classe.count() - len(absents)} presents(s),{len(absents)} absent(s).")
        
           
        return redirect('dashboard_enseignant')
    return render(request,'enseignants/absence.html',
                  {
                      'classes':classes,
                      'etudiants':etudiants,
                      'selected_classe':classe_id,
                      'today':today
                  })
   
# Vue des cahiers de texte 
def cahier(request):
    enseignant = Enseignant.objects.get(user=request.user)
    classes = Classe.objects.filter(affectation__enseignant=enseignant).distinct()
    modules = Module.objects.filter(affectation__enseignant=enseignant).distinct()
    
    if request.method == 'POST':
        classe_id = request.POST.get('classe')
        contenu = request.POST.get('contenu')
        module_id = request.POST.get('module')

        if (classe_id and not classes.filter(id=classe_id).exists()) or (module_id and not modules.filter(id=module_id).exists()):
            messages.error(request,"Données invalides: Vous n'êtes pas affecté à cette classe ou à ce module")
            return redirect('cahier')
        
        Cahier.objects.create(
            enseignant=enseignant,
            classe_id=classe_id or None,
            module_id = module_id or None,
            contenu=contenu,
            date=date.today(),
        )
        messages.success(request,"Le cahier de texte a été rempli.")
        return redirect('dashboard_enseignant')
    return render(request,'enseignants/cahier.html',{
        'classes':classes,
        'modules':modules,
        'enseignant':enseignant
    })

# Justification 
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
        return HttpResponseForbidden("Cette action est réservée à l'assistante pédagogique.")

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

# vue pour exporter et imprimer 
def apercu_impression_pdf(request):
    if request.user.role == 'enseignant':
        return HttpResponseForbidden("Acces refuse")
    
    type_operation = request.GET.get("type")
    enseignant_id = request.GET.get("enseignant")
    classe_id = request.GET.get("classe")
    date_debut = request.GET.get("date_debut")
    date_fin = request.GET.get("date_fin")
    
    resultat = []
    
    if type_operation == "emargement":
        resultat = Emargement.objects.select_related("classe","module", "enseignant").all()
        if enseignant_id: resultat = resultat.filter(enseignant_id=enseignant_id)
        if date_debut: resultat = resultat.filter(date__gte=date_debut)
        if date_fin: resultat =resultat.filter(date__lte=date_fin)
        
    elif type_operation == "absence":
        resultat = Absence.objects.select_related("etudiant","etudiant__filiere").all()
        if classe_id: resultat = resultat.filter(etudiant__filiere_id=classe_id)
        if date_debut: resultat = resultat.filter(date__gte=date_debut)
        if date_fin: resultat =resultat.filter(date__lte=date_fin)
            
    elif type_operation == "cahier":
        resultat = Cahier.objects.select_related("classe","module","enseignant").all()
        if enseignant_id: resultat = resultat.filter(enseignant_id=enseignant_id)
        if classe_id: resultat = resultat.filter(classe_id=classe_id)
        if date_debut: resultat = resultat.filter(date__gte=date_debut)
        if date_fin: resultat = resultat.filter(date__lte=date_fin)
        
        
    context = {
        "type_operation": type_operation,
        "resultat": resultat,
        "date_debut": date_debut,
        "date_fin": date_fin,
        }
        
    return render(request, 'responsables/impression_pdf.html', context)


# vue pour  la justification d'une absence 
@require_POST
def toggle_justification_absence(request, absence_id):
    if request.user.role != 'responsable':
        return JsonResponse({ 'status':'error','message':'Interdit'}, status=403)

    try:
        absence = Absence.objects.get(id=absence_id)
        absence.justifie = not absence.justifie
        absence.save()
        return JsonResponse({'status':'success','justifie':absence.justifie})
    except Absence.DoesNotExist:
        return JsonResponse({'status':'error','message':'Absence introuvable '}, status=404)


# Vues pour pour la gestion des classes
def liste_classes(request):
    if request.user.role == 'enseignant':
            return HttpResponseForbidden("Acces refuse")
        
    classes = Classe.objects.all().order_by('filiere','niveau')
    paginator = Paginator(classes,10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request,'responsables/liste_classes.html',{'page_obj':page_obj})


def creer_classe(request):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Acces refuse")
    
    if request.method == 'POST':
        form = ClasseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "La classe a été créée avec succès .")
            return redirect('liste_classes')
    
    else:
        form = ClasseForm()
    return render(request,'responsables/creer_classe.html',{'form':form})


def details_classe(request,pk):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Acces refuse")
    
    classe = get_object_or_404(Classe,pk=pk)
    
    if request.method == 'POST' and 'supprimer_etduiant_id' in request.POST:
        etudiant_id = request.POST.get('supprimer_etudiant_id')
        etudiant = get_object_or_404(Etudiant, id=etudiant_id, filter=classe)
        etudiant.delete()
        messages.success(request,f"L'étudiant(e) {etudiant} a été retiré(e) de la classe.")
        return redirect('details_classe',pk=classe.id)
    
    etudiants_classe = classe.etudiants.all().order_by('nom')
    return render(request,'responsables/details_classe.html',{'classe':classe,'etudiants':etudiants_classe})  

def modifier_classe(request,pk):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Acces refuse")
    
    classe = get_object_or_404(Classe,pk=pk)
    
    if request.method == 'POST':
        form = ClasseForm(request.POST,instance=classe)
        
        if form.is_valid():
            form.save()
            messages.success(request,f"La classe {classe.code} a été modifiée avec succès")
            return redirect('liste_classes')
    else:
        form = ClasseForm(instance=classe)
    
    return render(request,'responsables/modifier_classe.html',{'form':form,'classe':classe})   

def supprimer_classe(request,pk):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Acces refusé")
    
    classe = get_object_or_404(Classe,pk=pk)
    
    if request.method == 'POST':
        if classe.etudiants.exists():
            messages.error(
                request,f"Impossible de supprimer la classe {classe}.Elle contient encore {classe.etudiants.count()} étudiant(s)."
            )  
        else:
            classe.delete()
            messages.success(request,f"La classe {classe} a été supprimée avec succès")
    return redirect('liste_classes')


def ajouter_etudiant(request,classe_id):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Acces refuse")
    
    classe = get_object_or_404(Classe,pk=classe_id) 
    
    if request.method == 'POST':
        form = EtudiantForm(request.POST)
        if form.is_valid():
            etudiant = form.save(commit=False)
            etudiant.filiere = classe
            etudiant.save()
            messages.success(request, f"L'étudiant(e) {etudiant} a été ajouté(e) à la classe {classe}.")
            return redirect('details_classe',pk=classe.id)
        
    else:
        form = EtudiantForm(initial={'filiere':classe})
        
    return render(request,'responsables/creer_etudiant.html',{'form':form,'classe':classe})


def modifier_etudiant(request,pk):
    if request.user.role != 'responsable':
        return HttpResponseForbidden("Acces refuse")
    
    etudiant = get_object_or_404(Etudiant,pk=pk)
    ancienne_classe_id = etudiant.filiere.id
    
    if request.method == 'POST':
        form = EtudiantForm(request.POST , instance=etudiant)
        
        if form.is_valid():
            nouvel_etudiant = form.save()
            messages.success(request,f"Le profil de {nouvel_etudiant} a été mis à jour.")
            return redirect('details_classe',pk=nouvel_etudiant.filiere.id)
        else:
            messages.error(request,"Veuillez corriger les erreurs dans le formulaire ci-dessus")
    else:
        form = EtudiantForm(instance=etudiant)
    
    return render(request, 'responsables/modifier_etudiant.html',{'form':form, 'etudiant':etudiant})
   

        
def retirer_etudiant(request,pk):
    etudiant = get_object_or_404(Etudiant,pk=pk)
    classe_pk = etudiant.filiere.pk
    etudiant.delete()
    return redirect('details_classe',pk=classe_pk)