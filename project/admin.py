from django.contrib import admin
from .models import Absence, Enseignant, Etudiant, Emargment, User, AbstractUser, Classe ,Cahier

from project.models import Absence
admin.site.register(User)
# Register your models here.
@admin.register(Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email' , 'telephone')
    search_fields = ('nom', 'prenom')

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('filiere' , 'niveau')
    list_filter = ( 'niveau',)

@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'nom', 'prenom' , 'filiere')
    list_filter = ('filiere',)


@admin.register(Emargment)
class EmargmentAdmin(admin.ModelAdmin):
    list_display = ('enseignant', 'date')
    list_filter = ('date',)

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'date', 'motif')
    list_filter = ('date','etudiant')

@admin.register(Cahier)
class CahierAdmin(admin.ModelAdmin):
    list_display = ('contenu', 'enseignant', 'date')
    list_filter = ('date','contenu')

