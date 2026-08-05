from django.urls import path
from . import views

urlpatterns = [
    path('',views.connexion,name='login'),
    path('enseignants/dashboard_enseignant/',views.dashboard_enseignant,name='dashboard_enseignant'),
    path('enseignants/emarger/',views.emarger, name='emarger'),
    path('enseignants/absence/',views.absence,name= 'absence'),
    path('enseignants/cahier/',views.cahier , name='cahier'),
    path('responsables/dashboard_responsable/', views.dashboard_responsable,name='dashboard_responsable'),
    path('responsables/modules/creer/', views.creer_module, name='creer_module'),
    path('responsables/modules/liste/',views.liste_modules , name='liste_modules'),
    path('responsables/modules/modifier/<int:pk>', views.modifier_module, name='modifier_module'),
    path('responsables/modules/supprimer/<int:pk>', views.supprimer_module, name='supprimer_module'),
    path('responsables/classes/', views.gestion_classes, name='gestion_classes'),
    path('responsables/etudiants/ajouter/', views.ajouter_etudiant, name='ajouter_etudiant'),
    path('justifier/<int:id>',views.justifier, name='justifier'),
    path('responsables/affectations/creer/', views.affecter_module, name='affecter_module'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('dashboard/exporter/pdf/', views.apercu_impression_pdf , name='apercu_impression_pdf'),
    path('dashboard/absence/<int:absence_id>/toggle-justification/',views.toggle_justification_absence , name='toggle_justification_absence'),
    
]
