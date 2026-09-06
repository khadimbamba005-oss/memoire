from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string
from datetime import datetime
from django import forms

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
    nom = models.CharField(max_length=40)
    prenom = models.CharField(max_length=40)
    email = models.EmailField()
    telephone = models.CharField(max_length=9)

    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
class AssistantePedagogique(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=40)
    prenom = models.CharField(max_length=40)
    email = models.EmailField()
    telephone = models.CharField(max_length=9)

    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
class Classe(models.Model):
    code = models.CharField(max_length=10, blank=True)
    filiere = models.CharField(max_length=40)
    niveau = models.CharField(max_length=40)

    def __str__(self):
        return f"{self.filiere} {self.niveau}"
    
class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['code','niveau','filiere']
        widgets = {
            'code':forms.TextInput(attrs={'class':'input input-bordered w-full','placeholder':'L1INFO'}),
            'niveau':forms.TextInput(attrs={'class':'input input-bordered w-full','placeholder':'Licence 1'}),
            'filiere':forms.TextInput(attrs={'class':'input input-bordered w-full','placeholder':'Genie Logiciel'})
        }
        

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
        return f"{self.prenom} {self.nom}"
    
class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = ['nom','prenom','adresse','telephone','email']
        widgets = {
            'nom': forms.TextInput(attrs={'class':'input input-bordered w-full'}),
            'prenom': forms.TextInput(attrs={'class':'input input-bordered w-full'}),
            'adresse':forms.TextInput(attrs={'class':'input input-bordered w-full'}),
            'telephone':forms.TextInput(attrs={'class':'input input-bordered w-full','maxlength': '9'}),
            'email':forms.EmailInput(attrs={'class':'input input-borded w-full'}),
        }
    
class Module(models.Model):
    code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    nom = models.CharField(max_length=30, null=True)
    heures_cm = models.PositiveBigIntegerField(default=0, verbose_name="Heure CM")
    heures_td = models.PositiveBigIntegerField(default=0, verbose_name="Heures TD")
    heures_tp = models.PositiveBigIntegerField(default=0, verbose_name="Heures TP")
    volHoraire = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        self.volHoraire = (self.heures_cm or 0) + (self.heures_td or 0) + (self.heures_tp or 0)
        
        if not self.pk:
            super().save(*args, **kwargs)
    
        if not self.code:
            prefixe = "".join([mot[:3].upper() for mot in self.nom.split()])[:4]
            self.code = f"{prefixe}-{self.id}"
            kwargs['force_insert'] = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} ({self.volHoraire}h)"


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['nom','heures_cm','heures_td','heures_tp']
        widgets = {
            'nom':forms.TextInput(attrs={'class':'input input-bordered w-full'}),
            'heures_cm':forms.NumberInput(attrs={'class':'input input-bordered w-full','oninput':'CalculerVolumeHoraire()'}),
            'heures_td': forms.NumberInput(attrs={'class':'input input-bordered w-full','oninput':'CalculerVolumeHoraire()'}),
            'heures_tp':forms.NumberInput(attrs={'class':'input input-bordered w-full','oninput':'CalculerVolumeHoraire()'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        cm = cleaned_data.get('heures_cm') or 0
        td = cleaned_data.get('heures_td') or 0
        tp = cleaned_data.get('heures_tp') or 0
    
        cleaned_data['volHoraire'] = cm + td + tp
        
        return cleaned_data


class Emargement(models.Model):
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    date = models.DateField()
    arrivee = models.TimeField()
    depart = models.TimeField()
    module = models.ForeignKey(Module , on_delete=models.CASCADE , blank=True , null=True )
    classe = models.ForeignKey(Classe , on_delete=models.CASCADE , null=True)
    
    def __str__(self):
        return f"{self.enseignant} {self.date}"


class Absence(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    date = models.DateField()
    justifie = models.BooleanField(default=False)

    def justifier(self , motif):
        self.justifie = True
        self.save()


class Cahier(models.Model):
    emargement = models.OneToOneField(
        Emargement, 
        on_delete=models.CASCADE, 
        related_name="cahier_texte",
        null=True, 
        blank=True
    )
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
    classe = models.ForeignKey(
        Classe,on_delete=models.CASCADE, blank=True ,
        default=7
    )

    class Meta:
        unique_together = ("enseignant", "module", "annee_universitaire","classe")
    
    def __str__(self):
        return f"{self.enseignant}  {self.module}"


class AffectationForm(forms.ModelForm):
    class Meta:
        model = Affectation
        fields = ['enseignant', 'module', 'classe', 'annee_universitaire']
        
        widgets = {
            'enseignant': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'module': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'classe': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'annee_universitaire': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'maxlength': '20'}),
        }
        