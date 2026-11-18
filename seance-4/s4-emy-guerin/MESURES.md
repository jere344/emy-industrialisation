# MESURES — Séance 4

## Mesure 11 — matrice de confusion au seuil (recalculée à partir du CSV)

| | Prédit `a_examiner` | Prédit `surveillance` |
|---|---|---|
| **Malin** | VP = 53 | FN = 6 |
| **Bénin** | FP = 207 | VN = 792 |

| Contrôle | Valeur |
|---|---|
| Somme des quatre cases, comparée au nombre de vignettes de validation | 53 + 6 + 207 + 792 = 1 058 = 1 058 |
| Ma matrice est-elle identique à `matrice_confusion_validation` du meta ? | Non, d'une seule lésion : le meta donne VP = 54 et FN = 5 (FP et VN identiques) |

## Question 4.1

La lésion qui diffère est ISIC_5043386 (un malin) : son score est à 2×10⁻¹⁷ du seuil, donc quasiment égal à lui. `precision_recall_curve` choisit comme seuil le score d'une lésion de validation (les seuils candidats sont les scores eux-mêmes), donc cette lésion est exactement sur la barre et la règle `score >= seuil` la compte « à examiner » dans le meta. Après l'aller-retour par le fichier texte, les derniers chiffres de son score sont arrondis : il devient un peu plus bas que le seuil, et la lésion bascule en « surveillance » (FN 5 → 6, VP 54 → 53).

## Mesure 12 — métriques au seuil, calculées à partir de ma matrice

| Métrique | Formule | Valeur |
|---|---|---|
| Rappel | VP / (VP + FN) | 53 / 59 = 0,898 |
| Précision en validation | VP / (VP + FP) | 53 / 260 = 0,204 |
| Taux de faux positifs | FP / (FP + VN) | 207 / 999 = 0,207 |
| Part des lésions envoyées en examen | (VP + FP) / total | 260 / 1 058 = 0,246 |

Tableau de seuils sur `proba_brute` :

| Seuil sur `proba_brute` | VP | FP | Rappel | Précision |
|---|---|---|---|---|
| 0,5 | 27 | 20 | 0,458 | 0,574 |
| 0,1 | 43 | 88 | 0,729 | 0,328 |
| 0,05 | 47 | 150 | 0,797 | 0,239 |
| `seuil_brut` (0,0288) | 53 | 207 | 0,898 | 0,204 |
| 0,01 | 55 | 402 | 0,932 | 0,120 |

## Question 4.2

Le seuil de 0.5 ici est difficilement défendable : il n'a que très peu de faux positifs, mais laisse passer beaucoup trop de vrais positifs, seulement 0,458 de rappel, donc 32 malins sur 59 partent en surveillance, plus de la moitié des lésions malignes sont manquées. 0,5 n'a aucun statut particulier pour ce modèle : il suppose que les deux erreurs coûtent pareil (alors que rater un malin est bien plus grave) et que le modèle a appris sur une prévalence proche de la réalité (alors qu'il a appris à 5,55 % de malins contre 0,135 % dans le flux réel). Le bon seuil se déduit du rappel visé.

## Mesure 13 — recalibration

| Grandeur | Mon calcul | Valeur du meta |
|---|---|---|
| β | 5 000 / 217 183 = 0,02302 | `taux_negatifs` : 0,02302 |
| ln β | −3,7713 | `correction_logit` : −3,7713 |
| Seuil brut | — | `seuil_brut` : 0,028816 |
| Seuil recalibré σ(logit(seuil brut) + ln β) | 0,000682614 | `seuil` : 0,000682614 |
| Décisions de validation changées par la recalibration | 0 | — |
| Précision projetée sur le flux réel : rappel × π / (rappel × π + TFP × (1 − π)) | 0,00583 | `precision_projetee_prevalence_reelle` : 0,00594 |
| Lésions examinées par maligne trouvée | 171 | `lesions_examinees_par_maligne_reelle` : 168 |
| Même grandeur pour le modèle tabulaire de S2 (`MESURES.md` de S2) | précision 0,0045 ; 223 lésions par maligne | — |

Mes deux dernières valeurs diffèrent légèrement du meta car ma matrice a VP = 53 et celle du meta VP = 54 (voir question 4.1), donc le rappel utilisé n'est pas le même.

## Question 4.3

Pour le dermatologue : la recalibration ne change aucune décision, mais elle recadre le chiffre que donne le modèle pour que `probabilite_maligne` ne soit pas un nombre arbitraire, propre au monde d'entraînement (5,55 % de malins), mais un pourcentage qui correspond à la réalité du flux (0,135 % de malins). Sans elle, il lirait « 2,9 % » pour une lésion dont le risque réel est d'environ 0,07 %.
Pour l'analyste de la séance 5 : les probabilités servies sont à l'échelle du flux réel, décalées d'un terme connu et fixe (`correction_logit`) par rapport à celles de l'entraînement. Il peut donc les comparer proprement, et si la distribution servie change, c'est le flux qui a changé et non l'effet de l'échantillonnage.

## Question 4.4

| Erreur de déploiement | Lésions examinées | Part examinée | Rappel |
|---|---|---|---|
| 1. L'API sert `proba_brute` mais applique le seuil recalibré | 948 sur 1 058 | 89,6 % | 0,983 (58/59) |
| 2. L'API sert la probabilité recalibrée mais applique le seuil brut | 39 sur 1 058 | 3,7 % | 0,407 (24/59) |

Un score recalibré avec un seuil brut entraîne un taux de rappel beaucoup trop bas, avec seulement 24/59 lésions malignes découvertes. En comparaison, un score brut avec un seuil recalibré donne une part examinée trop élevée, ce qui entraîne plus d'examens à passer pour les médecins, près de 90 % de part examinée, ce qui correspond presque à la situation sans le système. Une erreur est dangereuse pour les patients qui ne seront pas traités (la 2), l'autre est gênante mais pas grave (la 1).

## Question 4.5

Pondérer les positifs d'un facteur w fait croire au réseau que les malins sont w fois plus fréquents : il surestime encore plus la probabilité d'être malin. Il faudrait ajouter un terme négatif, −ln w, à la correction de prior (qui deviendrait ln β − ln w), pour réduire les cotes et compenser cette surestimation.

## Mesure 14 — PR-AUC ramenées à une même prévalence

| | PR-AUC | Hasard (prévalence) |
|---|---|---|
| S4, validation sous-échantillonnée (meta) | 0,4932 | 0,0558 |
| S4, négatifs repondérés par 1/β | 0,0455 | 0,00136 |
| S2, flux réel (mon `MESURES.md`, régression logistique) | 0,0381 | 0,00135 |

## Question 4.6

La ROC-AUC compare le rappel (la part de VP) et le taux de FP. Ce sont des pourcentages, si on ajoute beaucoup de bénins, le nombre de FP augmente dans la même proportion, donc le pourcentage ne bouge pas. La précision (la part de VP parmi les lésions déclarées malignes) compare un nombre de malins qui ne change pas à un nombre de FP qui augmente : elle diminue, et donc la PR-AUC aussi. La PR-AUC dépend de la prévalence et pas la ROC-AUC.
Une fois ramenées à la même prévalence les deux PR-AUC sont du même ordre de grandeur (0,0455 pour S4, 0,0381 pour S2). On ne peut pas conclure que le CNN est meilleur, deplus S4 a été entrainé avec seulement 59 malin envalidation contre 110 pour S2, ce qui rend sa PR-AUC très instable.
## 5.1 — Écarts par rapport à l'énoncé (Dockerfile)

Mon Dockerfile de S2 était sur `python:3.14-slim`, sans variable `MODEL_PATH` : la ligne à changer était `COPY model/modele.joblib ./model/`, remplacée par `COPY model/modele.pt model/modele_meta.json ./model/` (`app.py` lit `MODEL_PATH`, valeur par défaut `model/modele.pt`).
Cette première image (`python:3.14-slim`) a échoué à `docker scout cves --exit-code` : 37 CVE (0 C / 7 H / 3 M / 27 L), code retour 2, dont des CVE système Debian sans correctif (`captures/docker_scout_cves_python-slim.txt`). Je suis donc passé à une base Wolfi comme le décrit l'énoncé (`cgr.dev/chainguard/wolfi-base`, Python 3.12, `pip` retiré dans le même `RUN`, utilisateur non root, même `CMD`). Le Dockerfile change donc de plus d'une ligne par rapport à S2.

## Mesure 15 — construction et scan

| Relevé | Valeur |
|---|---|
| Durée de la construction à froid | 79,6 s (base Wolfi) ; 63,8 s pour la première tentative sur `python:3.14-slim` |
| Taille de l'image S4 (`docker images`) | 1,13 Go |
| Taille de l'image S2 (même commande) | 467 Mo |
| Résultat de `docker scout cves` : C / H / M / L, et code retour | 0 / 0 / 0 / 0, code retour 0 (114 paquets). Première tentative `python:3.14-slim` : 0 / 7 / 3 / 27, code retour 2 |
| Exceptions écrites | aucune |

## Mesure 16 — démarrage hors ligne et concordance

| Relevé | Valeur |
|---|---|
| Délai jusqu'au premier `/health` à 200, sous `--network none` | 4,5 s (docker run jusqu'au premier 200, interrogation toutes les secondes) |
| Corps de `/health` | `{"hostname":"fb13289f1105","model_loaded":true,"service":"isic-vignettes-api","status":"ok","uptime_seconds":0.4}` |
| `probabilite_maligne` et `decision` servies pour l'image de contrôle (ISIC_0104229) | 0,062463 ; `a_examiner` |
| `controle.probabilite_maligne` du meta, et écart absolu | 0,062464 ; 1×10⁻⁶ (sous la tolérance de 10⁻⁵) |
| Codes HTTP : sans champ `image` / fichier qui n'est pas une image | 400 / 400 |

## Mesure 17 — mesures comparatives S2 / S4

| Grandeur | S2 | S4 |
|---|---|---|
| Taille de l'image | 467 Mo | 1,13 Go |
| Taille du fichier de modèle | 9,2 Ko | 44 780 171 octets (42,7 Mio) |
| Durée de construction à froid | 56,6 s | 79,6 s |
| Démarrage jusqu'au premier `/health` à 200 | 3,0 s | 3,3 s |
| Mémoire du conteneur (`docker stats`, après les 55 appels de mesure) | 217,7 MiB | 314,4 MiB |
| Latence `/predict` p50 / p95, local, 50 appels | 7,7 ms / 8,7 ms | 15,1 ms / 17,1 ms |
| Latence du réseau seul, lot de 1 (mesure 9) | — | 14,3 ms / 16,4 ms (CPU) |
| Architecture du poste | amd64 natif (x86_64) | amd64 natif (x86_64) |

Notes : le démarrage, la mémoire et la latence p50/p95 de S2 ont été mesurés aujourd'hui sur l'image `dermascan-api:1.0.0` avec la même méthode que S4 (mon `MESURES.md` de S2 ne les donnait pas sous cette forme : médiane 7,6 ms sur 10 appels). Les deux images ne sont pas sur la même base (S2 `python:3.14-slim`, S4 Wolfi).

## Question 5.1

Le chargement du modèle est passé d'un pipeline scikit-learn à ResNet18 pour correspondre à notre changement de type de modèle.
L'entrée de /predict, qui était une suite de variables en JSON, est maintenant une image, ce qui correspond bien plus à une utilisation réelle.
Une correction de prior `proba = σ(logit + correction_logit)` a été ajoutée pour que les chiffres affichés aux utilisateurs ne soient plus des chiffres apparemment arbitraires, mais un pourcentage basé sur la réalité.
/model/info retourne plus d'informations, avec sha256_poids et version_deployee, qui permettent plus de traçabilité des résultats.
Tout le reste (les routes, les clés de la réponse, les codes d'erreur) ne change pas. Chaque changement non nécessaire que l'on applique est une mise à jour qui devra être appliquée par nos utilisateurs, il est donc correct de faire le moins de modifications possibles sur nos interfaces pour faciliter la collaboration.
Deux exceptions que les postes de consultation devront gérer : l'entrée de /predict n'est plus un JSON mais une image en multipart, et la valeur du champ `decision` change (`maligne`/`bénin` en S2, `a_examiner`/`surveillance` en S4), même si sa clé reste la même. Ces deux changements sont nécessaires pour que le modèle soit utilisable dans la vraie vie.

## Question 5.2

`resnet18(weights=None)` crée seulement la structure du réseau, sans poids préentraînés : avec `weights="IMAGENET1K_V1"`, le conteneur chercherait à télécharger les poids ImageNet au démarrage, ce qui échouerait sans réseau, et serait de toute façon inutile puisque `modele.pt` les remplace juste après. Le conteneur démarre donc hors ligne et sans télécharger 45 Mo pour rien.
`torch.load(..., weights_only=True)` sert à la sécurité : le format `.pt` est un pickle, qui peut contenir des instructions exécutées à la lecture du fichier. Un `modele.pt` piégé pourrait donc exécuter des commandes sur le serveur dès le chargement ; avec `weights_only=True`, le chargement refuse tout ce qui n'est pas des données simples (tenseurs). On peut détecter qu'un fichier a été remplacé en vérifiant son hash (`sha256_poids` du meta, contrôlé par `verifier_s4.py`).

## Question 5.3

Passer par du base64 dans du JSON pour l'image fonctionnerait, mais c'est une transformation inutile. Le client doit encoder l'image en base64 et la placer dans du JSON, que nous devons ensuite valider, extraire et décoder : plus de travail des deux côtés, pour un résultat identique. Le format HTTP supporte nativement l'envoi de fichiers en multipart, autant l'utiliser pour faciliter la vie à tout le monde.

1. Taille transférée : sur ma vignette de contrôle (ISIC_0104229.jpg, 2 653 octets), le multipart envoie 2 860 octets (+207 octets d'en-têtes) contre 3 553 octets en JSON + base64 (+34 %, car le base64 écrit 4 caractères pour 3 octets).
2. Simplicité : le multipart se teste simplement avec `curl -F`, sans encodage côté client ni décodage côté API.

## Question 5.4

Avec un autre filtre (BICUBIC, NEAREST, ou un resize fait avec OpenCV), les pixels envoyés au réseau ne seraient pas exactement ceux vus pendant l'entraînement. Le modèle répondrait quand même, sans erreur, mais avec une probabilité un peu différente, et une lésion proche du seuil pourrait changer de décision sans que personne ne le remarque. Les tests de format et de code HTTP passeraient quand même.
La mesure 16 est la seule qui compare la probabilité donnée par l'API à celle calculée par le code d'entraînement (`controle.probabilite_maligne` du meta) à 10⁻⁵ près, c'est donc la seule qui vérifie que le prétraitement est le même des deux côtés.

## Question 5.5

Avec un p50 de 15,1 ms en local : 1 / 0,0151 = environ 66 requêtes par seconde, donc à peu près 238 000 lésions par heure au maximum.
C'est très optimiste pour le B1. La mesure est faite sur mon poste, plus rapide que le vCPU partagé du B1, sans passer par internet (TLS et aller-retour réseau, environ 22 ms mesurés en S3), et avec une seule requête à la fois. Sur Azure les requêtes arrivent en même temps et attendent derrière l'unique worker, et `/health` et `/model/info` prennent aussi du temps.

## 5.5 — Azure : publication et déploiement

Valeurs utilisées : `SUFFIX=EG08`, `RG=rg-dermascan-s4-EG08`, registre `dermascaneg08` (celui de S1, il ne suit pas le nom `acrdermascan$SUFFIX` de l'énoncé), plan `B1`, `WEBSITES_PORT=8000`, `WEBSITES_CONTAINER_START_TIME_LIMIT=600`, rôle `AcrPull`, tag `a_detruire="fin-de-seance-2026-11-17"`. Les commandes sont dans `deploiement/env.sh` et les sorties dans `deploiement/`.

J'ai mis 600 s pour `WEBSITES_CONTAINER_START_TIME_LIMIT` : l'image est grosse et torch est long à charger sur un seul vCPU, les 230 s par défaut risquaient de ne pas suffire. 600 s reste loin de la limite de 1 800 s.

`locustfile_s4.py` : `wait_time = between(2, 5)` comme en S3, poids 10 pour `/predict`, 2 pour `/health` et 1 pour `/model/info` (les mêmes qu'en S3). Paliers à 5 et 20 utilisateurs : ce sont mes paliers 1 et 2 de S3, je peux donc comparer directement. `-r 5`, 3 minutes chacun.

Premier essai raté : le réseau de mon poste passait par un proxy local, et le client de Locust l'ignore (il met `trust_env = False`). Toutes les requêtes ont échoué en erreur DNS sans jamais arriver sur Azure. J'ai supprimé ces sorties et relancé en remettant `trust_env = True` sur le client, sans toucher au scénario. Le proxy ajoute un petit détour, les latences sont peut-être un peu plus hautes qu'en S3 à cause de ça.

## Mesure 18 — le service S4 en ligne

| Relevé | Valeur |
|---|---|
| Durée du `docker push`, et taille annoncée | 212 s ; 383 Mo compressés (somme des couches), 1,13 Go une fois décompressée |
| Tags présents dans le dépôt `dermascan-api` | `1.0.0`, `1.0.1`, `2.0.0` |
| Digest de l'image poussée | `sha256:5f3d5e4464fc449925b6b7cbf5f90e091de4bac9381431c41645004e0a920c3d` |
| Durée entre le `restart` et le premier `200` sur `/health` | entre 6 min 40 s et 7 min 30 s : restart à 10:05:54, premier 200 vu à 10:13:22, mais je n'ai pas pu interroger l'URL avant 10:12 (même problème de proxy), et à 10:12:30 elle ne répondait pas encore. Au premier 200, `uptime_seconds` valait 11,3 s : presque toute l'attente vient du téléchargement de l'image depuis le registre, l'API démarre vite |
| `probabilite_maligne` et `decision` servies sur Azure pour l'image de contrôle | 0,062463 ; `a_examiner` (pareil qu'en local, 1×10⁻⁶ d'écart avec le meta) |
| `version` et `version_deployee` de `/model/info` | `2.0.0` et `2.0.0` |

Captures : `captures/predict_azure.json`, `captures/model_info_azure.json`.

## Mesure 19 — charge sur le service S4

Lignes `Aggregated` de `palier_s4_*_stats.csv` (de 09:22:31 à 09:28:33 UTC).

| Palier | Utilisateurs | Débit (req/s) | p50 (ms) | p95 (ms) | p99 (ms) | Échecs (%) |
|---|---|---|---|---|---|---|
| 1 | 5 | 1,37 | 160 | 390 | 1 500 | 0 (0 / 246) |
| 2 | 20 | 5,02 | 210 | 2 200 | 5 100 | 0 (0 / 900) |
| S3, palier au même nombre d'utilisateurs | 5 | 1,36 | 85 | 520 | 850 | 0 (0 / 243) |
| S3, palier 2 | 20 | 5,24 | 97 | 1 200 | 2 500 | 0 (0 / 940) |

`POST /predict` seul : p50 170 ms et p95 410 ms au palier 1, p50 230 ms et p95 2 300 ms au palier 2.
CPU du plan minute par minute, de 09:21 à 09:28 UTC : 20, 16, 20, 49, 27, 22, 38, 53 %. Mémoire entre 81 et 82 % (69 à 76 % en S3).

## Question 5.6

À 5 utilisateurs, le p50 passe de 85 ms en S3 à 160 ms en S4, presque deux fois plus. Ça vient de la latence de `/predict` de la mesure 17 : 15,1 ms en S4 contre 7,7 ms en S2, en local. ResNet18 demande beaucoup plus de calcul qu'une régression logistique (14,3 ms pour le réseau seul, mesure 9), et c'est encore pire sur le vCPU du B1. La mémoire aussi monte : 81 % sur le plan contre 69 à 76 % en S3.
Mon engagement de S3 était « jusqu'à 20 utilisateurs, 95 % des prédictions en moins de 1,2 s, moins de 1 % d'échecs ». Avec le nouveau modèle il ne tient plus : à 20 utilisateurs le p95 est à 2,2 s, même si aucune requête n'a échoué. Pour le garder sur le même plan il faudrait descendre à 5 ou 10 utilisateurs, prendre un plan plus gros, ou alléger le modèle (c'est le sujet de la séance 5).

## Mesure 21 — contrôles de fin de séance

| Contrôle | Observation |
|---|---|
| Ressources listées dans `$RG` avant destruction | `plan-dermascan-s4-EG08` (plan App Service) et `dermascan-api-s4-EG08` (web app) |
| `az group exists --name "$RG"` | `false` à 10:32:10, environ 2 min 30 après le `az group delete` de 10:29:37 |
| `az group exists --name "$RG_REGISTRE"` | `true` |
| Tags présents dans le registre après nettoyage | `1.0.0`, `1.0.1`, `2.0.0` |
| Point de reprise supprimé du Drive, session Colab terminée | Pas concerné : entraînement fait en local, sans Colab ni Drive. Il ne reste pas de `reprise.pt` dans `sorties/` |
| Crédit restant, relevé dans `Cost Management`, et écart avec S3 | Coût réel total depuis septembre : 6,21 €, dont 6,15 € pour le Container Registry et 0,07 € pour App Service. Je n'avais pas fait ce relevé en S3, je ne peux pas donner l'écart exact. Ce qui coûte, c'est le registre Basic : environ 0,15 € par jour même sans l'utiliser |

L'attribution `AcrPull` a été supprimée avant le groupe (10:29:32), `az role assignment list --scope "$ACR_ID"` ne renvoie plus rien. En local : conteneur `dermascan-api-s4` supprimé, alias `dermascaneg08.azurecr.io/dermascan-api:2.0.0` retiré, `dermascan-api:2.0.0` gardé pour la S5.

## Question 7.1

En S3 on supprimait le groupe qu'on venait de créer, dans le même shell, et à part celui du registre c'était le seul groupe. Maintenant `$RG` et `$RG_REGISTRE` sont exportés dans le même shell, et le registre contient `1.0.0`, `1.0.1` et `2.0.0` dont on a besoin en S5.
Si `$RG` a été écrasé (vieux shell de S3, mauvais copier-coller, variable vide), `az group delete --yes` supprimerait le mauvais groupe sans rien demander, peut-être celui du registre. Avec le `case`, tout ce qui ne commence pas par `rg-dermascan-s4-` est refusé, donc le registre ne peut pas partir par erreur.
