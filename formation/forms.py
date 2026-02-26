from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profil, Formation, Module, Cours, Quiz, Question, Choix


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(
        label='Nom d\'utilisateur',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'})
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'})
    )


class InscriptionForm(UserCreationForm):
    first_name = forms.CharField(
        label='Prénom', max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre prénom'})
    )
    last_name = forms.CharField(
        label='Nom', max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre@email.com'})
    )
    username = forms.CharField(
        label='Nom d\'utilisateur',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choisissez un identifiant'})
    )
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'})
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmez votre mot de passe'})
    )
    role = forms.ChoiceField(
        label='Rôle',
        choices=[('candidat', 'Candidat'), ('formateur', 'Formateur')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    telephone = forms.CharField(
        label='Téléphone', max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+224 XXX XXX XXX'})
    )
    organisation = forms.CharField(
        label='Organisation/Institution', max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre institution'})
    )
    poste = forms.CharField(
        label='Poste occupé', max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre fonction'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            Profil.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                telephone=self.cleaned_data.get('telephone', ''),
                organisation=self.cleaned_data.get('organisation', ''),
                poste=self.cleaned_data.get('poste', ''),
            )
        return user


class ProfilForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Prénom', max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Nom', max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Profil
        fields = ['photo', 'telephone', 'bio', 'date_naissance', 'adresse', 'organisation', 'poste']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'organisation': forms.TextInput(attrs={'class': 'form-control'}),
            'poste': forms.TextInput(attrs={'class': 'form-control'}),
        }


class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = ['titre', 'description', 'image', 'date_debut', 'date_fin',
                  'duree_heures', 'statut', 'note_passage', 'objectifs', 'public_cible']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la formation'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duree_heures': forms.NumberInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'note_passage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'objectifs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'public_cible': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['titre', 'description', 'ordre']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ['titre', 'description', 'type_fichier', 'fichier', 'contenu_texte', 'ordre', 'duree_minutes']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'type_fichier': forms.Select(attrs={'class': 'form-control'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'contenu_texte': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
            'duree_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['titre', 'description', 'duree_minutes', 'nb_tentatives']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'duree_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'nb_tentatives': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['texte', 'type_question', 'points', 'ordre']
        widgets = {
            'texte': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_question': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ChoixForm(forms.ModelForm):
    class Meta:
        model = Choix
        fields = ['texte', 'est_correct', 'ordre']
        widgets = {
            'texte': forms.TextInput(attrs={'class': 'form-control'}),
            'est_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),
        }
