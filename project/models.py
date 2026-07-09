from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string
from datetime import datetime

# generation de matricule
def generate_matricule(nom,filiere):
    nom_part = nom.strip()
    filiere_part = filiere.strip().upper()[:3]
    annee = datetime.now().year
    aleatoire = ''.join(random.choices(string.digits,k=4))
    matricule = f"{nom_part}{filiere_part}{annee}{aleatoire}"
    return matricule

# Creation du model user avec ces differents roles
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('enseignant','Enseignant'),
        ('responsable','Responsable'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES , default='enseignant')

    def __str__(self):
        return self.username


class Enseignant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=20)
    prenom = models.CharField(max_length=20)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)


    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
class Responsable(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=20)
    prenom = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Classe(models.Model):
    filiere = models.CharField(max_length=20)
    niveau = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.filiere} {self.niveau}"

class Etudiant(models.Model):
    matricule = models.CharField(max_length=20, unique=True , blank=True)
    nom = models.CharField(max_length=20)
    prenom = models.CharField(max_length=20)
    adresse = models.CharField(max_length=20)
    telephone = models.CharField(max_length=9)
    email = models.EmailField()
    filiere = models.ForeignKey(Classe, on_delete=models.CASCADE , related_name="etudiants")

    def save(self, *args, **kwargs):
        if not self.matricule:
            self.matricule = generate_matricule(self.nom,self.filiere.filiere)
            super().save(*args, **kwargs)

    def __str__(self):
        return f" {self.prenom} {self.nom}"
    
class Module(models.Model):
    nom = models.CharField(max_length=30, null=True)
    volHoraire = models.IntegerField(null=True)
    

    def __str__(self):
        return self.nom

class Emargement(models.Model):
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    date = models.DateField()
    arrivee = models.TimeField()
    depart = models.TimeField()
    module = models.ForeignKey(Module , on_delete=models.CASCADE , blank=True , null=True )

    def __str__(self):
        return f"{self.enseignant} {self.date}"


class Absence(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    date = models.DateField()
    justifie = models.BooleanField(default=False)
    motif = models.CharField(max_length=500)

    
    def justifier(self , motif):
        self.justifie = True
        self.motif = motif
        self.save()


class Cahier(models.Model):
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe , on_delete=models.CASCADE , null=True , blank=True)
    date = models.DateField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE ,blank=True , null=True)
    contenu = models.TextField()

    def __str__(self):
        return f"{self.enseignant} {self.date}"


class Affectation(models.Model):
    enseignant = models.ForeignKey(Enseignant , on_delete=models.CASCADE)
    module = models.ForeignKey(Module,on_delete=models.CASCADE)
    annee_universitaire = models.CharField(max_length=20,default="2025-2026" , blank=True)


    class Meta:
        unique_together = ("enseignant", "module", "annee_universitaire")
    
    def __str__(self):
        return f"{self.enseignant}  {self.module}"