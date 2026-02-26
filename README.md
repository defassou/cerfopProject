# CERFOP — Plateforme de Formation Parlementaire
## CNT — Conseil National de la Transition — République de Guinée

## Installation

```bash
# 1. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Créer les migrations
python manage.py makemigrations
python manage.py migrate

# 4. Créer le superadmin
python manage.py createsuperuser

# 5. Lancer le serveur
python manage.py runserver
```

## Accès
- **Site** : http://localhost:8000
- **Admin** : http://localhost:8000/admin

## Fonctionnalités
### Formateur
- Créer/gérer des formations avec modules et cours
- Téléverser PDF, Word (.docx), PowerPoint (.pptx)
- Créer des quiz d'évaluation avec QCM
- Suivre la progression de chaque candidat
- Octroyer des attestations officielles

### Candidat
- S'inscrire et suivre les formations
- Accéder aux supports de cours
- Passer les quiz d'évaluation
- Imprimer l'attestation officielle CNT/CERFOP

## Structure
```
cerfop/
├── cerfop/          # Configuration Django
├── formation/       # Application principale
│   ├── models.py    # Modèles de données
│   ├── views.py     # Logique métier
│   ├── urls.py      # Routage
│   ├── forms.py     # Formulaires
│   ├── admin.py     # Interface admin
│   ├── templates/   # Templates HTML
│   └── static/      # CSS, JS, Images
├── media/           # Fichiers uploadés
└── manage.py
```
