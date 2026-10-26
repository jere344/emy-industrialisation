# Mesures — Parties 2 à 6

Séance 1 · Cloud Azure & conteneurisation · suffixe `EG08` · région `France Central`

## Partie 2 — Mise en place de l'environnement

### Mesure 2 — identité du compte Azure

`az version` : `2.91.0`

`az account list --output table` :

```
Name                CloudName    SubscriptionId                        TenantId                              State    IsDefault
------------------  -----------  ------------------------------------  ------------------------------------  -------  -----------
Azure for Students  AzureCloud   b1e8aa25-d0ef-4e4c-a766-e02d270e49b6  38e72bba-3c22-4382-9323-ac1612931297  Enabled  True
```

`az account show --output table` :

```
EnvironmentName    HomeTenantId                          IsDefault    Name                State    TenantDefaultDomain    TenantDisplayName    TenantId
-----------------  ------------------------------------  -----------  ------------------  -------  ---------------------  -------------------  ------------------------------------
AzureCloud         38e72bba-3c22-4382-9323-ac1612931297  True         Azure for Students  Enabled  ynov.com               Ynov                 38e72bba-3c22-4382-9323-ac1612931297
```

> Tenant est Ynov
> identifiant du tenant est 38e72bba-3c22-4382-9323-ac1612931297
> identifiant de l'abonnement est b1e8aa25-d0ef-4e4c-a766-e02d270e49b6

### Question 2.1 — régions et critères de choix

> 109 régions
> En entreprise :
> - critère géographique pour la reglementation et les engagements de l'entreprise quand à la souveraineté des données
> - critère de performance et de latence entre les utilisateurs et les serveurs de la région d'hébergement

### Variables et groupe de ressources

```
export SUFFIX="EG08"
export LOCATION="France Central"
export RG="rg-dermascan-registre-$SUFFIX"
echo "$SUFFIX | $LOCATION | $RG"
```

Tags du groupe : `--tags projet=dermascan role=registre proprietaire="$SUFFIX" a_detruire="2027-07-01"`

### Mesure 3 — état d'approvisionnement du groupe de ressources

`az group show --name "$RG" --output table` :

```json
{
  "id": "/subscriptions/b1e8aa25-d0ef-4e4c-a766-e02d270e49b6/resourceGroups/rg-dermascan-registre-EG08",
  "location": "francecentral",
  "managedBy": null,
  "name": "rg-dermascan-registre-EG08",
  "properties": {
    "provisioningState": "Succeeded"
  },
  "tags": {
    "a_detruire": "2027-07-01",
    "projet": "dermascan",
    "proprietaire": "EG08",
    "role": "registre"
  },
  "type": "Microsoft.Resources/resourceGroups"
}
```

> `"provisioningState": "Succeeded"`

### Question 2.2 — coût de création du groupe de ressources

> Non, la création du groupe de ressources n'a pas consommé de crédit, l'analyse des coûts montre que le coût est de 0.00, on a créé une entité logique qui ne consomme pas de ressources physiques facturables.

### Mesure 4 — environnement Docker du poste

| **Élément relevé**             | **Commande source** | **Votre valeur** |
| ------------------------------ | ------------------- | ---------------- |
| Version du client Docker       | `docker version`    | 29.8.1           |
| Version du démon (server)      | `docker version`    | 29.8.1           |
| Architecture (`amd64`/`arm64`) | `docker info`       | x86_64 (amd64)   |
| Nombre d'images déjà présentes | `docker info`       | 262              |
| Mémoire allouée au démon       | `docker info`       | 14.39 GiB        |

## Partie 3 — Conteneuriser l'application

### Question 3.1 — pourquoi `0.0.0.0`

> `0.0.0.0` permet d'écouter sur toutes les interfaces réseaux alors que `127.0.0.1` n'écoute que sur l'interface locale qui n'est pas exposée à l'extérieur du conteneur.

### Question 3.2 — `EXPOSE` oublié, le conteneur fonctionne-t-il ?

> `-p` fait essentiellement la même chose que `EXPOSE`, donc le conteneur aurait fonctionné même sans `EXPOSE`.

### Question 3.3 — oubli du `.dockerignore` avec un `.venv/` de 400 Mo

> Si le dockerfile ajoute le `.venv/` dans le build, il sera copié dans l'image ce qui augmentera la durée du build et son poids.

### Mesure 5 — coût du premier build et composition de l'image

`time docker build -t "dermascan-health:0.1.0" .`

| **Mesure**                                               | **Votre valeur**   |
| -------------------------------------------------------- | ------------------ |
| Durée du premier build (cache vide)                      | real    0m6,362s   |
| Taille de l'image                                        | 133mb              |
| Nombre de couches listées par `docker history`           | 9                  |
| Couche la plus lourde, et son instruction                | 5.21MB pip install |
| Taille de l'image de base seule (`docker images python`) | 128mb              |

### Question 3.4 — part de l'image de base

> 128mb / 133mb = ~0.9624, soit 96.24% de la taille finale est imputable à l'image de base seule.

### Mesure 6 — réponse de la sonde `/health` du conteneur local

`docker run -d --name dermascan-health -p 8089:8000 "dermascan-health:0.1.0"` puis `curl -s -i http://localhost:8089/health`

| **Mesure**               | **Votre valeur** |
| ------------------------ | ---------------- |
| Code HTTP retourné       | 200              |
| Champ `hostname` du JSON | 68b2a77db367     |
| Champ `version` du JSON  | 0.1.0            |
| Champ `status` du JSON   | ok               |

### Question 3.5 — origine du `hostname`

> La valeur change avec un redémarrage du conteneur, elle est donc générée aléatoirement par Docker à chaque création d'un conteneur. L'identité d'un conteneur n'est pas persistance.

### Question 3.6 — second conteneur, `APP_VERSION` surchargée

`docker run -d --name dermascan-health-bis -p 8088:8000 -e APP_VERSION="0.2.0" "dermascan-health:0.1.0"`

> L'image est un artefact stable tandis que les variables d'environnement permettent de personnaliser le comportement du conteneur sans modifier l'image elle-même.

### Mesure 7 — effet de l'ordre des instructions sur le cache de build

| **Scénario**                                     | **Durée du build** | **Nombre d'étapes `CACHED`** | **`pip install` rejoué ?** |
| ------------------------------------------------ | ------------------ | ---------------------------- | -------------------------- |
| A — bon ordre, après modification d'`app.py`     | 0.419s             | 3                            | non                        |
| B — mauvais ordre, après modification d'`app.py` | 5.098s             | 2                            | oui                        |
| Écart A/B                                        | 4.679s             | 1                            | /                          |

### Question 3.7 — mécanisme d'invalidation du cache

> Le système de cache de Docker vérifie si une instruction et les fichiers qu'elle affecte n'ont pas changé depuis la dernière construction. Si une couche est identique à une précédente, elle est réutilisée. Sinon, toutes les couches suivantes sont invalidées et divent être reconstruites.

### Question 3.8 — coût du mauvais ordre sur vingt itérations

> L'installation pip avec ces packages a pris 50s sur ma machine. sur 20 installation cela fait 20 * 50s = 1000s soit environ 16 minutes et 40 secondes perdues à cause du mauvais ordre des instructions.

### Mesure 8 — contrôles de l'utilisateur non privilégié

| **Contrôle**              | **Résultat attendu** | **Votre observation**            |
| ------------------------- | -------------------- | -------------------------------- |
| `id` dans le conteneur    | uid non nul          | 10001                            |
| `.Config.User` de l'image | non vide             | appuser                          |
| Écriture dans `/etc`      | refusée              | Cannot touch : Permission denied |

### Question 3.9 — gain d'un attaquant si le processus tourne en root

> Si le processus tourne en root, l'attaquant peut modifier tout les fichiers du conteneur et exécuter n'importe quelle commande ce qui peut faciliter une évasion du conteneur sur l'hôte, ainsi que l'accès à toutes les informations sur le conteneur bien sur.

## Partie 4 — Azure Container Registry

### Mesure 9 — caractéristiques du registre ACR créé

`export ACR_NAME="dermascaneg08"` puis `az acr create --sku basic`

| **Élément**                                                      | **Votre valeur**         |
| ---------------------------------------------------------------- | ------------------------ |
| `loginServer` du registre                                        | dermascaneg08.azurecr.io |
| SKU retenu                                                       | Basic                    |
| État d'approvisionnement                                         | Succeeded                |
| Coût mensuel annoncé pour ce SKU (documentation tarifaire Azure) | $5                       |


### Question 4.1 — comparaison des SKU

> À partir de 100Gb de stoackage, 10 webhooks, ou si l'on souhaite une réplication géographique.

### Question 4.2 — contenu de `~/.docker/config.json`

```
"auths": {
    "dermascaneg08.azurecr.io": {
        "auth": "[redacted]",
        "identitytoken": "[redacted]"
    }
}
```

> Ce fichier contient nos informations d'utilisations. Le rendre public permettrait à n'importe qui de se connecter à notre registre et d'y pousser des images malicieuse ou tirer des images sensibles.

### Question 4.3 — utilisateur administrateur du registre

> - Si l'utilisateur administrateur est compromis, l'attaquant a accès à toutes les images du registre au lieu d'une seule image.
> - Le mot de passe est fixe et ne peut pas être révoqué facilement, contrairement à un jeton d'accès.

### Mesure 10 — coût du premier push vers ACR et identité de l'image poussée

| **Mesure**                                          | **Votre valeur**                                                        |
| --------------------------------------------------- | ----------------------------------------------------------------------- |
| Durée du push                                       | 10m59,668s                                                              |
| Nombre de couches poussées                          | 9                                                                       |
| `IMAGE ID` local et `IMAGE ID` taggé : identiques ? | oui                                                                     |
| Digest (`sha256:...`) retourné en fin de push       | sha256:449aacc6d082f84a2b484c9c2fe87787eba542a5b814119a5db1a48a0279323c |

### Question 4.4 — second push, mécanisme de stockage des couches

> 0m4,441s
> Layer already exists
> Docker ne pousse que les couches qui n'existent pas déjà dans le registre, il y a un mechanisme de cache dans le registre et chaque couche est stockée indépendamment.

### Mesure 11 — exécution de l'image retéléchargée depuis ACR

`docker run -d --name dermascan-from-acr -p 8089:8000 "$IMAGE_FULL"` puis `curl -s http://localhost:8089/health`

| **Mesure**                                                   | **Votre valeur** |
| ------------------------------------------------------------ | ---------------- |
| Durée du `docker run` avec téléchargement                    | 0m6,137s         |
| Le JSON de santé est-il identique à celui de la partie 3.4 ? | non              |
| Le `hostname` a-t-il changé ?                                | oui              |

## Partie 5 — Gouvernance

### Question 5.1 — `pip freeze` vs `requirements.txt`

> 7 packets au lieux de 1.
> Ces packets supplémentaires sont des dépendances transities de Flask. Les audit doivent se faire sur `pip freeze` car il montre l'ensemble des paquets réellement installés dans l'image, y compris les dépendances indirectes. Le package jinja2 même si non ajouté dans le requirements.txt est bien installé dans notre container car il est une dépendance de Flask.

```
$ pip-licenses --packages blinker click Flask itsdangerous Jinja2 MarkupSafe Werkzeug
 Name          Version  License
 Flask         3.0.3    BSD License
 Jinja2        3.1.6    BSD License
 MarkupSafe    3.0.4    BSD-3-Clause
 Werkzeug      3.1.9    BSD-3-Clause
 blinker       1.9.0    MIT License
 click         8.5.0    BSD-3-Clause
 itsdangerous  2.2.0    BSD License
```

### Question 5.2 — licences identifiées et obligations

> CPython : Python Software Foundation License 2.0 (PSF-2.0)
>
> Toutes ces licenses sont permissives. BSD-3-Clause impose de conserver les mentions de copyright et de licence dans les redistributions ce peut impacter légèrement la redistribution.

## Partie 6 — Nettoyage

### Mesure 12 — nettoyage local et coût de ce que l'on laisse actif

Local : conteneurs `dermascan-health`, `dermascan-health-bis` et `dermascan-from-acr` supprimés ; image `dermascan-health:naif` supprimée ; `docker system prune -f` exécuté.

| **Contrôle de fin de séance**                             | **Votre observation**                                                    |
| --------------------------------------------------------- | ------------------------------------------------------------------------ |
| Espace disque libéré par `docker system prune`            | Total reclaimed space: 76.91GB (j'avais pas fait ça depuis longtemps...) |
| Nombre de ressources laissées actives dans `$RG`          | 1 : `dermascaneg08` (Microsoft.ContainerRegistry/registries, Succeeded)  |
| SKU du registre, et son coût journalier estimé            | Basic, $0.167/jour (~$5/mois)                                            |
| Date portée par l'étiquette `a_detruire`                  | 2027-07-01                                                               |
| Nombre de groupes de ressources vous appartenant au total | 1 : `rg-dermascan-registre-EG08`                                         |
| Crédit restant, relevé dans `Cost Management`             | $88                                                                      |

### Question 6.1 — phrase de ticket pour la destruction du registre

> Le registre ACR `dermascaneg08` et son groupe de ressources `rg-dermascan-registre-EG08` créé pourc la séance 1 et consommé par les séances 2, 3 et 4 doit être conservé jusqu'à la fin du projet fil rouge puis détruit avec la commande : `az group delete --name rg-dermascan-registre-EG08 --yes --no-wait`

### Question 6.2 — risque du `--no-wait`

> Une suppression peut échouer pour de nombreuses raisons (problème de réaseau, bug, warning bloquant...). Il est donc nécessaire de vérifier que le groupe a été réellement supprimé. On peut s'en assurer depuis l'interface Azure ou avec la commande `az group exists --name "$RG"` qui doit renvoyer false.
