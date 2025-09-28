# Meetinity Development Environment

Ce guide décrit la manière de configurer un environnement de développement local pour l'écosystème Meetinity. Il s'appuie sur
`docker-compose` afin d'orchestrer les microservices et les dépendances techniques décrites dans la spécification fonctionnelle.

## Prérequis

Avant de démarrer, assurez-vous de disposer des éléments suivants :

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ou Docker Engine >= 24.
- Le plugin **Docker Compose** (inclus avec Docker Desktop et disponible pour Docker Engine).
- `make` pour utiliser les cibles fournies à la racine du dépôt.
- Accès aux autres dépôts Meetinity (API Gateway et microservices) si vous souhaitez construire les images localement.

## Arborescence recommandée

Le fichier `docker-compose.dev.yml` fait l'hypothèse que tous les dépôts se trouvent au même niveau. Exemple :

```
~/workspace/
├── meetinity
├── meetinity-api-gateway
├── meetinity-user-service
├── meetinity-matching-service
├── meetinity-event-service
```

Adaptez les chemins de build dans `docker-compose.dev.yml` si votre organisation diffère.

## Variables d'environnement

Les services utilisent un fichier `.env.dev` à placer à la racine de ce dépôt. Voici un exemple de configuration :

```
# Base de données partagée
POSTGRES_USER=meetinity
POSTGRES_PASSWORD=meetinity
POSTGRES_DB=meetinity
POSTGRES_PORT=5432

# Kafka
KAFKA_PORT=9092
KAFKA_BROKER=kafka:9092
KAFKA_ZOOKEEPER=zookeeper:2181
KAFKA_UI_PORT=8085

# Services
API_GATEWAY_PORT=8080
USER_SERVICE_PORT=8081
MATCHING_SERVICE_PORT=8082
EVENT_SERVICE_PORT=8083
```

Les microservices peuvent nécessiter des variables supplémentaires (clés OAuth, secrets JWT, etc.). Référez-vous aux README
propres à chaque dépôt et ajoutez les variables correspondantes au même fichier `.env.dev`.

## Lancer l'environnement de développement

Les commandes suivantes sont disponibles via le Makefile :

```bash
make dev-up    # démarre les services en arrière-plan et reconstruit si besoin
make dev-down  # arrête et supprime les conteneurs
make dev-logs  # suit les journaux agrégés
```

Derrière ces commandes, `docker compose` est invoqué avec le fichier `docker-compose.dev.yml` fourni à la racine du dépôt.

Vous pouvez également lancer les services manuellement :

```bash
docker compose --env-file .env.dev -f docker-compose.dev.yml up -d
docker compose --env-file .env.dev -f docker-compose.dev.yml down --remove-orphans
```

## Services disponibles

| Service                  | Port local | Description                                                 |
|--------------------------|------------|-------------------------------------------------------------|
| API Gateway              | 8080       | Point d'entrée des clients (mobile, admin)                  |
| User Service             | 8081       | Gestion des comptes, profils, authentification              |
| Matching Service         | 8082       | Algorithmes de matching et recommandations                  |
| Event Service            | 8083       | Gestion des événements et inscriptions                      |
| PostgreSQL               | 5432       | Base de données relationnelle partagée                      |
| Kafka                    | 9092       | Bus de messages pour la communication asynchrone            |
| Kafka UI (optionnel)     | 8085       | Interface web pour visualiser les topics Kafka              |

## Dépannage

- **Port déjà utilisé** : modifiez le port dans `.env.dev` ou adaptez `docker-compose.dev.yml`.
- **Images introuvables** : assurez-vous que les dossiers des microservices sont présents et construits (`docker compose build`).
- **Variables manquantes** : vérifiez votre fichier `.env.dev` et complétez les secrets requis.

Pour toute contribution ou amélioration, ouvrez une Pull Request sur ce dépôt après avoir mis à jour la documentation si
nécessaire.
