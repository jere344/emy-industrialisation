# Réponses — Partie 1

## Tableau de décisions (partie 0)

| **Décision**                       | **Contrainte**                                                   | **Votre valeur**             |
| ---------------------------------- | ---------------------------------------------------------------- | ---------------------------- |
| Suffixe personnel                  | 4 à 6 caractères, minuscules et chiffres                         | `EG08`                       |
| Région Azure                       | une seule, la même partout                                       | `France Central`             |
| Nom du groupe de ressources        | préfixé<br>`rg-dermascan-registre-`                              | `rg-dermascan-registre-EG08` |
| Nom du registre ACR                | minuscules et chiffres, unique sur Azure                         | `dermascaneg08`              |
| Nom de l'image                     | ce que l'image contient, pas votre nom                           | `dermascan-health`           |
| Tag de version initial             | versionnage sémantique                                           | `0.1.0`                      |
| Image de base Python               | variante légère, version explicitement fixée, jamais<br>`latest` | `python:3.14-slim`           |
| Répertoire de travail dans l'image | chemin absolu, le même dans le<br>`Dockerfile`et le<br>`CMD`     | `/app`                       |
| Port d'écoute de l'application     | cohérent entre<br>`EXPOSE` , la variable<br>`PORT`et vos<br>`-p` | `8089`                       |
| uid de l'utilisateur d'exécution   | non nul, au-delà de 10000                                        | `10001`                      |

**Question 0.1** — Le nom du registre ACR doit être unique sur l'ensemble d'Azure, pas seulement dans votre abonnement. Quelle contrainte technique ce choix trahit-il sur la manière dont Azure expose les registres ? Répondez en une phrase dans `reponses_partie1.md` .

> Ce choix trahi une contrainte d'unicité d'enregistrement des registres, il existe quelque part un point de vision unique à tout les registres Azure.

## 1.1 — Les trois modèles de service

| **Modèle** | **Ce que le fournisseur gère à**<br>**votre place**             | **Ce qui reste à votre charge**                                                        | **Exemple de service**<br>**Azure**           |
| ---------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------- |
| **IaaS**   | Le matériel, le réseau physique,<br>la couche de virtualisation | Le système d'exploitation, les mises à jour,<br>le runtime, l'application, les données | Machine virtuelle (Azure<br>Virtual Machines) |
| **PaaS**   | `IaaS + Le système d'exploitation et runtime`                   | `L'application, les données`                                                           | `Microsoft Azure App Service`                 |
| **SaaS**   | `PaaS + L'application`                                          | `les données`                                                                          | `Suite Microsoft`                             |

## 1.2 — Où s'arrête votre responsabilité

| **Couche**                                       | **Dernier modèle où c'est à vous** |
| ------------------------------------------------ | ---------------------------------- |
| Correctifs de sécurité du système d'exploitation | `IaaS`                             |
| Version du runtime Python                        | `IaaS`                             |
| Code de l'application                            | `PaaS`                             |
| Dimensionnement du nombre d'instances            | `PaaS`                             |
| Vos données métier                               | `SaaS`                             |

**Question 1.1** — Un seul élément de ce tableau reste à votre charge dans les trois modèles. Lequel, et quelle conséquence cela a-t-il sur la conformité RGPD d'un projet d'IA ? Trois lignes maximum.

> Les données métier restent à la charge de l'utilisateur dans les trois modèles. Cela signifie que la conformité à la RGPD dans un projet d'AI est responsabilité de l'utilisateur, et non du fournisseur de service cloud.

## 1.3 — Les cinq caractéristiques NIST

| **Caractéristique NIST**      | **Traduction opérationnelle en une phrase**                                              |
| ----------------------------- | ---------------------------------------------------------------------------------------- |
| Libre-service à la demande    | Je crée une ressource sans ouvrir de ticket ni attendre l'accord d'un humain.            |
| Accès réseau large            | J'accède à mes ressources depuis n'importe quel appareil connecté à Internet.            |
| Mise en commun des ressources | Mes ressources sont partagées avec d'autres clients (mais je ne vois pas leurs données). |
| Élasticité rapide             | Mes ressources sont ajustées par rapport à mon utilisation automatiquement               |
| Service mesuré                | Je paie uniquement ce que j'utilise avec transparence                                    |

**Question 1.2** — Parmi ces cinq caractéristiques, laquelle explique directement que le nettoyage en fin de TP soit obligatoire ? Justifiez en deux lignes.

> La caractéristique "service mesuré" explique que le nettoyage en fin de TP soit obligatoire. Si les ressources ne sont pas détruites, elles continuent à être facturées (même avec une utilisation légère, facturation en temps).

## 1.4 — Exploration du portail Azure

**Mesure 1** — relevé d'exploration du portail Azure : abonnement, groupes de ressources, crédit restant et quotas.

1. Champs obligatoires à la création d'un Container Registry :

> - Subscription
> - Resource group
> - Registry name
> - location
> - Domain name label scope
> - Pricing plan
> - Role assignment permissions mode
>
> 7 champs obligatoires, certains pré remplis. Resource group et Registry name n'ont pas de valeurs par défaut.

2. Abonnement :

> Azure for Students
> identifiant : JRC4-ZSLT-BG7-PGB
> Status : Active

3. Groupes de ressources :

> Aucun

4. Crédit restant :

> usage : 0.00
> Il me reste $88

5. Quota :

> Quota : Standard DSv3 Family vCPUs
> Limite : 4

6. Onglet Étiquettes (Tags) :

> Les étiquettes sont une manière de catégoriser les ressources Azure pour nous permettre d'organiser notre facturation.

### Classement des services Azure

| **Service Azure**                                 | **Modèle** |
| ------------------------------------------------- | ---------- |
| Azure Virtual Machines                            | IaaS       |
| Azure App Service                                 | `PaaS`     |
| Azure Container Registry                          | `PaaS`     |
| Azure Machine Learning (espace de travail managé) | `PaaS`     |
| Microsoft 365                                     | `SaaS`     |

**Question 1.3** — Le groupe de ressources.

- Une ressource peut-elle appartenir à deux groupes de ressources simultanément ?

> Non, une ressource ne peut appartenir qu'à un seul groupe de ressources à la fois.

- Que se passe-t-il pour les ressources contenues lorsqu'on supprime un groupe de ressources ?

> Elles sont suppprimées.

- La région d'un groupe de ressources contraint-elle la région des ressources qu'il contient ? Si non, à quoi sert-elle ?

> Non, ce n'est pas une contrainte mais une indication pour savoir où se trouvent les ressources par défault.
