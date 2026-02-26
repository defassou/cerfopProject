from django.contrib import admin
from django.utils.html import format_html
from .models import *

admin.site.site_header = "CERFOP — Administration"
admin.site.site_title = "CNT / CERFOP"
admin.site.index_title = "Plateforme de Formation Parlementaire"


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'telephone', 'organisation']
    list_filter = ['role']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'formateur', 'statut', 'date_debut', 'date_fin', 'nb_inscrits']
    list_filter = ['statut', 'formateur']
    search_fields = ['titre', 'description']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['titre', 'formation', 'ordre']
    list_filter = ['formation']


@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ['titre', 'module', 'type_fichier', 'ordre']
    list_filter = ['type_fichier']


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ['candidat', 'formation', 'progression', 'attestation_accordee', 'date_inscription']
    list_filter = ['attestation_accordee', 'formation']
    actions = ['accorder_attestations']

    def accorder_attestations(self, request, queryset):
        import uuid
        from django.utils import timezone
        for insc in queryset:
            if not insc.numero_attestation:
                insc.numero_attestation = f"CERFOP/{timezone.now().year}/{str(uuid.uuid4())[:8].upper()}"
            insc.attestation_accordee = True
            insc.date_attestation = timezone.now()
            insc.save()
        self.message_user(request, f"{queryset.count()} attestation(s) accordée(s).")
    accorder_attestations.short_description = "Accorder les attestations sélectionnées"


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['titre', 'module', 'duree_minutes', 'nb_tentatives']


@admin.register(TentativeQuiz)
class TentativeQuizAdmin(admin.ModelAdmin):
    list_display = ['inscription', 'quiz', 'note', 'termine', 'date_debut']
    list_filter = ['termine', 'quiz__module__formation']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'destinataire', 'type_notif', 'lue', 'date_creation']
    list_filter = ['lue', 'type_notif']
