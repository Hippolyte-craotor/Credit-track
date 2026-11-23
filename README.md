# AgriConnect

Plateforme web SaaS agricole mettant en relation **producteurs**, **acheteurs** et **transporteurs**.  
MVP construit avec **Django**, templates HTML/CSS/JS, et base de données configurable (SQLite par défaut, PostgreSQL prêt).

## Fonctionnalités MVP

- Authentification sécurisée (inscription, connexion, déconnexion).
- Rôles utilisateurs : Administrateur, Producteur, Acheteur, Transporteur.
- Profils utilisateurs adaptés au rôle.
- Publication et gestion de produits agricoles (photo, prix, quantité, localisation).
- Catalogue produits avec recherche et filtres (nom, catégorie, région, prix).
- Commandes avec suivi de statut (En attente, Confirmée, En livraison, Livrée, Annulée).
- Tableau de bord personnalisé par rôle.
- Tableau de bord administrateur avec statistiques.
- Données de démonstration réalistes.

## Stack technique

- **Backend** : Python / Django
- **Frontend** : HTML, CSS, JavaScript
- **Base de données** : SQLite (défaut dev) / PostgreSQL (configuration via variables d'environnement)
- **Médias** : Pillow pour les images produits

## Structure du projet

```text
.
├── config/                 # Configuration Django
├── accounts/               # Utilisateurs, rôles, profils, authentification
├── products/               # Produits, catalogue, recherche/filtres
├── orders/                 # Commandes et suivi de statut
├── dashboard/              # Tableaux de bord par rôle
├── templates/              # Templates HTML
├── static/                 # CSS / JS / assets
├── manage.py
└── requirements.txt
```

## Installation (local)

1. **Créer et activer un environnement virtuel** (recommandé)

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

2. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

3. **Configurer l'environnement** (optionnel)

Copiez `.env.example` en `.env` et adaptez les valeurs.

4. **Appliquer les migrations**

```bash
python manage.py migrate
```

5. **Charger les données de démonstration**

```bash
python manage.py seed_demo
```

6. **Lancer le serveur**

```bash
python manage.py runserver
```

Application : http://127.0.0.1:8000/

## Comptes de démonstration

Après `seed_demo` :

| Rôle | Utilisateur | Mot de passe |
|---|---|---|
| Administrateur | `admin` | `Admin12345!` |
| Producteur | `ama_prod` | `Demo12345!` |
| Producteur | `yaw_prod` | `Demo12345!` |
| Acheteur | `akua_buy` | `Demo12345!` |
| Acheteur | `kodjo_buy` | `Demo12345!` |
| Transporteur | `femi_trans` | `Demo12345!` |

## Configuration PostgreSQL

Par défaut, l'application utilise SQLite pour faciliter le développement local.  
Pour PostgreSQL, définissez les variables d'environnement :

```env
DB_ENGINE=postgres
POSTGRES_DB=agriconnect
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Notes MVP

- Les paiements Mobile Money ne sont pas encore intégrés (architecture prévue pour extension).
- La messagerie temps réel n'est pas incluse dans cette première version ; le contact passe par les informations de commande/profil.
- Les notifications sont actuellement gérées via les messages applicatifs et le suivi de statut.
- L'interface est responsive et pensée pour un usage mobile-first.

## Prochaines évolutions possibles

- Paiement Mobile Money.
- Messagerie interne / notifications push.
- Gestion avancée des livraisons et géolocalisation.
- API REST/GraphQL pour application mobile.
- Vérification KYC des utilisateurs et modération avancée.
