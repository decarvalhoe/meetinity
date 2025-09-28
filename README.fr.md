[English](README.md) | [Français](README.fr.md)

# 🤝 Meetinity - Plateforme de Réseautage Professionnel

Une plateforme moderne de réseautage professionnel conçue pour aider les utilisateurs à **se connecter**, **découvrir des événements**, et **développer leur réseau professionnel**. Ce projet open-source permet de créer des relations professionnelles significatives grâce à des algorithmes de matching intelligents et à la découverte d'événements.

## 🎯 Qu'est-ce que Meetinity ?

Meetinity est une plateforme de réseautage complète qui vous permet de :

- **Vous connecter avec des professionnels** grâce à des algorithmes de matching intelligents
- **Découvrir des événements pertinents** dans votre secteur et votre région
- **Construire des relations significatives** avec des professionnels partageant vos intérêts
- **Gérer votre profil professionnel** avec une authentification OAuth sécurisée

### Pourquoi choisir Meetinity ?

- ✅ **Architecture Moderne** : Microservices évolutifs avec interfaces React
- ✅ **Authentification Sécurisée** : OAuth 2.0 avec intégration Google et LinkedIn
- ✅ **Matching Intelligent** : Algorithmes avancés pour les connexions professionnelles
- ✅ **Découverte d'Événements** : Système complet de gestion et découverte d'événements
- ✅ **Open Source** : Développement transparent et communautaire

## 🚀 État du Projet

### Phase 1 : Authentification & Infrastructure de Base (✅ Terminée - 80%)
**Objectif** : Établir une gestion sécurisée des utilisateurs et l'infrastructure de base

- ✅ **Authentification OAuth** : Intégration Google et LinkedIn avec JWT
- ✅ **Gestion des Profils** : Opérations CRUD complètes pour les profils utilisateur
- ✅ **Application Mobile** : App React avec interface d'authentification
- ✅ **Portail Admin** : Dashboard de gestion utilisateur avec filtres et analytics
- ✅ **API Gateway** : Routage des requêtes et middleware JWT

*Résultat* : Fondation solide avec authentification sécurisée et gestion utilisateur.

### Phase 2 : Gestion des Événements (🔄 En Cours - 35%)
**Objectif** : Permettre la création, découverte et inscription aux événements

- 🔄 **Service Événements** : API REST avec validation (nécessite intégration BDD)
- 📋 **Inscription aux Événements** : Enregistrement et suivi de participation
- 📋 **Découverte d'Événements** : Recherche et filtrage avancés

*Résultat Attendu* : Les utilisateurs pourront créer, découvrir et s'inscrire à des événements professionnels.

### Phase 3 : Matching Professionnel (🔄 En Cours - 25%)
**Objectif** : Connecter les professionnels via des algorithmes intelligents

- 🔄 **Algorithmes de Matching** : Scoring de compatibilité basé sur les profils
- 📋 **Interface Swipe** : Interaction type Tinder pour connexions professionnelles
- 📋 **Matching Temps Réel** : Notifications instantanées pour connexions mutuelles

### Phase 4 : Communication & Réseautage (📋 Planifiée)
**Objectif** : Permettre la communication entre professionnels connectés

- 📋 **Système de Messagerie** : Chat temps réel entre utilisateurs connectés
- 📋 **Gestion des Conversations** : Organisation et historique des discussions
- 📋 **Système de Notifications** : Notifications push pour matchs et messages

## 🛠️ Pour les Développeurs

### Démarrage Rapide

```bash
# 1. Cloner le projet
git clone https://github.com/decarvalhoe/meetinity.git
cd meetinity

# 2. Configurer l'environnement de développement
make setup

# 3. Démarrer tous les services
make dev-up

# 4. Vérifier la santé des services
curl http://localhost:5000/health

# 5. Arrêter l'environnement
make dev-down
```

### Architecture Technique

Le projet utilise une **architecture microservices** moderne :

- **API Gateway** : Routage des requêtes et authentification basé sur Flask
- **Service Utilisateur** : Authentification OAuth et gestion des profils
- **Service Événements** : Création, découverte et inscription aux événements
- **Service Matching** : Algorithmes de matching et fonctionnalité swipe
- **App Mobile** : React 18 avec TypeScript et Vite
- **Portail Admin** : Interface d'administration basée sur React
- **Base de Données** : PostgreSQL pour la persistance des données
- **Cache** : Redis pour l'optimisation des performances

### Structure des Repositories

| Repository | Description | État |
|---|---|---|
| **meetinity** | Repository principal avec contrats API et documentation | 15% - Spécifications définies |
| **meetinity-mobile-app** | Application mobile React pour utilisateurs finaux | 70% - Fonctionnelle avec OAuth |
| **meetinity-admin-portal** | Interface d'administration React | 60% - Gestion utilisateur complète |
| **meetinity-api-gateway** | API Gateway Flask pour routage des requêtes | 40% - Routage de base implémenté |
| **meetinity-user-service** | Gestion utilisateur et authentification Flask | 80% - OAuth et profils complets |
| **meetinity-matching-service** | Algorithmes de matching et logique swipe Flask | 25% - Algorithmes de base implémentés |
| **meetinity-event-service** | Système de gestion d'événements Flask | 35% - API REST avec validation |

## 🤝 Comment Contribuer ?

Nous accueillons toutes les contributions ! Que vous soyez :

- **Professionnel du Réseautage** : Partagez vos insights sur les meilleures pratiques
- **Développeur** : Améliorez la qualité du code et ajoutez de nouvelles fonctionnalités
- **Designer** : Améliorez l'expérience utilisateur et le design d'interface
- **Testeur** : Aidez à identifier et corriger les bugs sur la plateforme

### Étapes pour Contribuer

1. **Consultez** les [issues ouvertes](https://github.com/decarvalhoe/meetinity/issues) et la [feuille de route](TODO.md)
2. **Lisez** le guide de contribution dans `CONTRIBUTING.md`
3. **Créez** une branche de fonctionnalité pour votre contribution
4. **Soumettez** une pull request avec vos améliorations

## 📊 Évaluation 2025 & Feuille de Route

Une évaluation technique complète a été menée en septembre 2025, révélant des fondations solides avec des opportunités stratégiques de croissance.

- **Points Forts** : Authentification OAuth robuste, interfaces React modernes, architecture microservices propre
- **Issues Critiques** : Problèmes d'intégration base de données dans user-service, infrastructure CI/CD incomplète
- **Actions Prioritaires** : Résoudre les problèmes de base de données, finaliser les services événements et matching, implémenter les fonctionnalités de réseautage

Consultez l'évaluation détaillée et la feuille de route stratégique dans [`docs/project-evaluation.md`](docs/project-evaluation.md) et [`TODO.md`](TODO.md).

## 📞 Support et Communauté

- **GitHub Issues** : Signaler des bugs ou suggérer des fonctionnalités
- **Discussions** : Interagir avec la communauté
- **Documentation** : Guides complets dans le dossier `docs/`

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier `LICENSE` pour plus de détails.

---

> **Développé avec ❤️ par decarvalhoe et la communauté open-source**  
> **Progression Globale : 45%** | Dernière mise à jour : Septembre 2025

