from django.urls import path
from . import views

urlpatterns = [
    path('',views.connexion , name='login'),
    path('dashboard_enseignant/', views.dashboard_enseignant , name='dashboard_enseignant'),
    path('emargement/',views.emarger , name='emarger'),
    path('absence/', views.absence , name= 'absence'),
    path('cahier/' ,views.remplir , name='remplir')
    
]