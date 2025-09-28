# Liste de Tâches du Projet Meetinity

Ce document présente une liste de tâches dense et priorisée pour guider la prochaine phase de développement de la plateforme Meetinity. Elle est basée sur une évaluation complète de l'état actuel des repositories et des objectifs de l'application.

## EPIC 1: Solidifier l'Infrastructure et le DevOps

Cet épique se concentre sur la stabilisation de la base technique du projet, la résolution des problèmes critiques et la mise en place d'une automatisation complète.

### Tâche 1.1: Résoudre l'Intégration Critique de la Base de Données du User Service

*   **Description:** Le `user-service` présente une issue critique qui empêche la persistance correcte des données. Cette tâche exige une analyse approfondie de la configuration de SQLAlchemy et Alembic, le diagnostic des problèmes de connexion et de migration, et l'implémentation d'un correctif robuste. Cela inclut la rédaction de tests d'intégration complets pour valider la persistance des données après redémarrage du service et pour garantir que le schéma de la base de données de production est stable et correct.
*   **Livrables:** Code du `user-service` corrigé, suite de tests d'intégration réussie, documentation de la configuration de la base de données.
*   **Issue Associée:** `decarvalhoe/meetinity-user-service#14`

### Tâche 1.2: Implémenter un Pipeline CI/CD Complet pour Tous les Services

*   **Description:** Configurer les workflows GitHub Actions existants (`ci.yml`, `cd.yml`) avec les secrets et la logique de déploiement requis. Cela implique la création de scripts de déploiement (par exemple, en utilisant Docker, Kubernetes) pour chaque microservice et les applications frontend. Le pipeline doit automatiser la construction, les tests et le déploiement des services vers un environnement de staging à chaque push sur la branche `main`, et vers la production lors de la création d'un nouveau tag de version.
*   **Livrables:** Pipelines CI/CD entièrement opérationnels, scripts de déploiement, `README.md` mis à jour avec les instructions de déploiement.
*   **Issue Associée:** `decarvalhoe/meetinity#1`

### Tâche 1.3: Définir et Documenter l'Architecture des Données

*   **Description:** Créer un document complet détaillant les modèles de données pour chaque service, les relations entre eux, et la stratégie globale de flux et d'intégration des données. Cela inclut la définition de la "source de vérité" pour chaque donnée, les stratégies de synchronisation des données entre les services (par exemple, en utilisant des événements via Kafka), et la création de diagrammes entité-relation (ERD) détaillés.
*   **Livrables:** Un fichier `docs/data-architecture.md` avec des ERDs et des descriptions détaillées du flux de données.
*   **Issue Associée:** `decarvalhoe/meetinity#3`

## EPIC 2: Finaliser les Services Backend de Base (Event & Matching)

Cet épique vise à compléter les fonctionnalités de base des services `event-service` et `matching-service` pour les rendre pleinement opérationnels.

### Tâche 2.1: Finaliser l'Event Service avec Base de Données et Inscription

*   **Description:** Intégrer une base de données PostgreSQL en utilisant SQLAlchemy, implémenter Alembic pour les migrations, et construire le système d'inscription aux événements comme défini dans la spécification OpenAPI (`/events/{id}/join`). Cela inclut la création des modèles de base de données nécessaires, la logique de repository pour les opérations CRUD, et les endpoints pour que les utilisateurs puissent s'inscrire aux événements et que les organisateurs puissent voir les participants.
*   **Livrables:** `event-service` entièrement persistant, fonctionnalité d'inscription aux événements, couverture de test complète.
*   **Issue Associée:** `decarvalhoe/meetinity-event-service#1`

### Tâche 2.2: Compléter le Matching Service avec Swipe et Matching en Temps Réel

*   **Description:** Implémenter la fonctionnalité de swipe (`/swipe` endpoint) pour enregistrer les "likes" et "passes" des utilisateurs. Développer un système de détection de match en temps réel, potentiellement en utilisant des WebSockets ou une file d'attente de messages (comme Kafka), pour notifier immédiatement les utilisateurs lorsqu'un match mutuel se produit. Cela nécessite une intégration complète avec le `user-service` pour récupérer les profils pour l'algorithme de matching.
*   **Livrables:** API de swipe fonctionnelle, système de notification de match en temps réel, intégration avec le `user-service`.
*   **Issue Associée:** `decarvalhoe/meetinity-matching-service#1`

## EPIC 3: Implémenter les Fonctionnalités de Réseautage de l'Application Mobile

Cet épique se concentre sur la construction des fonctionnalités de base de l'application mobile qui permettent aux utilisateurs d'interagir et de se connecter.

### Tâche 3.1: Construire l'Interface de Découverte de Profils et de Swipe

*   **Description:** Créer la fonctionnalité principale de l'application pour la découverte d'autres professionnels. Cela implique la construction de l'écran "Découverte" qui récupère les profils du `matching-service`, les affiche dans une interface utilisateur basée sur des cartes (similaire à Tinder), et permet aux utilisateurs de swiper à gauche (passer) ou à droite (aimer). La gestion de l'état doit être robuste pour gérer efficacement le chargement des profils, les animations de swipe et les appels API.
*   **Livrables:** Écran "Découverte" avec des cartes de profil, implémentation du geste de swipe, intégration de l'API avec le `matching-service`.
*   **Issue Associée:** `decarvalhoe/meetinity-mobile-app#4`

### Tâche 3.2: Implémenter le Système de Matchs et de Messagerie

*   **Description:** Créer un écran "Matchs" qui affiche une liste des utilisateurs avec lesquels un match mutuel a été établi. À partir de cet écran, les utilisateurs devraient pouvoir entamer une conversation. Cela nécessite la construction d'une interface de messagerie complète, y compris un écran de liste de conversations et un écran de chat pour l'échange de messages en temps réel, en utilisant les endpoints définis dans la spécification OpenAPI (`/conversations`, `/messages`).
*   **Livrables:** Écran "Matchs", écran de liste de conversations, interface de chat en temps réel.
*   **Issue Associée:** `decarvalhoe/meetinity-mobile-app#4`

## EPIC 4: Améliorer l'API Gateway et le Portail d'Administration

Cet épique vise à ajouter des fonctionnalités avancées à l'API Gateway et à étendre les capacités du portail d'administration.

### Tâche 4.1: Implémenter des Fonctionnalités Avancées pour l'API Gateway

*   **Description:** Améliorer l'API Gateway en ajoutant des fonctionnalités critiques prêtes pour la production. Cela inclut l'implémentation de la limitation de débit (rate limiting) pour prévenir les abus, l'ajout d'une couche de cache (par exemple, avec Redis) pour les données fréquemment consultées et non sensibles, et l'implémentation d'une journalisation structurée (par exemple, au format JSON) pour une meilleure surveillance et analyse.
*   **Livrables:** Middleware de limitation de débit, mécanisme de mise en cache, implémentation de la journalisation structurée.
*   **Issue Associée:** `decarvalhoe/meetinity-api-gateway#4`

### Tâche 4.2: Étendre le Portail d'Administration avec la Gestion des Événements et du Contenu

*   **Description:** Étendre le portail d'administration au-delà de la gestion des utilisateurs. Construire des modules pour la gestion des événements (voir, modifier, supprimer) et pour la modération de contenu (par exemple, examiner les profils ou les messages signalés). Cela implique la création de nouveaux composants, services et routes au sein de l'application React.
*   **Livrables:** Tableau de bord de gestion des événements, outils de modération de contenu dans le portail d'administration.
*   **Issue Associée:** `decarvalhoe/meetinity-admin-portal#4`

## EPIC 5: Finaliser la Documentation et les Tests

Cet épique se concentre sur l'amélioration de la qualité globale du projet par le biais de tests approfondis et d'une documentation complète.

### Tâche 5.1: Atteindre une Couverture de Test Élevée sur Tous les Services

*   **Description:** Augmenter systématiquement la couverture des tests pour tous les microservices et les applications frontend. Cela inclut la rédaction de tests unitaires pour les fonctions et composants individuels, et de tests d'intégration pour les interactions entre services et les endpoints de l'API. L'objectif est d'atteindre un niveau de couverture élevé (par exemple, >80%) pour garantir la qualité du code et prévenir les régressions.
*   **Livrables:** Rapports de couverture de test améliorés, nouvelles suites de tests pour tous les repositories.

### Tâche 5.2: Générer une Documentation Complète de l'API et du Projet

*   **Description:** Créer un hub de documentation centralisé. Générer automatiquement la documentation de l'API à partir de la spécification OpenAPI et l'héberger. Rédiger des guides détaillés pour les développeurs sur des sujets tels que la configuration locale, l'architecture et les directives de contribution. S'assurer que le `README.md` de chaque repository est à jour et fournit des instructions claires.
*   **Livrables:** Documentation de l'API hébergée, guides complets pour les développeurs, READMEs mis à jour.

