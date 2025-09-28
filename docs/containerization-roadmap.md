# Plan d'action : Containerisation et Orchestration

Cette feuille de route détaille les actions nécessaires pour livrer la première vague d'infrastructure container/Kubernetes pour Meetinity. Chaque section comprend les prérequis, les sorties attendues et les responsables pressentis.

## 1. Inventorier tous les services et définir leurs Dockerfiles
- **Objectifs** :
  - Dresser la liste exhaustive des applications (front, back, jobs, workers, services tiers).
  - Identifier les dépendances (langages, runtimes, bases de données, brokers, binaires).
- **Actions** :
  1. Lancer un audit des dépôts Meetinity et centraliser les services dans un tableau partagé (Notion/Sheet).
  2. Pour chaque service :
     - Documenter la commande de build, la commande de démarrage et les variables d'environnement.
     - Lister les exigences système (paquets, certificats, ports, stockage persistant).
  3. Créer ou mettre à jour le Dockerfile correspondant en appliquant les bonnes pratiques (multistage build, user non-root, cache).
- **Livrables** :
  - Tableau d'inventaire à jour.
  - Dockerfiles revus avec validation locale via `docker build` et `docker compose`.

## 2. Créer un registre d'images avec stratégie de tagging et retention
- **Objectifs** :
  - Disposer d'un registre central (GHCR, ECR, GCR) sécurisé.
  - Garantir une politique de tagging cohérente et une purge automatique.
- **Actions** :
  1. Valider la plateforme cible (préférence GHCR si GitHub Actions).
  2. Configurer les permissions d'accès (OIDC GitHub Actions, accès lecture pour runtime, écriture pour CI).
  3. Définir le schéma de tags : `app:branch-SHORT_SHA`, `app:env-release`, `app:version`.
  4. Mettre en place la rétention (ex : 30 derniers builds par branche, suppression images orphelines).
  5. Documenter la procédure de publication et de purge.
- **Livrables** :
  - Registre opérationnel + secrets CI/CD configurés.
  - Politique de tagging et rétention décrite dans la documentation d'infra (`docs/container-registry.md`).

## 3. Déployer un cluster Kubernetes avec configuration réseau et stockage
- **Objectifs** :
  - Obtenir un cluster prêt pour les environnements staging/prod.
  - Assurer la haute disponibilité réseau et le provisionnement du stockage.
- **Actions** :
  1. Choisir le provider (AKS/EKS/GKE/K3s managé) et la région.
  2. Automatiser le provisioning avec Terraform (`infra/terraform/kubernetes`).
  3. Configurer le réseau : CNI, ingress controller (NGINX ou Traefik), certificats TLS.
  4. Configurer le stockage : classes StorageClass (gp2/gp3/ssd), provisioner CSI, snapshots.
  5. Valider l'accès kubectl via RBAC et groupes IAM.
- **Livrables** :
  - Cluster fonctionnel avec accès restreint.
  - Documentation d'onboarding (`docs/dev-environment.md`).

## 4. Écrire/Maintenir des Helm charts pour chaque service
- **Objectifs** :
  - Standardiser les déploiements applicatifs.
  - Séparer les valeurs par environnement (dev, staging, prod).
- **Actions** :
  1. Initialiser un chart parent (common templates, configmap, secrets, probes).
  2. Créer un chart par service dans `infra/helm` avec templates pour Deployment, Service, HPA, Ingress.
  3. Définir un dossier `values/` par environnement et intégrer les secrets via Vault/SealedSecrets.
  4. Ajouter des tests Helm (`helm lint`, `helm template`) dans la CI.
- **Livrables** :
  - Charts versionnés avec README.
  - Pipelines CI validant les templates.

## 5. Mettre en place l'autoscaling (HPA/VPA) et définir les requests/limits
- **Objectifs** :
  - Garantir la résilience et l'utilisation optimale des ressources.
- **Actions** :
  1. Collecter les métriques applicatives (Prometheus adapter).
  2. Définir les ressources de base par service (CPU, RAM) via profil de charge.
  3. Configurer Horizontal Pod Autoscaler (HPA) sur métriques CPU/RAM ou custom.
  4. Évaluer Vertical Pod Autoscaler (VPA) en mode recommandation pour production.
  5. Documenter les budgets de PodDisruptionBudget.
- **Livrables** :
  - Manifeste HPA/VPA commités.
  - Table de sizing initiale et procédure de révision.

## 6. Gérer la promotion multi-environnements via namespaces et secrets dédiés
- **Objectifs** :
  - Séparer les environnements et tracer les déploiements.
- **Actions** :
  1. Créer des namespaces par environnement (`dev`, `staging`, `prod`).
  2. Définir la nomenclature des releases Helm (`service-env`).
  3. Provisionner les secrets avec des outils adaptés (SealedSecrets, External Secrets).
  4. Configurer les règles réseau (NetworkPolicies) et quotas par namespace.
  5. Mettre en place la promotion automatisée via pipelines (tag + déploiement progressif).
- **Livrables** :
  - Namespaces et policies appliqués.
  - [Guide de promotion documenté](promotion-guide.md).

---

## Calendrier indicatif
| Sprint | Livrable principal | Notes |
|--------|--------------------|-------|
| S1     | Inventaire des services + Dockerfiles prioritaires | Implique toutes les squads applicatives |
| S2     | Registre d'images + pipeline de build initial | Dépend de S1 |
| S3     | Cluster Kubernetes prêt + chart commun | Collaboration avec l'équipe plateforme |
| S4     | Charts par service + déploiements dev/staging | Tests intégrés dans la CI |
| S5     | Autoscaling + promotion multi-env | Ajustements basés sur les métriques |

## Gouvernance
- **Owner** : Équipe Platform/DevOps.
- **Stakeholders** : Leads applicatifs, sécurité, QA.
- **Revues** : Stand-up hebdo, revue de sprint, comité d'architecture mensuel.

