# DEPLOIEMENT — Séance 3

## Mesure 3 — identification exacte de l'image à déployer

| Relevé                                  | Votre valeur                                                              |
| --------------------------------------- | ------------------------------------------------------------------------- |
| `loginServer`                           | `dermascaneg08.azurecr.io`                                                |
| Nom complet de l'image (`IMAGE_FULL`)   | `dermascaneg08.azurecr.io/dermascan-api:1.0.1`                            |
| Digest `sha256` du tag déployé          | `sha256:0df1b9e549b1d514d6f9943fd4429e32b30b3b10fc3948b95433d5e94af8a728` |
| Architecture déclarée dans le manifeste | `amd64` (os `linux`)                                                      |
| Date de publication de ce tag           | `2026-10-26T11:02:40Z` (UTC)                                              |

## Question 2.1

**Question 2.1** — Vous déployez un tag, mais vous relevez un digest. Que se passerait-il si, demain, un camarade poussait une autre image sous le **même** tag dans ce registre, et que votre service redémarrait ? Le digest relevé aujourd'hui vous servirait-il à quelque chose ? Répondez dans `DEPLOIEMENT.md`.

> Après un redémarrage, l'image sous le tag 1.0.1 la plus récente sera déployée, donc celle du camarade.
> Le digest permet de vérifier l'image exacte déployée. Un digest est unique par image, il est donc important pour la traçabilité. Si le nouveau déploiement avec le même tag pose soucis, les logs montreront que l'image a en réalité changé depuis nos tests et il sera plus simple de tracer la source du problème.

## Mesure 4 — comportement du service avant tout octroi de droit sur le registre

| Relevé avant octroi des droits                    | Votre valeur                                                                                                                                                           |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Code HTTP retourné                                | `503`                                                                                                                                                                  |
| Durée de la réponse                               | `16.402925 s`                                                                                                                                                          |
| Contenu de la page renvoyée (une ligne de résumé) | Page « 503 Service Unavailable » d'Azure : « The server is unable to handle your request right now. This is usually temporary, so please try again in a few minutes. » |

## Mesure 5 — identité managée, rôle accordé, portée du rôle et délai de propagation

| Relevé                                                      | Votre valeur                                                                                                                                                                                 |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `principalId` de l'identité managée                         | `30fc90cc-3947-49d6-90dc-6277ef0f5c53`                                                                                                                                                       |
| Rôle accordé                                                | `AcrPull`                                                                                                                                                                                    |
| Portée exacte du rôle (chemin complet)                      | `/subscriptions/b1e8aa25-d0ef-4e4c-a766-e02d270e49b6/resourceGroups/rg-dermascan-registre-EG08/providers/Microsoft.ContainerRegistry/registries/dermascaneg08`                               |
| Délai entre l'attribution du rôle et le premier pull réussi | environ 3 minutes : rôle attribué à 12:51:18, premier `200` sur `/health` à 12:54:18 (heure locale). Le premier redémarrage (12:51:27) a suffi, aucun second redémarrage n'a été nécessaire. |

## Question 2.2

**Question 2.2** — Il existe un rôle plus large qui aurait aussi fonctionné, et un rôle encore plus large que certains tutoriels recommandent par facilité. Nommez-les tous les deux, et dites précisément ce que votre application pourrait faire en plus avec chacun. Trois lignes dans `DEPLOIEMENT.md`.

> AcrPull permet de lire des images seulement. AcrPush aurait fonctionné et permis d'écrire des images en plus.  Il y a ensuite les rôles Contributor et Owner souvent utilisés par facilité qui permettent un accès complet aux ressources ce qui peut être vraiment risqué surtout en cas de leak/problème de sécurité.

## Question 2.3

**Question 2.3** — L'attribution d'un rôle n'est pas instantanée : elle doit se propager. Si votre premier redémarrage échoue encore, attendez et relancez avant de conclure à une erreur de configuration. Combien de temps avez-vous dû attendre ? Notez-le : c'est une donnée utile pour écrire un script de déploiement automatisé.

> Environ 3 minutes entre l'attribution du rôle (12:51:18) et le premier `200` sur `/health` (12:54:18).
## Mesure 6 — premier démarrage réussi

Un simple `az webapp restart` a répondu `200` une seconde après la commande (l'ancien conteneur répondait encore) : ce n'est pas un vrai démarrage à froid. La mesure ci-dessous a donc été faite avec `az webapp stop` puis `az webapp start`.

| Mesure du premier démarrage                                                                | Votre valeur                                                                            |
| ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Durée entre le démarrage (`start`) et le premier `200` sur `/health`                       | `83 s` (13:00:28 → 13:01:39)                                                            |
| Codes HTTP observés pendant l'attente, dans l'ordre (`000` : délai client de 30 s dépassé) | `403`, `503`, `000`, `200`                                                              |
| Champ `model_loaded` de la réponse `/health`                                               | `true` (réponse complète : `{"model_loaded":true,"status":"ok"}`)                       |
| Version de modèle retournée par `/model/info`                                              | `1.0.0`                                                                                 |
| `probabilite_maligne` et `decision` retournés par `/predict`                               | `0.866314` et `maligne`                                                                 |
| Le `seuil` appliqué par le service est-il celui de votre paquet S2 ?                       | Oui : `0.33334563815577495`, identique à celui de `/model/info` et à celui du paquet S2 |
| Durée de la **première** requête `/predict` (juste après le démarrage)                     | `1.014738 s`                                                                            |
| Durée de la **cinquième** requête `/predict` identique                                     | `0.411199 s`                                                                            |

Les cinq durées relevées après le démarrage : 1.014738 s, 0.607759 s, 0.255381 s, 0.236438 s, 0.411199 s.

## Question 2.4

**Question 2.4** — L'écart entre la première et la cinquième requête est-il nul, faible ou important ? Proposez **deux** causes possibles, et dites pour chacune comment vous pourriez la confirmer ou l'écarter avec les outils dont vous disposez aujourd'hui. C'est une question d'hypothèses, pas de connaissance : une réponse fausse mais testable vaut mieux qu'une réponse juste récitée.

Écart mesuré sur Azure, juste après un démarrage : 1.014738 s pour la première requête, 0.411199 s pour la cinquième.

**Écart :** faible.

**Hypothèse 1 :** Ce temps additionnel vient du réseau (résolution du DNS ou TLS).

**Test :** Pour tester je regarderais simplement si cet écart existe uniquement sur Azure ou en local aussi.

**Résultat :**
- 1ère requête : 0.037 s
- 2ème à 5ème requêtes : 0.007 - 0.009 s
- différence sur Azure : 0.6 s
- différence en local : 0.03 s

**Conclusion :** Le ralentissement est plus léger qu'une fois déployé, le réseau est donc une cause du ralentissement de la première requête. Néanmoins la première requête est là aussi plus lente que les suivantes, ce n'est donc pas la seule raison de ce ralentissement.

**Hypothèse 2 :** Python construit du cache ce qui ralentit les requêtes.

**Test :** Chronométrer l'appel `predict_proba` du pipeline, seul, dans le conteneur de l'image, sans serveur ni réseau : le même appel répété 5 fois dans un processus Python neuf, sur la ligne de `charge.json`.

**Résultat** (durée de chaque appel, en secondes) :

| Processus | Appel 1 | Appel 2 | Appel 3 | Appel 4 | Appel 5 |
| --------- | ------- | ------- | ------- | ------- | ------- |
| 1         | 0.0307  | 0.0057  | 0.0057  | 0.0046  | 0.0060  |
| 2         | 0.0218  | 0.0046  | 0.0047  | 0.0047  | 0.0047  |
| 3         | 0.0206  | 0.0045  | 0.0043  | 0.0044  | 0.0041  |

Différence de 0.015 - 0.025 s

**Conclusion :** Le cache Python est une cause du ralentissement de la première requête. Cela expliquerait presque l'entièreté des 30 ms de différences observées en local une fois le réseau hors de l'équation.

Plus de test serait nécessaire si d'autres facteurs que les 2 mesurés ci-dessus sont responsables du ralentissement, mais cela correspond à des délais extrêmement courts, une investigation plus poussée ne serait donc pas très justifiable.

## 3.1 — Variables d'environnement et port

Réglages posés (13:23) : `PORT=8000`, `MODEL_VERSION=1.0.0`, `LOG_LEVEL=INFO`, `ENVIRONMENT=production`, `SEUIL=0.33334563815577495`.

Configuration effective : **7 réglages** (`WEBSITES_ENABLE_APP_SERVICE_STORAGE=false` et `WEBSITES_PORT=8000` ajoutés par la plateforme, plus les 5 ci-dessus).

**Question 3.1** — `WEBSITES_PORT` et `PORT` doivent-ils porter la même valeur ? Lequel des deux est lu par la plateforme, lequel est lu par votre code ? Que se passe-t-il s'ils diffèrent ? Vous vérifierez expérimentalement en partie 4 — répondez d'abord, mesurez ensuite.

> PORT est celui du container et WEBSITES_PORT est celui qu'azure envoie à
> Si ils ne portent pas la même valeur la requête ne fonctionnera pas, la requête partira à WEBSITES_PORT et se heurtera à un port fermé ou écouté par un autre container.


## 3.2 — Secrets

**Mesure 7** — visibilité réelle du secret `INFERENCE_LOG_SALT` à ses trois points d'exposition.

| Contrôle | Votre observation |
|---|---|
| La valeur du sel est-elle masquée dans la sortie du CLI ? | Non : `az webapp config appsettings list` affiche la valeur complète en clair (32 caractères hexadécimaux). |
| Est-elle visible dans le portail Azure, onglet `Configuration` ? | Masquée par défaut (lien « Show value »), mais un clic suffit pour l'afficher en clair. |
| Est-elle lisible par un processus qui s'exécuterait dans le conteneur ? | Oui : App Service injecte les réglages d'application comme variables d'environnement. Non vérifié par mesure (`az webapp ssh` n'a rien retourné, l'image n'embarque pas de serveur SSH). |

**Question 3.2** — Un réglage d'application n'est pas un coffre-fort : c'est un moyen de transport. Nommez le service Azure qui joue le rôle de coffre-fort, et décrivez en deux lignes ce que la combinaison « ce service + l'identité managée que vous avez créée en 2.3 » permettrait de supprimer complètement de votre configuration. Vous ne l'implémentez pas aujourd'hui ; vous devez savoir le nommer.

> Azure Key Vault est le service qui joue le rôle de coffre-fort. Combiné avec l'identité managée créée en 2.3, il permet de supprimer complètement les secrets de ma configuration : ils restent isolés dans le coffre-fort et accessibles de manière limitée uniquement au service qui les utilise.


## 3.3 — Sonde de santé

**Mesure 8** — effet de la configuration complète après redémarrage : sonde enregistrée, délai de retour au service, nombre de réglages, et effet du seuil à entrée et à modèle rigoureusement identiques, obtenu sans redémarrage.

| Relevé après redémarrage | Votre valeur |
|---|---|
| Chemin de sonde enregistré | `/health` |
| Durée du redémarrage jusqu'au premier `200` | `2 s` (14:21:21 → 14:21:22) : l'ancien conteneur répondait probablement encore, ce n'est pas un démarrage à froid |
| Délai entre le `appsettings set` du seuil abaissé et l'apparition du nouveau seuil dans la réponse | `69 s` (14:23:08 → 14:24:11) |
| Nombre total de réglages d'application | `8` |
| La valeur de `MODEL_VERSION` apparaît-elle dans la réponse de `/model/info` ? | Non : `/model/info` retourne `1.0.0`, lue dans le paquet du modèle, pas dans la variable |
| `probabilite_maligne`, avec votre seuil de S2 | `0.866314` |
| `seuil` et `decision` retournés, avec votre seuil de S2 | `0.33334563815577495`, `maligne` |
| `probabilite_maligne`, avec le seuil abaissé (`0.033334563815577495`) | `0.866314` |
| `seuil` et `decision` retournés, avec le seuil abaissé | `0.03333456381557749`, `maligne` (la décision ne change pas : la probabilité de la ligne de `charge.json` est au-dessus des deux seuils) |

Test complémentaire, hors énoncé : un seuil abaissé ne peut pas changer la décision d'une lésion déjà `maligne`. J'ai donc relevé aussi un seuil **relevé** à `0.9`, avec la même `charge.json` et sans redémarrage manuel.

| Seuil | `probabilite_maligne` | `decision` | Délai d'apparition |
|---|---|---|---|
| `0.33334563815577495` (S2) | `0.866314` | `maligne` | |
| `0.9` | `0.866314` | `bénin` | `90 s` |
| `0.33334563815577495` (restauré) | `0.866314` | `maligne` | `112 s` |

Les valeurs de S2 ont été remises en place après chaque essai.


**Question 3.3** — Votre `/health` retourne `model_loaded`. Imaginez deux versions de cette sonde :

- version 1 : elle retourne `200` dès que le processus Python répond ;
- version 2 : elle retourne `200` uniquement si le modèle est chargé **et** si une inférence de test sur une entrée figée donne le résultat attendu.

Laquelle déployeriez-vous, et quel risque introduit celle que vous écartez ? Traitez le cas d'une instance qui répond mais dont le modèle n'a pas pu être chargé. Quatre lignes dans `DEPLOIEMENT.md`.

> Je déploierais la version 2. Une instance qui répond donc le modèle n'a pas pu être chargée déplace la charge de la gestion d'erreur depuis l'architecture (ici Azure) vers l'appelant (ici le logiciel du médecin). Ceci implique davantage de complexité pour les appelants sans vrai avantage : il n'y a dans tous les cas pas de résultat, la seule solution est de rappeler plus tard. De plus cela empêche la mise en place de load balancing côté Azure : l'instance sera vue comme healthy par Azure qui y routera les requêtes alors même qu'elle ne fonctionne pas, au lieu de les renvoyer vers une autre instance réellement stable.
> Autre souci avec la version 1 moins stricte est le risque de modèle mal paramétré déployé, en particulier dans un cadre médical comme celui-ci, il est impératif de ne pas envoyer en production une instance avec un résultat inattendu qui ne répond pas correctement à nos tests. Dans ce contexte pas de réponse est mieux qu'une mauvaise réponse. Le coût de la version 2 est qu'un test en échec ou trop lent peut retirer du routage une instance en réalité healthy, ce qui avec une seule instance provoquerait une indisponibilité.


**Question 3.4** — Même image, même modèle, même charge utile : la probabilité n'a pas bougé d'un millième et la décision a changé. Répondez en quatre lignes dans `DEPLOIEMENT.md` :

1. Qu'est-ce qui, du modèle ou du service, a changé de comportement ?
2. Le service déployé rend-il « les mêmes décisions » dans les deux cas ? C'est une question de vocabulaire, et elle se pose en audit : un rapport qui annonce « le modèle a changé d'avis » décrit-il correctement ce qui s'est passé ?
3. Un collègue abaisse ce réglage en production sans vous le dire, pour faire remonter le rappel. Quelle trace vous permettrait de le découvrir après coup ? Reliez votre réponse à la grille de la partie 6.
4. Un seuil modifiable sans redéploiement est-il un progrès ou un risque ? Donnez votre position **et** l'argument adverse.

> 1. Les seuils ont changé.
> 2. Il rend des décisions différentes dans les deux cas. Le modèle n'a pas changé d'avis, mais notre interprétation du modèle a changé.
> 3. Il faudrait que chaque ligne de journal contienne le seuil utilisé pour la prédiction. En regardant les logs chronologiquement, on voit quand le seuil change. C'est la ligne « Seuil appliqué et rappel visé » des logs, toujours affichée. Sans elle, on ne verrait que les décisions, pas pourquoi elles ont changé.
> 4. C'est un progrès dans le sens où le seuil peut être contrôlé directement selon la capacité de l'hôpital par rapport au nombre de patients, mais cela a un coût : il ajoute un risque de changement d'avis du modèle, avec des résultats qui apparaissent incohérents.

## 7 — Nettoyage

**Mesure 16** — inventaire de ce qui a réellement été créé, avant destruction (`az resource list --resource-group "$RG" --output table`).

| Relevé avant destruction | Votre valeur |
|---|---|
| Nombre de ressources dans le groupe | `2` |
| Types de ressources listés | `Microsoft.Web/serverFarms` (`plan-dermascan-EG08`) et `Microsoft.Web/sites` (`dermascan-eg08`) |
| Le registre ACR est-il dans **ce** groupe ou dans le groupe du registre ? | Dans le groupe du registre, `rg-dermascan-registre-EG08` : le groupe de la séance 3 ne contient pas l'ACR. |

**Mesure 17** — contrôles de destruction, attribution de rôle orpheline comprise.

Suppression de l'attribution `AcrPull` à 16:42, puis `az group delete --name rg-dermascan-s3-EG08 --yes --no-wait` à 16:42:30.

| Contrôle de fin de séance | Votre observation |
|---|---|
| Le groupe `rg-dermascan-s3-EG08` apparaît-il encore ? | Non : `az group list` ne liste plus que `rg-dermascan-registre-EG08` (disparu à 16:43:40, soit environ 70 s après la commande). |
| Reste-t-il une attribution de rôle sur le registre ? | Non : `az role assignment list --scope "$ACR_ID"` ne renvoie plus rien après la suppression. |
| Le groupe du registre est-il, lui, toujours debout ? | Oui : `rg-dermascan-registre-EG08`, état `Succeeded`. |
| `az group exists` renvoie | `false` |
| Crédit restant, relevé dans `Cost Management` | 86 € sur 88 € (Azure Education, expire le 06/10/2027) ; coûts d'octobre : 2,92 € |
| Écart avec le relevé de la séance précédente | Crédit affiché inchangé (86 € sur 88 €, arrondi à l'euro). Coûts d'octobre : 2,88 € relevés plus tôt dans la séance, 2,92 € maintenant, soit +0,04 €. Les coûts de la séance 3 peuvent encore ne pas être tous comptabilisés. |

**Question 7.1** — Vous devez conserver le registre ACR pour la séance 4 et le projet fil rouge, mais détruire tout le reste. Qu'est-ce qui, dans la façon dont vous avez organisé vos groupes de ressources, rend cette opération sûre en une seule commande ? Qu'auriez-vous dû faire de plus si le registre avait été dans le même groupe que l'application web ?

> On a créé des groupes de ressources ce qui nous permet de séparer les ressources persistantes (registre ACR) de celles uniques à cette séance qui auraient un coût si oubliées (la VM B1).
>
> Nous aurions dû supprimer item par item les ressources de la session au lieu du groupe entier, ce qui augmente les risques d'erreurs.

## Extinction

| Contrôle d'extinction | Fait |
|---|---|
| `az group exists` sur le groupe de la séance renvoie `false` | Oui (16:43:40) |
| Aucun conteneur de la séance dans `docker ps -a` | Oui : aucun conteneur de la séance ; seuls restent ceux d'un autre projet (`lncrawler-*`) |
| Docker Desktop quitté | Sans objet : poste sous Linux, Docker Engine sans Docker Desktop |
| Machine éteinte | |
