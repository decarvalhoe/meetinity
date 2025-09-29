# Base de données et cache

Cette documentation explique comment l'infrastructure PostgreSQL et Redis déployée avec Terraform est exploitée, comment automatiser les migrations applicatives et quels réflexes adopter pour la sauvegarde, la restauration et la supervision des performances.

## Aperçu de l'infrastructure

- **PostgreSQL** : un cluster Amazon Aurora PostgreSQL haute disponibilité est créé via le module Terraform `infra/terraform/modules/rds`. Il expose un endpoint principal (lecture/écriture) et un endpoint secondaire (lecture seule). Les identifiants générés sont synchronisés dans le Secret Kubernetes `platform-database` par `infra/scripts/deploy.sh`.
- **Redis** : un groupe de réplication Amazon ElastiCache Redis multi-AZ est géré par le module `infra/terraform/modules/elasticache`. Le Secret `platform-redis` contient l'URL chiffrée (`rediss://`) ainsi que le token d'authentification généré.
- **Consommation applicative** : le script de déploiement transmet les noms des secrets à Helm (`global.database.secretName` et `global.redis.secretName`). Les charts consomment ensuite ces secrets pour injecter `DATABASE_URL` et `REDIS_URL` dans les déploiements applicatifs.

## Procédures de migration

### 1. Job Helm dédié

1. Créer un fichier de valeurs temporaire qui pointe vers l'image de migration :

   ```bash
   cat > /tmp/migrate.yaml <<'YAML'
   jobs:
     database-migrate:
       image: ghcr.io/meetinity/user-service:migrations
       command: ["alembic", "upgrade", "head"]
       envFromSecret: platform-database
   YAML
   ```

2. Lancer le job via Helm :

   ```bash
   helm upgrade --install meetinity-${ENV} infra/helm/meetinity \
     --namespace meetinity-${ENV} \
     --values infra/helm/meetinity/values.yaml \
     --values infra/helm/meetinity/values/${ENV}.yaml \
     --values /tmp/migrate.yaml \
     --set-string global.database.secretName=platform-database \
     --set-string global.redis.secretName=platform-redis \
     --set-string global.environment=${ENV}
   ```

   Le job est exécuté une fois puis supprimé lors du prochain déploiement.

### 2. `kubectl run`

Pour des migrations ponctuelles ou exploratoires :

```bash
kubectl run db-migrate --rm -i --tty \
  --namespace meetinity-${ENV} \
  --image ghcr.io/meetinity/user-service:migrations \
  --env-from=secretRef:platform-database \
  --command -- alembic upgrade head
```

Cette approche permet d'exécuter un conteneur éphémère en réutilisant les secrets déjà provisionnés.

### 3. Automatisation CI/CD

- Intégrer `infra/scripts/deploy.sh` dans le pipeline afin que les migrations s'exécutent automatiquement après `terraform apply` via l'un des mécanismes ci-dessus.
- Protéger l'ordre des étapes : *apply Terraform → mettre à jour kubeconfig → lancer les migrations → déployer les services*.

## Sauvegardes et restauration

### Sauvegardes automatiques

- **PostgreSQL** : la rétention des snapshots est configurée via la variable `database_config.backup_retention_period` (7 jours par défaut). Les exports ponctuels peuvent être lancés avec `aws rds create-db-cluster-snapshot --db-cluster-identifier <cluster> --db-cluster-snapshot-identifier <snapshot>`.
- **Redis** : les sauvegardes quotidiennes sont contrôlées par `redis_config.snapshot_retention_limit`. Pour déclencher une sauvegarde manuelle : `aws elasticache create-snapshot --replication-group-id <groupe> --snapshot-name <nom>`.

### Restaurer PostgreSQL

1. Créer un nouveau snapshot ou en sélectionner un existant.
2. Restaurer dans un nouveau cluster :

   ```bash
   aws rds restore-db-cluster-from-snapshot \
     --db-cluster-identifier meetinity-${ENV}-restore \
     --snapshot-identifier <snapshot-id>
   ```
3. Mettre à jour les sorties Terraform ou les variables du pipeline pour pointer vers le nouveau cluster si la restauration devient permanente.
4. Redéployer avec `infra/scripts/deploy.sh` pour mettre à jour les secrets.

### Restaurer Redis

1. Créer un groupe de réplication depuis un snapshot :

   ```bash
   aws elasticache restore-replication-group-from-snapshot \
     --replication-group-id meetinity-${ENV}-redis-restore \
     --snapshot-name <snapshot-name>
   ```
2. Une fois l'instance opérationnelle, mettre à jour les valeurs Terraform (ou un fichier `tfvars`) pour reprendre le contrôle via IaC, puis relancer le déploiement afin de propager les nouveaux endpoints.

## Monitoring et observabilité

- **CloudWatch / Performance Insights** : activer Performance Insights (`database_config.performance_insights_enabled`) permet de suivre la consommation CPU, les requêtes lentes ou la pression I/O du cluster Aurora.
- **Alertes** : configurer des alarmes CloudWatch sur la latence, le débit de connexion et la mémoire libre (Redis) via `aws cloudwatch put-metric-alarm` ou IaC complémentaire.
- **Prometheus/Grafana** : la stack de monitoring déployée dans `infra/monitoring` peut être enrichie avec :
  - l'exporter `prometheus-community/prometheus-postgres-exporter` pour Aurora,
  - `oliver006/redis_exporter` pour ElastiCache (mode TLS),
  puis des dashboards Grafana dédiés (temps de requêtes, locks, fragmentation Redis).
- **Tests de charge** : avant chaque montée de version, utiliser `kubectl port-forward` pour cibler un lecteur secondaire et exécuter des benchmarks (`pgbench`, `redis-benchmark`).

## Bonnes pratiques

- Toujours exécuter les migrations avant de déployer une version qui introduit des changements de schéma.
- Documenter dans le dépôt applicatif les commandes Alembic/Liquibase utilisées pour éviter la dérive.
- Nettoyer régulièrement les secrets temporaires et limiter les accès aux secrets (`kubectl get secret platform-database -n meetinity-${ENV}` doit être restreint aux équipes data/ops).
- Vérifier l'expiration des snapshots lors des changements de rétention pour éviter la perte de points de restauration.
