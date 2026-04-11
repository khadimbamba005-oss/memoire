from django.urls import path
from . import views

urlpatterns = [
    path('',views.connexion,name='login'),
    path('enseignants/dashboard_enseignant/',views.dashboard_enseignant,name='dashboard_enseignant'),
    path('enseignants/emarger/',views.emarger, name='emarger'),
    path('enseignants/absence/',views.absence,name= 'absence'),
    path('enseignants/cahier/',views.cahier , name='cahier'),
    path('responsables/dashboard_responsable', views.dashboard_responsable,name='dashboard_responsable'),
    path('justifier/<int:id>',views.justifier, name='justifier')
    
]