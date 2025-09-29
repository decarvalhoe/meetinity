# Plan d'Action Prioritaire Meetinity (MVP)

L'infrastructure, les pipelines CI/CD et la base Terraform sont livrés. La priorité passe désormais à l'expérience utilisateur : finaliser la couverture de l'API Gateway, sécuriser les inscriptions aux événements, synchroniser les données de matching et activer la messagerie. Les tâches ci-dessous sont triées par impact direct sur l'obtention d'un MVP fonctionnel.

## EPIC 1 – API Gateway prête pour le MVP

### Tâche 1.1 – Couverture des parcours clés
- **Description :** Étendre les routes de la passerelle pour exposer l'ensemble des flux `event-service`, `matching-service` et le futur service de messagerie, avec un routage basé sur les rôles et une gestion des erreurs homogène.
- **Livrables :** Nouvelles routes documentées, politiques d'autorisation consolidées, tests d'intégration couvrant les flux critiques.

### Tâche 1.2 – Observabilité et résilience
- **Description :** Ajouter traçabilité distribuée, métriques et budget d'erreurs sur l'API Gateway en s'appuyant sur les normes décrites dans [`docs/observability.md`](docs/observability.md) et [`docs/autoscaling-playbook.md`](docs/autoscaling-playbook.md).
- **Livrables :** Tableaux de bord et alertes configurés, tests de charge validant la tolérance aux pannes, mise à jour de la documentation opérateur.

## EPIC 2 – Inscriptions aux événements fiables

### Tâche 2.1 – Persistance et quotas
- **Description :** Connecter le `event-service` à PostgreSQL, modéliser les inscriptions et gérer les quotas/attentes conformément aux contrats OpenAPI.
- **Livrables :** Migrations Alembic, endpoints `/events/{id}/register` et `/events/{id}/attendees`, tests d'intégration.

### Tâche 2.2 – Notifications et synchronisation
- **Description :** Publier des événements métier (Kafka ou Redis Streams) lors des inscriptions et exposer des webhooks pour informer le portail admin.
- **Livrables :** Producteurs d'événements, documentation d'abonnement, scripts d'exemple pour la consommation.

## EPIC 3 – Matching connecté aux données réelles

### Tâche 3.1 – Pipeline de données profils & disponibilités
- **Description :** Synchroniser les profils et préférences depuis le `user-service`, ainsi que les disponibilités d'événements depuis le `event-service`, via des jobs planifiés ou des événements.
- **Livrables :** Jobs d'ingestion, stockage normalisé, tests garantissant la cohérence des données.

### Tâche 3.2 – Algorithmes prêts pour la production
- **Description :** Remplacer les données factices par le pipeline réel, recalibrer les scores de matching et exposer des endpoints paginés pour le mobile et l'admin.
- **Livrables :** Nouvelles métriques de pertinence, documentation de tuning, tests de performance.

## EPIC 4 – Messagerie MVP

### Tâche 4.1 – Service de conversations
- **Description :** Définir l'architecture (WebSocket + Redis Streams ou équivalent), créer le service de messagerie et ses contrats (REST + WebSocket) avec authentification via la Gateway.
- **Livrables :** Service conteneurisé dans `services/messaging-service`, schéma de données, tests d'acceptation.

### Tâche 4.2 – Intégrations clients
- **Description :** Brancher l'application mobile et le portail admin sur les nouveaux endpoints de messagerie avec notifications en temps réel.
- **Livrables :** Guides d'intégration, stories UI, scénarios de tests bout-en-bout couvrant un échange de messages.

---

Les tâches hors périmètre MVP (améliorations UI secondaires, optimisations financières cloud, refontes d'infrastructure déjà livrées) sont volontairement écartées afin de concentrer l'équipe sur l'ouverture du produit aux premiers utilisateurs.
