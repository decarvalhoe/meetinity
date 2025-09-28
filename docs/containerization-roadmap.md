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

## 2. Modules Terraform industrialisés
- **Résumé** : Les modules publiés dans [`infra/terraform/modules`](../infra/terraform/modules) couvrent le provisionnement du cluster Kubernetes, des namespaces, de l'ingress et des dépendances réseau. Le `main.tf` et les environnements d'exemple ([`infra/terraform/kubernetes`](../infra/terraform/kubernetes)) documentent comment composer ces briques avec les variables partagées.
- **Références** :
  - Documentation d'usage : [`infra/terraform/README.md`](../infra/terraform/README.md)
  - Pipelines d'initialisation : [`infra/terraform/main.tf`](../infra/terraform/main.tf)

> **État :** Livré. Suivi restant : compléter l'inventaire des services (Section 1) pour ajouter les modules manquants identifiés lors de l'audit Dockerfiles.

## 3. Chart Helm umbrella
- **Résumé** : L'umbrella chart [`infra/helm/meetinity`](../infra/helm/meetinity) assemble les composants mutualisés (ingress, certificats, observabilité) et expose les valeurs communes pour les services applicatifs. Les sous-charts spécifiques résident dans [`infra/helm/meetinity/charts`](../infra/helm/meetinity/charts) avec des valeurs surchargées par environnement (`values/`).
- **Références** :
  - Guide de packaging : [`infra/helm/README.md`](../infra/helm/README.md)
  - Modèle de valeurs : [`infra/helm/meetinity/values.yaml`](../infra/helm/meetinity/values.yaml)

> **État :** Livré. Suivi restant : finaliser l'inventaire des services pour embarquer les derniers charts applicatifs manquants.

## 4. Chaîne CD GitHub Actions → Kubernetes
- **Résumé** : Le workflow [`.github/workflows/cd.yml`](../.github/workflows/cd.yml) orchestre la construction des images, la publication dans GHCR et le déploiement Helm vers les environnements `staging` et `prod`. Les jobs valident les manifests (`helm lint`, `kubectl diff`) avant promotion et déclenchent des notifications en cas d'échec.
- **Références** :
  - Documentation GHCR : [`docs/container-registry.md`](container-registry.md)
  - README des workflows : [`.github/workflows/README.md`](../.github/workflows/README.md)

> **État :** Livré. Suivi restant : inclure les nouveaux services de l'inventaire dans les matrices de déploiement.

## 5. Playbook d'autoscaling
- **Résumé** : Le document [`docs/autoscaling-playbook.md`](autoscaling-playbook.md) consolide les paramètres CPU/mémoire recommandés, l'utilisation des HPAs par service et la procédure de revue trimestrielle. Il référence également la configuration Prometheus Adapter gérée dans [`infra/monitoring/prometheus-adapter`](../infra/monitoring/prometheus-adapter) et les alertes associées.
- **Références** :
  - Paramètres Grafana : [`infra/monitoring/grafana/values.yaml`](../infra/monitoring/grafana/values.yaml)
  - Configuration Prometheus : [`infra/monitoring/prometheus/values.yaml`](../infra/monitoring/prometheus/values.yaml)

> **État :** Livré. Suivi restant : intégrer les métriques des services récemment inventoriés pour compléter les courbes de référence.

## 6. Guide de promotion multi-environnements
- **Résumé** : Le guide opérationnel [`docs/promotion-guide.md`](promotion-guide.md) détaille la gouvernance des namespaces, la gestion des secrets et les garde-fous pour les déploiements progressifs. Il décrit également la procédure de rollback et la validation qualité avant passage en production.
- **Références** :
  - Politique de sécurité : [`infra/security/README.md`](../infra/security/README.md)
  - Script de déploiement : [`infra/scripts/deploy.sh`](../infra/scripts/deploy.sh)

> **État :** Livré. Suivi restant : attendre l'issue de l'audit Dockerfiles/Inventaire pour intégrer les derniers flux de promotion.

---

## Calendrier indicatif
| Sprint | Livrable principal | Notes |
|--------|--------------------|-------|
| S1     | Inventaire des services + Dockerfiles prioritaires | ⏳ Reste à finaliser : consolidation de l'audit et revue des Dockerfiles |
| S2     | Registre d'images + pipeline de build initial | ✅ Livré – dépendait de S1 mais la dette est isolée à l'inventaire |
| S3     | Cluster Kubernetes prêt + chart commun | ✅ Livré et aligné avec les modules Terraform |
| S4     | Charts par service + déploiements dev/staging | ✅ Livré via l'umbrella chart et la chaîne CD |
| S5     | Autoscaling + promotion multi-env | ✅ Livré – reste uniquement les ajustements liés aux nouveaux services |

## Gouvernance
- **Owner** : Équipe Platform/DevOps.
- **Stakeholders** : Leads applicatifs, sécurité, QA.
- **Revues** : Stand-up hebdo, revue de sprint, comité d'architecture mensuel.

