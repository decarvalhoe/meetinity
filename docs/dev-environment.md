# Meetinity Development Environment

Ce guide décrit la manière de configurer un environnement de développement local pour l'écosystème Meetinity. Il s'appuie sur
`docker-compose` afin d'orchestrer les microservices et les dépendances techniques décrites dans la spécification fonctionnelle.

## Prérequis

Avant de démarrer, assurez-vous de disposer des éléments suivants :

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ou Docker Engine >= 24.
- Le plugin **Docker Compose** (inclus avec Docker Desktop et disponible pour Docker Engine).
- `make` pour utiliser les cibles fournies à la racine du dépôt.
- Aucun dépôt supplémentaire n'est requis : toutes les images se construisent à partir des dossiers `services/*` versionnés ici.

## Arborescence recommandée

Le fichier `docker-compose.dev.yml` construit directement les microservices depuis ce dépôt. Assurez-vous que la structure suivante est conservée :

```
~/workspace/meetinity
├── services/
│   ├── api-gateway/
│   ├── event-service/
│   ├── matching-service/
│   ├── messaging-service/
│   └── user-service/
├── infra/
├── scripts/
└── docker-compose.dev.yml
```

Si vous déplacez un service, mettez à jour la directive `context` correspondante dans `docker-compose.dev.yml`.

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
MESSAGING_SERVICE_PORT=8084
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
| Messaging Service        | 8084       | Backend REST/WebSocket pour la messagerie                   |
| PostgreSQL               | 5432       | Base de données relationnelle partagée                      |
| Kafka                    | 9092       | Bus de messages pour la communication asynchrone            |
| Kafka UI (optionnel)     | 8085       | Interface web pour visualiser les topics Kafka              |

## Données de démonstration

Les microservices reposent sur des migrations Alembic. Une fois l'environnement démarré, lancez le job `seed-data` pour injecter un jeu de données cohérent (utilisateurs, événements, inscriptions et conversations de démonstration) dans PostgreSQL :

```bash
make dev-seed
# ou directement
./scripts/dev/seed.sh
```

Le script applique d'abord les migrations nécessaires (`services/user-service`, `services/event-service`, `services/messaging-service`) via `docker compose exec` puis déclenche le service Compose `seed-data` (profil `seed`). Celui-ci monte `scripts/dev/sql/seed.sql` dans un conteneur `postgres:15` éphémère qui exécute les `INSERT` idempotents. Vous pouvez relancer la commande autant de fois que nécessaire pour rafraîchir les données de test.

## Mocks et dépendances externes

`docker-compose.dev.yml` embarque un service [WireMock](https://wiremock.org/) exposé sur `http://localhost:${WIREMOCK_PORT:-8089}`. Les stubs sont versionnés dans `infra/mocks/wiremock` :

- `mappings/` pour les routes (`health.json` propose un exemple de réponse JSON) ;
- `__files/` (créez le dossier au besoin) pour les payloads plus volumineux.

Modifiez/ajoutez vos mappings puis relancez le conteneur WireMock (`docker compose restart wiremock`) pour simuler vos dépendances SaaS sans accès externe.

## Hot reload et debug

Les services Flask (`api-gateway`, `user-service`, `matching-service`, `event-service`, `messaging-service`) démarrent désormais avec `flask run --debug` dans Docker. Les volumes `./services/*:/app` sont montés en écriture : chaque sauvegarde locale redémarre automatiquement l'application grâce au reloader intégré.

Commandes pratiques :

```bash
# démarrer seulement les services applicatifs avec hot reload
docker compose --env-file .env.dev -f docker-compose.dev.yml up api-gateway user-service matching-service event-service messaging-service

# attacher un shell interactif pour debugger
docker compose exec user-service flask shell
```

Pour désactiver le reloader (ex. debug pas à pas), exportez `FLASK_DEBUG=0` dans `.env.dev` ou sur un `docker compose run`. Pensez aussi à activer le port de debuggage de votre IDE (ex. `debugpy`) en ajoutant le paquet à `requirements.txt` puis en démarrant l'agent depuis le conteneur.

## Dépannage

- **Port déjà utilisé** : modifiez le port dans `.env.dev` ou adaptez `docker-compose.dev.yml`.
- **Images introuvables** : assurez-vous que les dossiers des microservices sont présents et construits (`docker compose build`).
- **Variables manquantes** : vérifiez votre fichier `.env.dev` et complétez les secrets requis.

Pour toute contribution ou amélioration, ouvrez une Pull Request sur ce dépôt après avoir mis à jour la documentation si
nécessaire.

## Accès au cluster Kubernetes managé

L'infrastructure cloud provisionne un cluster Amazon EKS dans la région `eu-west-1`. Après l'exécution de Terraform :

1. Assurez-vous d'avoir une session AWS valide avec les droits de base (via SSO ou `aws configure`).
2. Prenez le rôle IAM d'administration du cluster (par défaut `meetinity-eks-admin`) :

   ```bash
   aws sts assume-role --role-arn $(terraform output -raw cluster_admin_role_arn) --role-session-name admin-session
   ```

   Exportez ensuite les identifiants temporaires renvoyés (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`).
3. Générez le contexte kubeconfig :

   ```bash
   aws eks update-kubeconfig \
     --region eu-west-1 \
     --name $(terraform output -raw cluster_name)
   ```

4. Vérifiez l'accès :

   ```bash
   kubectl get nodes
   ```

### Onboarding RBAC pour un·e nouvel·le équipier·ère

Les accès Kubernetes sont fédérés via IAM. Pour ajouter une personne :

1. Créez (ou identifiez) un utilisateur ou un rôle IAM pouvant être assumé par la personne.
2. Ajoutez l'ARN correspondant à la variable Terraform `cluster_admin_principal_arns` (ou créez un nouvel `aws_eks_access_entry` si un rôle avec des droits plus limités est requis).
3. Appliquez la configuration Terraform :

   ```bash
   terraform apply -var-file=env.tfvars
   ```

4. Communiquez à la personne le rôle à assumer puis le workflow `aws eks update-kubeconfig` ci-dessus.

Le contrôleur d'ingress NGINX et cert-manager sont installés automatiquement ; les certificats TLS par défaut sont auto-signés.
Pour utiliser un certificat public, déployez un nouvel `Issuer/ClusterIssuer` cert-manager et associez-le à vos Ingress.
