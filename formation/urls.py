from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.page_accueil, name='accueil'),
    path('login/', views.connexion, name='connexion'),
    path('register/', views.inscription_view, name='inscription'),
    path('logout/', views.deconnexion, name='deconnexion'),

    # Dashboard & profil
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profil/', views.mon_profil, name='mon_profil'),

    # Catalogue
    path('formations/', views.catalogue_formations, name='catalogue_formations'),
    path('formations/<int:pk>/', views.detail_formation, name='detail_formation'),
    path('formations/<int:pk>/inscrire/', views.sinscrire_formation, name='sinscrire_formation'),

    # Gestion formations (formateur)
    path('mes-formations/', views.mes_formations, name='mes_formations'),
    path('formations/creer/', views.creer_formation, name='creer_formation'),
    path('formations/<int:pk>/modifier/', views.modifier_formation, name='modifier_formation'),
    path('formations/<int:pk>/supprimer/', views.supprimer_formation, name='supprimer_formation'),
    path('formations/<int:pk>/gerer/', views.gerer_formation, name='gerer_formation'),
    path('formations/<int:pk>/suivi/', views.suivi_candidats, name='suivi_candidats'),
    path('inscriptions/<int:insc_id>/attestation-accorder/', views.accorder_attestation, name='accorder_attestation'),

    # Modules
    path('formations/<int:formation_pk>/modules/ajouter/', views.ajouter_module, name='ajouter_module'),
    path('modules/<int:pk>/modifier/', views.modifier_module, name='modifier_module'),
    path('modules/<int:pk>/supprimer/', views.supprimer_module, name='supprimer_module'),

    # Cours
    path('modules/<int:module_pk>/cours/ajouter/', views.ajouter_cours, name='ajouter_cours'),
    path('cours/<int:pk>/modifier/', views.modifier_cours, name='modifier_cours'),
    path('cours/<int:pk>/supprimer/', views.supprimer_cours, name='supprimer_cours'),
    path('cours/<int:cours_pk>/voir/', views.voir_cours, name='voir_cours'),

    # Quiz
    path('modules/<int:module_pk>/quiz/ajouter/', views.ajouter_quiz, name='ajouter_quiz'),
    path('quiz/<int:pk>/gerer/', views.gerer_quiz, name='gerer_quiz'),
    path('quiz/<int:quiz_pk>/question/ajouter/', views.ajouter_question, name='ajouter_question'),
    path('quiz/<int:quiz_pk>/passer/', views.passer_quiz, name='passer_quiz'),
    path('quiz/resultats/<int:tentative_pk>/', views.resultat_quiz, name='resultat_quiz'),

    # Suivi candidat
    path('formations/<int:pk>/suivre/', views.suivre_formation, name='suivre_formation'),

    # Attestation
    path('attestation/<int:insc_id>/', views.voir_attestation, name='voir_attestation'),

    # Notifications
    path('notifications/', views.mes_notifications, name='mes_notifications'),
    path('notifications/<int:pk>/lue/', views.marquer_notif_lue, name='marquer_notif_lue'),
]
