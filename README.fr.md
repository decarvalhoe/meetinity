# Projet Meetinity

**Meetinity** est une plateforme de networking professionnel conçue pour aider les utilisateurs à se connecter, découvrir des événements et développer leur réseau professionnel. Ce repository sert de point d'entrée principal pour le projet, fournissant une vue d'ensemble complète de l'architecture et des différents services qui composent la plateforme.

## Vue d'ensemble du projet

La plateforme Meetinity est construite sur une architecture microservices, avec une application mobile basée sur React et un portail d'administration. Le projet est divisé en sept repositories principaux, chacun responsable d'une partie spécifique de la plateforme.

### Architecture

L'architecture du projet est définie par la spécification OpenAPI située dans le répertoire `contracts`. Cette spécification détaille tous les points d'accès disponibles, les modèles de données et les interactions entre les différents services.

### Repositories

Voici une liste des repositories qui composent le projet Meetinity, ainsi qu'une brève description de leur rôle et de leur état actuel :

| Repository | Description | État |
|---|---|---|
| **meetinity** | Repository principal contenant les contrats de l'API (OpenAPI) et ce README principal. | 15% - Spécifications définies, pas d'implémentation. |
| **meetinity-mobile-app** | Une application mobile construite avec React, permettant aux utilisateurs d'interagir avec la plateforme. | 70% - Application fonctionnelle avec authentification OAuth. |
| **meetinity-admin-portal** | Un portail d'administration pour la gestion de la plateforme, construit avec React. | 60% - Interface d'administration avec des composants de visualisation de données. |
| **meetinity-api-gateway** | Une passerelle API construite avec Flask, responsable du routage des requêtes vers les microservices appropriés. | 40% - Structure de base avec middleware JWT implémenté. |
| **meetinity-user-service** | Un service de gestion des utilisateurs construit avec Flask, gérant l'authentification et les profils utilisateurs. | 80% - Service complet avec OAuth et JWT. |
| **meetinity-matching-service** | Un service de mise en relation des utilisateurs en fonction de leurs profils et de leurs intérêts, construit avec Flask. | 25% - Logique de base implémentée avec des données fictives. |
| **meetinity-event-service** | Un service de gestion des événements professionnels, construit avec Flask. | 35% - API REST de base avec validation des données. |

## Pour commencer

Pour commencer avec le projet Meetinity, vous devrez cloner chacun des repositories listés ci-dessus. Vous pouvez ensuite suivre les instructions dans le fichier README de chaque repository pour installer les dépendances et lancer les services.

## Avancement global

- **Frontend** : 65% (Application mobile + Portail d'administration)
- **Backend** : 45% (Services API)
- **Infrastructure** : 20% (Pas encore de déploiement configuré)
- **Documentation** : 40% (Spécifications API et documentation partielle du code)

**Avancement global estimé : 45%**

Le projet dispose d'une base solide avec une architecture bien définie et des composants fonctionnels. L'effort principal doit maintenant se concentrer sur l'intégration des services avec une base de données réelle et la mise en place de l'environnement de production.

Pour suivre l'état des issues Git et des sujets récemment clôturés, consultez le [résumé dédié](docs/issues.md).

