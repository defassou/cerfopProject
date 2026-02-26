from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


class Profil(models.Model):
    ROLE_CHOICES = [('formateur', 'Formateur'), ('candidat', 'Candidat')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidat')
    telephone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='profils/', blank=True, null=True)
    bio = models.TextField(blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    adresse = models.TextField(blank=True)
    organisation = models.CharField(max_length=200, blank=True)
    poste = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

    def is_formateur(self):
        return self.role == 'formateur'

    def is_candidat(self):
        return self.role == 'candidat'


class Formation(models.Model):
    STATUT_CHOICES = [('brouillon', 'Brouillon'), ('publie', 'Publié'), ('archive', 'Archivé')]
    titre = models.CharField(max_length=200)
    description = models.TextField()
    formateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='formations_crees')
    image = models.ImageField(upload_to='formations/images/', blank=True, null=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    duree_heures = models.PositiveIntegerField(default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    date_creation = models.DateTimeField(auto_now_add=True)
    note_passage = models.PositiveIntegerField(default=50, help_text="Note minimale pour l'attestation (%)")
    objectifs = models.TextField(blank=True)
    public_cible = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'

    def __str__(self):
        return self.titre

    def nb_inscrits(self):
        return self.inscriptions.filter(active=True).count()

    def nb_modules(self):
        return self.modules.count()

    def nb_cours(self):
        return sum(m.cours.count() for m in self.modules.all())


class Module(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='modules')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=1)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Module'

    def __str__(self):
        return f"{self.formation.titre} - Module {self.ordre}: {self.titre}"


def upload_cours(instance, filename):
    return f'cours/{instance.module.formation.id}/module_{instance.module.id}/{filename}'


class Cours(models.Model):
    TYPE_CHOICES = [
        ('pdf', 'PDF'), ('word', 'Word (.docx)'),
        ('powerpoint', 'PowerPoint (.pptx)'), ('video', 'Vidéo'), ('texte', 'Contenu texte')
    ]
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='cours')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type_fichier = models.CharField(max_length=20, choices=TYPE_CHOICES, default='pdf')
    fichier = models.FileField(upload_to=upload_cours, blank=True, null=True)
    contenu_texte = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=1)
    duree_minutes = models.PositiveIntegerField(default=0)
    date_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'

    def __str__(self):
        return self.titre

    def get_icon(self):
        icons = {'pdf': '📄', 'word': '📝', 'powerpoint': '📊', 'video': '🎬', 'texte': '📖'}
        return icons.get(self.type_fichier, '📁')

    def get_color(self):
        colors = {'pdf': '#e74c3c', 'word': '#2980b9', 'powerpoint': '#e67e22', 'video': '#8e44ad', 'texte': '#27ae60'}
        return colors.get(self.type_fichier, '#7f8c8d')

    def get_extension(self):
        if self.fichier:
            return os.path.splitext(self.fichier.name)[1].lower()
        return ''

    def taille_fichier(self):
        if self.fichier:
            try:
                size = self.fichier.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size // 1024} KB"
                else:
                    return f"{size // (1024 * 1024)} MB"
            except:
                return "N/A"
        return ""


class Inscription(models.Model):
    candidat = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscriptions')
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='inscriptions')
    date_inscription = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    progression = models.PositiveIntegerField(default=0)  # %
    attestation_accordee = models.BooleanField(default=False)
    date_attestation = models.DateTimeField(null=True, blank=True)
    note_finale = models.FloatField(null=True, blank=True)
    numero_attestation = models.CharField(max_length=50, blank=True, unique=True, null=True)

    class Meta:
        unique_together = ['candidat', 'formation']
        verbose_name = 'Inscription'

    def __str__(self):
        return f"{self.candidat.get_full_name()} → {self.formation.titre}"

    def calculer_progression(self):
        total_cours = sum(m.cours.count() for m in self.formation.modules.all())
        if total_cours == 0:
            return 0
        cours_termines = self.progres.filter(termine=True).count()
        return int((cours_termines / total_cours) * 100)

    def peut_obtenir_attestation(self):
        if self.calculer_progression() < 100:
            return False
        evals = self.evaluations_candidat.all()
        if not evals.exists():
            return True
        moyenne = sum(e.note for e in evals) / evals.count()
        return moyenne >= self.formation.note_passage

    def get_moyenne(self):
        evals = self.evaluations_candidat.all()
        if not evals.exists():
            return None
        return round(sum(e.note for e in evals) / evals.count(), 2)


class ProgresCoursCandidat(models.Model):
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, related_name='progres')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    termine = models.BooleanField(default=False)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['inscription', 'cours']

    def __str__(self):
        return f"{self.inscription.candidat.get_full_name()} - {self.cours.titre}"


class Quiz(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quiz')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duree_minutes = models.PositiveIntegerField(default=30)
    nb_tentatives = models.PositiveIntegerField(default=3)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quiz'

    def __str__(self):
        return f"Quiz: {self.titre} ({self.module.titre})"


class Question(models.Model):
    TYPE_CHOICES = [('qcm', 'QCM'), ('vrai_faux', 'Vrai/Faux'), ('texte_libre', 'Texte libre')]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    texte = models.TextField()
    type_question = models.CharField(max_length=20, choices=TYPE_CHOICES, default='qcm')
    points = models.PositiveIntegerField(default=1)
    ordre = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"Q{self.ordre}: {self.texte[:50]}"


class Choix(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choix')
    texte = models.CharField(max_length=500)
    est_correct = models.BooleanField(default=False)
    ordre = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"{'✓' if self.est_correct else '✗'} {self.texte[:40]}"


class TentativeQuiz(models.Model):
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE, related_name='evaluations_candidat')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='tentatives')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    note = models.FloatField(default=0)
    termine = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Tentative de quiz'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.inscription.candidat.get_full_name()} - {self.quiz.titre} ({self.note}%)"


class ReponseCandidat(models.Model):
    tentative = models.ForeignKey(TentativeQuiz, on_delete=models.CASCADE, related_name='reponses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choix_selectionne = models.ForeignKey(Choix, on_delete=models.CASCADE, null=True, blank=True)
    texte_reponse = models.TextField(blank=True)
    est_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ['tentative', 'question']


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'), ('succes', 'Succès'), ('alerte', 'Alerte'), ('attestation', 'Attestation')
    ]
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_notif = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    lien = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"[{self.type_notif}] {self.titre} → {self.destinataire.get_full_name()}"
