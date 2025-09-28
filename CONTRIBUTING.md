# Contributing Guide

[English](#english-guide) | [Français](#guide-francais)

<a id="english-guide"></a>
## English Guide

Thank you for your interest in Meetinity! This guide outlines what we expect from contributors so everyone can collaborate effectively on building the best professional networking platform.

### 1. Before You Start

- Read the [Code of Conduct](CODE_OF_CONDUCT.md) and agree to follow it.
- Review the existing issues and roadmap in `docs/project-evaluation.md` and `TODO.md` to identify current priorities.
- Open an issue if you want to discuss a new feature or major change before you begin coding.

### 2. Set Up Your Environment

```bash
git clone https://github.com/decarvalhoe/meetinity.git
cd meetinity
make setup           # install development dependencies
make dev-up          # start PostgreSQL, Redis, and core services
```

Consult the `Makefile` and the `docs/` directory for other useful commands (tests, deployment scripts, etc.).

### 3. Git Strategy

- Use feature branches: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`.
- Keep `main` stable; use `develop` (if available) for intermediate integrations.
- Rebase regularly on `main` to limit conflicts.

### 4. Code Style and Commits

- Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) convention.
- For Python services: Follow PEP 8, use `black` for formatting, `flake8` for linting.
- For React applications: Use ESLint and Prettier configurations provided in each repository.
- Before pushing, run:

```bash
# For Python services
black . && flake8 .
pytest -q            # add tests when you modify or introduce features

# For React applications
npm run lint
npm run test
```

Document new APIs, environment variables, or configuration changes in the respective `README.md` files.

### 5. Submit a Pull Request

1. Ensure tests pass locally and CI runs cleanly.
2. Fill in the PR description with the motivation, implementation details, and potential impacts.
3. Attach screenshots or relevant logs if your change affects the UI or API behavior.
4. Mention related issues (`Fixes #123`, `Closes #456`).
5. Be ready to iterate based on review feedback.

### 6. Code Review

- Maintainers validate technical coherence, security, and documentation.
- Feedback must remain respectful and constructive; feel free to ask for clarifications.
- At least one approval is required for merging; two approvals for significant changes (architecture, data models, security).

### 7. Non-Code Contributions

Documentation improvements, translations, UX/UI design, and testing are equally appreciated. Please surface them via dedicated issues or discussions.

### 8. Repository-Specific Guidelines

Each repository has its own specific setup and contribution guidelines:

- **meetinity-mobile-app**: React 18 + TypeScript + Vite setup
- **meetinity-admin-portal**: React + TypeScript for admin interfaces
- **meetinity-user-service**: Flask + SQLAlchemy + OAuth implementation
- **meetinity-event-service**: Flask + event management logic
- **meetinity-matching-service**: Flask + matching algorithms
- **meetinity-api-gateway**: Flask + request routing and middleware

---

<a id="guide-francais"></a>
## Guide français

Merci de votre intérêt pour Meetinity ! Ce guide résume les attentes pour contribuer dans les meilleures conditions à la construction de la meilleure plateforme de réseautage professionnel.

### 1. Avant de commencer

- Lisez le [Code de conduite](CODE_OF_CONDUCT.md) et engagez-vous à le respecter.
- Parcourez les issues existantes et la feuille de route dans `docs/project-evaluation.md` et `TODO.md` pour identifier les priorités actuelles.
- Ouvrez une issue si vous souhaitez discuter d'une nouvelle fonctionnalité ou d'un changement majeur avant de démarrer le développement.

### 2. Préparer votre environnement

```bash
git clone https://github.com/decarvalhoe/meetinity.git
cd meetinity
make setup           # installe les dépendances de développement
make dev-up          # lance PostgreSQL, Redis et les services principaux
```

Consultez le `Makefile` et le dossier `docs/` pour d'autres commandes utiles (tests, scripts de déploiement, etc.).

### 3. Stratégie Git

- Branche par fonctionnalité : `feat/<slug>`, `fix/<slug>`, `chore/<slug>`.
- `main` : branche stable ; `develop` (si existante) pour les intégrations intermédiaires.
- Rebasez-vous régulièrement sur `main` pour limiter les conflits.

### 4. Style de code et commits

- Suivez les conventions [Conventional Commits](https://www.conventionalcommits.org/fr/v1.0.0/).
- Pour les services Python : Respectez PEP 8, utilisez `black` pour le formatage, `flake8` pour le linting.
- Pour les applications React : Utilisez les configurations ESLint et Prettier fournies dans chaque repository.
- Avant de pousser, exécutez :

```bash
# Pour les services Python
black . && flake8 .
pytest -q            # ajoutez des tests lorsqu'une fonctionnalité est modifiée ou introduite

# Pour les applications React
npm run lint
npm run test
```

Documentez les nouvelles APIs, variables d'environnement ou changements de configuration dans les fichiers `README.md` respectifs.

### 5. Soumettre une Pull Request

1. Vérifiez que les tests passent localement et que la CI s'exécute sans erreur.
2. Remplissez la description en expliquant la motivation, l'implémentation et les impacts éventuels.
3. Ajoutez des captures ou extraits de logs pertinents si votre changement touche l'UI ou le comportement de l'API.
4. Mentionnez les issues liées (`Fixes #123`, `Closes #456`).
5. Soyez prêt·e à itérer suite aux retours de revue.

### 6. Revue de code

- Les mainteneurs valident la cohérence technique, la sécurité et la documentation.
- Les retours doivent rester respectueux et constructifs ; n'hésitez pas à poser des questions.
- Une approbation minimum est requise pour merger ; deux approbations pour les changements significatifs (architecture, modèles de données, sécurité).

### 7. Contribution non-code

Les améliorations de documentation, traductions, design UX/UI et tests sont tout autant appréciées. Signalez-les via des issues dédiées ou des discussions.

### 8. Directives Spécifiques par Repository

Chaque repository a ses propres directives de configuration et contribution :

- **meetinity-mobile-app** : Configuration React 18 + TypeScript + Vite
- **meetinity-admin-portal** : React + TypeScript pour les interfaces d'administration
- **meetinity-user-service** : Flask + SQLAlchemy + implémentation OAuth
- **meetinity-event-service** : Flask + logique de gestion d'événements
- **meetinity-matching-service** : Flask + algorithmes de matching
- **meetinity-api-gateway** : Flask + routage de requêtes et middleware

---

Merci de contribuer à faire de Meetinity une plateforme de réseautage professionnel fiable et collaborative !
