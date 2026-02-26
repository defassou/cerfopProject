from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.views.decorators.http import require_POST
import uuid
import json

from .models import (Profil, Formation, Module, Cours, Inscription,
                     ProgresCoursCandidat, Quiz, Question, Choix,
                     TentativeQuiz, ReponseCandidat, Notification)
from .forms import (ConnexionForm, InscriptionForm, ProfilForm,
                    FormationForm, ModuleForm, CoursForm, QuizForm, QuestionForm, ChoixForm)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_profil(user):
    profil, _ = Profil.objects.get_or_create(user=user, defaults={'role': 'candidat'})
    return profil


def notifier(user, titre, message, type_notif='info', lien=''):
    Notification.objects.create(
        destinataire=user, titre=titre, message=message,
        type_notif=type_notif, lien=lien
    )


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def page_accueil(request):
    features = [
        {
            "icon": "📄",
            "title": "Supports variés",
            "desc": "PDF, Word, PowerPoint, vidéos",
            "color": "or"
        },
        {
            "icon": "📝",
            "title": "Quiz d'évaluation",
            "desc": "Évaluez vos connaissances à chaque étape",
            "color": "bleu"
        },
        {
            "icon": "🏅",
            "title": "Attestations officielles",
            "desc": "Imprimez votre attestation CNT/CERFOP",
            "color": "vert"
        }
    ]
    if request.user.is_authenticated:
        return redirect('dashboard')

    formations = Formation.objects.filter(statut='publie')[:6]
    return render(request, 'formation/accueil.html', {'formations': formations, 'features': features})


def connexion(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = ConnexionForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Bienvenue, {user.get_full_name() or user.username} !")
        return redirect('dashboard')
    return render(request, 'formation/connexion.html', {'form': form})


def inscription_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = InscriptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Compte créé avec succès ! Bienvenue sur la plateforme CERFOP.")
        return redirect('dashboard')
    return render(request, 'formation/inscription.html', {'form': form})


@login_required
def deconnexion(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('connexion')


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    profil = get_profil(request.user)
    notifs = Notification.objects.filter(destinataire=request.user, lue=False)[:5]
    ctx = {'profil': profil, 'notifs': notifs, 'nb_notifs': notifs.count()}

    if profil.is_formateur():
        formations = Formation.objects.filter(formateur=request.user)
        total_inscrits = sum(f.nb_inscrits() for f in formations)
        ctx.update({
            'formations': formations[:5],
            'total_formations': formations.count(),
            'total_inscrits': total_inscrits,
            'formations_publiees': formations.filter(statut='publie').count(),
        })
        return render(request, 'formation/dashboard_formateur.html', ctx)
    else:
        inscriptions = Inscription.objects.filter(candidat=request.user, active=True).select_related('formation')
        ctx.update({
            'inscriptions': inscriptions,
            'nb_formations': inscriptions.count(),
            'nb_terminees': inscriptions.filter(progression=100).count(),
            'nb_attestations': inscriptions.filter(attestation_accordee=True).count(),
        })
        return render(request, 'formation/dashboard_candidat.html', ctx)


# ─── PROFIL ───────────────────────────────────────────────────────────────────

@login_required
def mon_profil(request):
    profil = get_profil(request.user)
    form = ProfilForm(request.POST or None, request.FILES or None, instance=profil)
    if request.method == 'POST':
        form_valid = form.is_valid()
        if form_valid:
            p = form.save()
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.email = request.POST.get('email', request.user.email)
            request.user.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('mon_profil')
    return render(request, 'formation/profil.html', {'form': form, 'profil': profil})


# ─── FORMATIONS (FORMATEUR) ───────────────────────────────────────────────────

@login_required
def mes_formations(request):
    profil = get_profil(request.user)
    if not profil.is_formateur():
        return redirect('catalogue_formations')
    formations = Formation.objects.filter(formateur=request.user).annotate(
        nb_inscrits_count=Count('inscriptions', filter=Q(inscriptions__active=True))
    )
    return render(request, 'formation/mes_formations.html', {'formations': formations, 'profil': profil})


@login_required
def creer_formation(request):
    profil = get_profil(request.user)
    if not profil.is_formateur():
        messages.error(request, "Seuls les formateurs peuvent créer des formations.")
        return redirect('dashboard')
    form = FormationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        formation = form.save(commit=False)
        formation.formateur = request.user
        formation.save()
        messages.success(request, f"Formation « {formation.titre} » créée avec succès.")
        return redirect('gerer_formation', pk=formation.pk)
    return render(request, 'formation/creer_formation.html', {'form': form, 'profil': profil})


@login_required
def modifier_formation(request, pk):
    formation = get_object_or_404(Formation, pk=pk, formateur=request.user)
    form = FormationForm(request.POST or None, request.FILES or None, instance=formation)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Formation mise à jour.")
        return redirect('gerer_formation', pk=pk)
    return render(request, 'formation/modifier_formation.html', {'form': form, 'formation': formation})


@login_required
def supprimer_formation(request, pk):
    formation = get_object_or_404(Formation, pk=pk, formateur=request.user)
    if request.method == 'POST':
        titre = formation.titre
        formation.delete()
        messages.success(request, f"Formation « {titre} » supprimée.")
        return redirect('mes_formations')
    return render(request, 'formation/confirmer_suppression.html', {'objet': formation, 'type': 'formation'})


@login_required
def gerer_formation(request, pk):
    profil = get_profil(request.user)
    formation = get_object_or_404(Formation, pk=pk, formateur=request.user)
    modules = formation.modules.prefetch_related('cours', 'quiz')
    inscriptions = Inscription.objects.filter(formation=formation, active=True).select_related(
        'candidat', 'candidat__profil'
    )
    return render(request, 'formation/gerer_formation.html', {
        'formation': formation, 'modules': modules,
        'inscriptions': inscriptions, 'profil': profil
    })


@login_required
def suivi_candidats(request, pk):
    formation = get_object_or_404(Formation, pk=pk, formateur=request.user)
    inscriptions = Inscription.objects.filter(formation=formation, active=True).select_related(
        'candidat', 'candidat__profil'
    )
    for insc in inscriptions:
        insc.progression = insc.calculer_progression()
        insc.save()
    return render(request, 'formation/suivi_candidats.html', {
        'formation': formation, 'inscriptions': inscriptions
    })


@login_required
def accorder_attestation(request, insc_id):
    inscription = get_object_or_404(Inscription, pk=insc_id)
    if inscription.formation.formateur != request.user:
        messages.error(request, "Non autorisé.")
        return redirect('dashboard')
    if not inscription.numero_attestation:
        inscription.numero_attestation = f"CERFOP/{timezone.now().year}/{str(uuid.uuid4())[:8].upper()}"
    inscription.attestation_accordee = True
    inscription.date_attestation = timezone.now()
    inscription.save()
    notifier(
        inscription.candidat,
        "🏅 Attestation accordée !",
        f"Félicitations ! Votre attestation pour la formation « {inscription.formation.titre} » est disponible.",
        type_notif='attestation',
        lien=f'/attestation/{inscription.pk}/'
    )
    messages.success(request, f"Attestation accordée à {inscription.candidat.get_full_name()}.")
    return redirect('suivi_candidats', pk=inscription.formation.pk)


# ─── MODULES ──────────────────────────────────────────────────────────────────

@login_required
def ajouter_module(request, formation_pk):
    formation = get_object_or_404(Formation, pk=formation_pk, formateur=request.user)
    form = ModuleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        module = form.save(commit=False)
        module.formation = formation
        module.save()
        messages.success(request, f"Module « {module.titre} » ajouté.")
        return redirect('gerer_formation', pk=formation_pk)
    return render(request, 'formation/ajouter_module.html', {'form': form, 'formation': formation})


@login_required
def modifier_module(request, pk):
    module = get_object_or_404(Module, pk=pk, formation__formateur=request.user)
    form = ModuleForm(request.POST or None, instance=module)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Module mis à jour.")
        return redirect('gerer_formation', pk=module.formation.pk)
    return render(request, 'formation/ajouter_module.html', {'form': form, 'formation': module.formation, 'edit': True})


@login_required
def supprimer_module(request, pk):
    module = get_object_or_404(Module, pk=pk, formation__formateur=request.user)
    formation_pk = module.formation.pk
    if request.method == 'POST':
        module.delete()
        messages.success(request, "Module supprimé.")
        return redirect('gerer_formation', pk=formation_pk)
    return render(request, 'formation/confirmer_suppression.html', {'objet': module, 'type': 'module', 'retour_pk': formation_pk})


# ─── COURS ────────────────────────────────────────────────────────────────────

@login_required
def ajouter_cours(request, module_pk):
    module = get_object_or_404(Module, pk=module_pk, formation__formateur=request.user)
    form = CoursForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        cours = form.save(commit=False)
        cours.module = module
        cours.save()
        messages.success(request, f"Cours « {cours.titre} » ajouté.")
        return redirect('gerer_formation', pk=module.formation.pk)
    return render(request, 'formation/ajouter_cours.html', {'form': form, 'module': module})


@login_required
def modifier_cours(request, pk):
    cours = get_object_or_404(Cours, pk=pk, module__formation__formateur=request.user)
    form = CoursForm(request.POST or None, request.FILES or None, instance=cours)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Cours mis à jour.")
        return redirect('gerer_formation', pk=cours.module.formation.pk)
    return render(request, 'formation/ajouter_cours.html', {'form': form, 'module': cours.module, 'edit': True})


@login_required
def supprimer_cours(request, pk):
    cours = get_object_or_404(Cours, pk=pk, module__formation__formateur=request.user)
    formation_pk = cours.module.formation.pk
    if request.method == 'POST':
        cours.delete()
        messages.success(request, "Cours supprimé.")
        return redirect('gerer_formation', pk=formation_pk)
    return render(request, 'formation/confirmer_suppression.html', {'objet': cours, 'type': 'cours', 'retour_pk': formation_pk})


# ─── QUIZ ─────────────────────────────────────────────────────────────────────

@login_required
def ajouter_quiz(request, module_pk):
    module = get_object_or_404(Module, pk=module_pk, formation__formateur=request.user)
    form = QuizForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        quiz = form.save(commit=False)
        quiz.module = module
        quiz.save()
        messages.success(request, f"Quiz « {quiz.titre} » créé.")
        return redirect('gerer_quiz', pk=quiz.pk)
    return render(request, 'formation/ajouter_quiz.html', {'form': form, 'module': module})


@login_required
def gerer_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, module__formation__formateur=request.user)
    questions = quiz.questions.prefetch_related('choix')
    return render(request, 'formation/gerer_quiz.html', {'quiz': quiz, 'questions': questions})


@login_required
def ajouter_question(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk, module__formation__formateur=request.user)
    q_form = QuestionForm(request.POST or None)
    if request.method == 'POST' and q_form.is_valid():
        question = q_form.save(commit=False)
        question.quiz = quiz
        question.save()
        # Sauvegarder les choix
        choix_texts = request.POST.getlist('choix_texte')
        choix_corrects = request.POST.getlist('choix_correct')
        for i, texte in enumerate(choix_texts):
            if texte.strip():
                Choix.objects.create(
                    question=question,
                    texte=texte.strip(),
                    est_correct=(str(i) in choix_corrects),
                    ordre=i + 1
                )
        messages.success(request, "Question ajoutée.")
        return redirect('gerer_quiz', pk=quiz_pk)
    return render(request, 'formation/ajouter_question.html', {'q_form': q_form, 'quiz': quiz})


# ─── CATALOGUE & INSCRIPTION ─────────────────────────────────────────────────

def catalogue_formations(request):
    q = request.GET.get('q', '')
    formations = Formation.objects.filter(statut='publie')
    if q:
        formations = formations.filter(Q(titre__icontains=q) | Q(description__icontains=q))
    return render(request, 'formation/catalogue.html', {'formations': formations, 'q': q})


@login_required
def detail_formation(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    profil = get_profil(request.user)
    inscription = None
    if profil.is_candidat():
        inscription = Inscription.objects.filter(candidat=request.user, formation=formation).first()
    modules = formation.modules.prefetch_related('cours', 'quiz')
    return render(request, 'formation/detail_formation.html', {
        'formation': formation, 'inscription': inscription,
        'modules': modules, 'profil': profil
    })


@login_required
def sinscrire_formation(request, pk):
    formation = get_object_or_404(Formation, pk=pk, statut='publie')
    profil = get_profil(request.user)
    if not profil.is_candidat():
        messages.error(request, "Seuls les candidats peuvent s'inscrire.")
        return redirect('detail_formation', pk=pk)
    insc, created = Inscription.objects.get_or_create(
        candidat=request.user, formation=formation,
        defaults={'active': True}
    )
    if created:
        messages.success(request, f"Inscription confirmée pour « {formation.titre} ».")
        notifier(
            formation.formateur,
            "Nouvel inscrit",
            f"{request.user.get_full_name()} vient de s'inscrire à la formation « {formation.titre} ».",
            type_notif='info'
        )
    else:
        messages.info(request, "Vous êtes déjà inscrit(e) à cette formation.")
    return redirect('suivre_formation', pk=pk)


# ─── SUIVI FORMATION (CANDIDAT) ───────────────────────────────────────────────

@login_required
def suivre_formation(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    inscription = get_object_or_404(Inscription, candidat=request.user, formation=formation, active=True)
    modules = formation.modules.prefetch_related('cours', 'quiz')

    # Cours terminés par ce candidat
    cours_termines_ids = ProgresCoursCandidat.objects.filter(
        inscription=inscription, termine=True
    ).values_list('cours_id', flat=True)

    inscription.progression = inscription.calculer_progression()
    inscription.save()

    return render(request, 'formation/suivre_formation.html', {
        'formation': formation,
        'inscription': inscription,
        'modules': modules,
        'cours_termines_ids': list(cours_termines_ids),
    })


@login_required
def voir_cours(request, cours_pk):
    cours = get_object_or_404(Cours, pk=cours_pk)
    formation = cours.module.formation
    inscription = get_object_or_404(Inscription, candidat=request.user, formation=formation, active=True)

    # Marquer comme commencé/terminé
    progres, created = ProgresCoursCandidat.objects.get_or_create(
        inscription=inscription, cours=cours
    )
    if not progres.termine:
        progres.termine = True
        progres.date_fin = timezone.now()
        progres.save()

    # Recalculer progression
    inscription.progression = inscription.calculer_progression()
    inscription.save()

    # Vérifier si attestation peut être accordée
    if inscription.progression == 100 and inscription.peut_obtenir_attestation():
        notifier(
            formation.formateur,
            f"Candidat éligible à l'attestation",
            f"{request.user.get_full_name()} a terminé la formation « {formation.titre} » avec une note suffisante.",
            type_notif='succes'
        )

    return render(request, 'formation/voir_cours.html', {
        'cours': cours, 'formation': formation,
        'inscription': inscription, 'progres': progres
    })


@login_required
def passer_quiz(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    formation = quiz.module.formation
    inscription = get_object_or_404(Inscription, candidat=request.user, formation=formation, active=True)

    nb_tentatives = TentativeQuiz.objects.filter(inscription=inscription, quiz=quiz, termine=True).count()
    if nb_tentatives >= quiz.nb_tentatives:
        messages.warning(request, f"Vous avez atteint le nombre maximum de tentatives ({quiz.nb_tentatives}).")
        return redirect('suivre_formation', pk=formation.pk)

    tentative, created = TentativeQuiz.objects.get_or_create(
        inscription=inscription, quiz=quiz, termine=False
    )

    questions = quiz.questions.prefetch_related('choix')

    if request.method == 'POST':
        total_points = 0
        points_obtenus = 0

        for question in questions:
            total_points += question.points
            choix_id = request.POST.get(f'question_{question.pk}')
            texte_rep = request.POST.get(f'texte_{question.pk}', '')

            choix = None
            est_correct = False

            if question.type_question == 'qcm' and choix_id:
                try:
                    choix = Choix.objects.get(pk=choix_id, question=question)
                    est_correct = choix.est_correct
                    if est_correct:
                        points_obtenus += question.points
                except Choix.DoesNotExist:
                    pass
            elif question.type_question == 'vrai_faux' and choix_id:
                try:
                    choix = Choix.objects.get(pk=choix_id, question=question)
                    est_correct = choix.est_correct
                    if est_correct:
                        points_obtenus += question.points
                except Choix.DoesNotExist:
                    pass

            ReponseCandidat.objects.update_or_create(
                tentative=tentative, question=question,
                defaults={'choix_selectionne': choix, 'texte_reponse': texte_rep, 'est_correct': est_correct}
            )

        note = (points_obtenus / total_points * 100) if total_points > 0 else 0
        tentative.note = round(note, 2)
        tentative.termine = True
        tentative.date_fin = timezone.now()
        tentative.save()

        messages.success(request, f"Quiz soumis ! Votre note : {note:.1f}%")
        return redirect('resultat_quiz', tentative_pk=tentative.pk)

    return render(request, 'formation/passer_quiz.html', {
        'quiz': quiz, 'questions': questions,
        'tentative': tentative, 'inscription': inscription
    })


@login_required
def resultat_quiz(request, tentative_pk):
    tentative = get_object_or_404(TentativeQuiz, pk=tentative_pk, inscription__candidat=request.user)
    reponses = tentative.reponses.select_related('question', 'choix_selectionne').prefetch_related('question__choix')
    return render(request, 'formation/resultat_quiz.html', {
        'tentative': tentative, 'reponses': reponses
    })


# ─── ATTESTATION ──────────────────────────────────────────────────────────────

@login_required
def voir_attestation(request, insc_id):
    inscription = get_object_or_404(Inscription, pk=insc_id, attestation_accordee=True)
    # Seul le candidat concerné ou le formateur peuvent voir
    if request.user != inscription.candidat and request.user != inscription.formation.formateur:
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')
    return render(request, 'formation/attestation.html', {'inscription': inscription})


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

@login_required
def mes_notifications(request):
    notifs = Notification.objects.filter(destinataire=request.user)
    notifs.filter(lue=False).update(lue=True)
    return render(request, 'formation/notifications.html', {'notifs': notifs})


@login_required
def marquer_notif_lue(request, pk):
    notif = get_object_or_404(Notification, pk=pk, destinataire=request.user)
    notif.lue = True
    notif.save()
    return JsonResponse({'status': 'ok'})
