# FAISABILITE — Séance 3

**Question 0.1** — Le nom de l'application web est unique sur tout Azure, exactement comme l'était le nom du registre ACR en séance 1. Cette fois, une conséquence supplémentaire apparaît, que le registre n'avait pas : laquelle, du point de vue d'un attaquant qui cherche des services mal protégés ? Deux lignes dans `FAISABILITE.md`.

> Le nom de l'application web étant unique et public il est facile pour un attaquant d'itérer pour trouver toutes les applications et d'essayer automatiquement des listes de failles de sécurité visant des serveurs non mis à jour. Cela simplifie aussi des attaques par déni de service ou une utilisation abusive de l'application entrainant des frais pour son créateur.

## Tableau de décisions

| Décision                     | Votre valeur           |
| ---------------------------- | ---------------------- |
| Suffixe personnel            | `EG08`                 |
| Région Azure                 | `francecentral`        |
| Nom du groupe de ressources  | `rg-dermascan-s3-EG08` |
| Nom du registre ACR existant | `dermascaneg08`        |
| Dépôt et tag de l'image S2   | `dermascan-api:1.0.1`  |
| Nom du plan de service       | `plan-dermascan-EG08`  |
| Nom de l'application web     | `dermascan-eg08`       |

## Mesure 1 — sondes de faisabilité de l'abonnement

| Sonde                               | Commande source             | Votre relevé                                                                                                   |
| ----------------------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Régions autorisées par la politique | `az policy assignment list` | `francecentral`, `spaincentral`, `italynorth`, `polandcentral`, `belgiumcentral`                               |
| `Microsoft.Web`                     | `az provider show`          | `NotRegistered`, puis `Registered` après `az provider register --namespace Microsoft.Web --wait`               |
| `Microsoft.ContainerInstance`       | `az provider show`          | `NotRegistered`, puis `Registered` après `az provider register --namespace Microsoft.ContainerInstance --wait` |
| `Microsoft.ContainerRegistry`       | `az provider show`          | `Registered`                                                                                                   |

| Création du plan App Service Linux  | `az appservice plan create` | succès (SKU `B1`, état `Ready`)             |
| ----------------------------------- | --------------------------- | ------------------------------------------- |
| Code d'erreur exact, le cas échéant | sortie de la commande       | aucune erreur                               |
| Durée totale de la sonde            | chronomètre                 | 12:12:53 → 12:19:40, soit environ 7 minutes |

## Mesure 2 — cible retenue

| Élément de la décision                                         | Votre réponse                                                                                 |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Cible retenue                                                  | A — App Service for Containers                                                                |
| Fait déclencheur, cité avec le message d'erreur s'il y en a un | Le plan Linux B1 a été créé sans erreur et affiche l'état `Ready` (`az appservice plan show`) |
| Heure de la décision                                           | 12:19                                                                                         |
| Ce que cette cible ne permettra pas de montrer aujourd'hui     | rien ? |

## Question 1.1

**Question 1.1** — Les trois cibles diffèrent par le niveau d'abstraction. Pour chacune, indiquez ce que vous n'avez **pas** à gérer, en reprenant la grille IaaS / PaaS / SaaS de la séance 1.

| Cible | Modèle de service | Ce que vous ne gérez pas | Ce qui reste à votre charge |
|---|---|---|---|
| App Service for Containers | PaaS | Le matériel, le réseau physique, la virtualisation, le système d'exploitation et le runtime (hôte et moteur de conteneurs), le point d'entrée HTTPS public, le redémarrage du conteneur | L'application (l'image : code, dépendances, modèle), sa configuration (variables, port, sonde), les données |
| Azure Container Instances | PaaS | Le matériel, le réseau physique, la virtualisation, le système d'exploitation et le moteur de conteneurs | L'application (l'image), sa configuration, les données, et ce qu'App Service fournit en plus : pas de frontal HTTPS intégré, supervision et redémarrage à configurer |
| Docker sur votre poste | Aucun (hors cloud : ni IaaS, ni PaaS, ni SaaS) | Rien | Tout : la machine, son système d'exploitation, Docker, l'application, la configuration, les données, la disponibilité |

## Question 1.2

**Question 1.2** — Relevez dans la documentation tarifaire Azure le coût mensuel annoncé du SKU que vous venez de choisir, dans votre région. Rapportez-le au crédit restant de votre compte, relevé dans `Cost Management`. Combien de jours de fonctionnement continu votre crédit finance-t-il ? Ce chiffre justifie à lui seul le nettoyage de fin de séance.

| Élément | Valeur |
|---|---|
| SKU, région | B1 Linux, France Central |
| Prix horaire annoncé | 0,018 USD / heure |
| Coût mensuel (730 h) | environ 13,14 USD |
| Coût journalier (24 h) | 0,018 × 24 = 0,432 USD |
| Crédit restant | 86 € sur 88 € (Azure Education), expire le 06/10/2027 |
| Jours financés | 86 / 0,432 ≈ **199 jours** de fonctionnement continu du plan B1 seul (1 USD compté pour 1 €, hypothèse prudente) |

Le coût du registre ACR de S1 (2,88 € depuis le 5 octobre, soit environ 0,14 €/jour) vient en plus : plan B1 et registre ensemble, le crédit finance environ 86 / 0,57 ≈ 151 jours.
