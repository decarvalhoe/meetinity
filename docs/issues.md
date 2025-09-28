# Suivi des Issues Git

Ce document récapitule l'état des issues identifiées dans le dépôt GitHub `meetinity/meetinity` au moment de cette mise à jour.

| Issue | Titre | Statut | Notes |
|-------|-------|--------|-------|
| #13 | Étendre l'API Événements avec un endpoint de détail et de gestion | ✅ Fermée | Les endpoints `GET /events/{id}`, `PATCH /events/{id}` et `DELETE /events/{id}/join` documentent désormais l'accès détaillé et la gestion des inscriptions. |
| #14 | Permettre la mise à jour du profil utilisateur | ✅ Fermée | Nouveau endpoint `PATCH /profiles/me` avec le schéma `ProfileUpdateInput`. |
| #15 | Activer la création de conversations et les accusés de lecture | ✅ Fermée | Ajout des endpoints `POST /conversations`, `POST /conversations/{id}/read` ainsi que du schéma `ConversationCreateInput`. |

Toutes les issues connues sont maintenant complétées. Les évolutions futures pourront être ajoutées à ce fichier pour centraliser l'état du backlog.
