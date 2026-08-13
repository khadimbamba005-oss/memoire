from django.urls import path
from . import views

urlpatterns = [
    path('',views.connexion,name='login'),
    path('enseignants/dashboard_enseignant/',views.dashboard_enseignant,name='dashboard_enseignant'),
    path('enseignants/emarger/',views.emarger, name='emarger'),
    path('enseignants/absence/',views.absence,name= 'absence'),
    path('enseignants/cahier/',views.cahier , name='cahier'),
    
    path('responsables/dashboard_responsable/', views.dashboard_responsable,name='dashboard_responsable'),
    # urls pour les modules
    path('responsables/modules/creer/', views.creer_module, name='creer_module'),
    path('responsables/modules/liste/',views.liste_modules , name='liste_modules'),
    path('responsables/modules/modifier/<int:pk>', views.modifier_module, name='modifier_module'),
    path('responsables/modules/supprimer/<int:pk>', views.supprimer_module, name='supprimer_module'),
    # urls pour les affectations
    path('responsable/affectations/creer', views.creer_affectation , name='creer_affectation'),
    path('responsables/affectations/liste_affectations', views.liste_affectations, name='liste_affectations'),
    path('responsables/affectations/modifier/<int:pk>',views.modifier_affectation, name='modifier_affectation'),
    path('responsables/affectations/suprimer/<int:pk>',views.supprimer_affectation, name='supprimer_affectation'),
    # urls pour les classes
    path('responsables/classes/' , views.liste_classes, name='liste_classes'),
    path('reponsables/classes/creer/', views.creer_classe , name='creer_classe'),
    path('responsables/classes/<int:pk>/' , views.details_classe , name='details_classe'),
    path('responsables/classes/modifier/<int:pk>', views.modifier_classe , name='modifier_classe'),
    path('responsables/classes/supprimer/<int:pk>', views.supprimer_classe , name='supprimer_classe'),
    
    # urls pour etudiants 
    path('responsables/classes/<int:classe_id>/etudiants/ajouter', views.ajouter_etudiant , name='ajouter_etudiant'),
    path('responsables/etudiants/modifier/<int:pk>/' , views.modifier_etudiant , name='modifier_etudiant'),
    path('responsables/etudiants/retirer/<int:pk>/', views.retirer_etudiant , name='retirer_etudiant'),
    # urls pour la deconnexion
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('dashboard/exporter/pdf/', views.apercu_impression_pdf , name='apercu_impression_pdf'),
    path('dashboard/absence/<int:absence_id>/toggle-justification/',views.toggle_justification_absence , name='toggle_justification_absence'),
    
]
