# MESURES — Séance 5

## Mesure 1 — point de départ (S4)

| Grandeur (S4)                                                          | Ma valeur                                                                          |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Empreinte de `modele.pt`, identique à `sha256_poids` (oui / non)       | oui (`48f9d0e99950da7b…`)                                                          |
| Taille de l'image `dermascan-api:2.0.0`                                | 1,13 Go                                                                            |
| Taille du fichier de modèle                                            | 44 780 171 octets (42,7 Mio)                                                       |
| Démarrage jusqu'au premier `/health` à `200`                           | 3,3 s (mesure 17) ; 4,5 s hors ligne (mesure 16)                                   |
| Mémoire du conteneur au repos                                          | 314,4 MiB (`docker stats` après les 55 appels de mesure)                           |
| Latence `/predict` p50 / p95, local                                    | 15,1 ms / 17,1 ms                                                                  |
| Mesure 19 : p50 et p95 au palier le plus chargé sur `B1`, CPU du plan  | palier 2 (20 utilisateurs) : 210 ms / 2 200 ms ; CPU max 53 % (moyenne par minute) |
| Mesure 20 : part de `3D: white` dans votre manifeste et dans l'archive | 55,23 % / 52,73 %                                                                  |

## Question 1.1

La comparaison doit être faite avec du matériel proche de ce qui sera utilisé en production. Le plan a un seul vCPU quand mon poste en a 16. Ainsi, si un des moteurs supporte le parallélisme, il sera grandement avantagé dans nos tests, mais pas lors d'une exécution réelle.

## Question 1.2

Les premiers appels peuvent générer du cache et d'autres optimisations variées, ils ne sont donc pas représentatifs de la vie du système. Dans notre cas en particulier, le premier appel réserve la mémoire de travail du moteur, il sera beaucoup plus lent.

## Mesure 2 — l'export (`QUANTIFIER=0 python exporter_onnx.py model`)

Blancs remplis : `input_names=["entree"]` (nom attendu par `comparer.py` ; `app.py` le lit dans la session), `external_data=False` (un seul fichier, poids inclus).

| Relevé                                                               | Ma valeur                                                                  |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Taille de `modele.onnx`, comparée à `modele.pt`                      | 44 781 762 octets contre 44 780 171 (+1 591 octets, 44,8 Mo tous les deux) |
| Empreinte de `modele.onnx` (16 premiers caractères)                  | `88b0919750a3c7fa`                                                         |
| Écart maximal de logit sur le lot de contrôle, affiché par le script | 8,1×10⁻⁶ (lot aléatoire de 4)                                              |
| L'export relancé une seconde fois donne-t-il la même empreinte ?     | oui (`88b0919750a3c7fa…` les deux fois)                                    |

## Question 2.1

Sans cette ligne, le script exporterait le réseau en mode entraînement, avec des couches `BatchNorm2d` mobiles sur les moyennes du lot en cours au lieu des moyennes apprises figées du réseau en évaluation. Sans `eval()`, la référence PyTorch du script tourne aussi en mode entraînement, alors que l'export fige les moyennes apprises : les deux calculs diffèrent et l'assertion échoue. Testé : écart de logit de 4,84, `AssertionError`.

TL;DR : sans ça, les évaluations en production dépendraient des autres images évaluées dans le même lot au lieu des données d'entraînement.

## Question 2.2

`check_model` vérifie le modèle comme un compilateur : qu'il passe ne suffit pas à affirmer que le résultat est parfait. Il valide la structure, mais pas les sorties. `assert ecart < 1e-4`, lui, est un test qui compare les sorties du réseau avec celles de PyTorch.

## Question 2.3

Le réseau a été entraîné sur des images en 3 couleurs de 128 px par 128 px. Il faut lui donner des entrées équivalentes, d'où le `.resize((t, t), Image.BILINEAR)` qui s'assure du format en ramenant l'image de 300 px à 128 px.

## Mesure 3 — les trois variantes (`python comparer.py model`, 1 058 vignettes de validation dont 59 malignes, seuil 0,000683)

`python exporter_onnx.py model` : `modele_int8.onnx` 11,3 Mo, sha256 `352613e2daf83e23`.

| Variante  | Taille (Mo) | p50 (ms) | p95 (ms) | Proba de contrôle | Rappel au seuil | Alertes | ROC-AUC | Écart max de proba | Décisions changées |
| --------- | ----------- | -------- | -------- | ----------------- | --------------- | ------- | ------- | ------------------ | ------------------ |
| PyTorch   | 44,8        | 28,84    | 32,10    | 0,062464          | 0,9153 (54/59)  | 261     | 0,9058  | 0                  | 0                  |
| ONNX      | 44,8        | 16,86    | 19,96    | 0,062464          | 0,8983 (53/59)  | 260     | 0,9058  | 3×10⁻⁶             | 1                  |
| ONNX int8 | 11,3        | 14,80    | 17,53    | 0,088594          | 0,8814 (52/59)  | 280     | 0,9051  | 0,23               | 47                 |

## Mesure 4 — ce que l'int8 change

| Relevé                                                              | Ma valeur                                                               |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Décisions passées en `a_examiner` / passées en `surveillance`       | 33 / 14                                                                 |
| Malignes parmi les décisions changées                               | 2 (ISIC_0521019 et ISIC_5035525, toutes deux passées en `surveillance`) |
| Rapport des probabilités int8 / PyTorch : médiane, minimum, maximum | 1,084 ; 0,321 ; 3,774                                                   |

La seule décision changée par ONNX float32 est ISIC_5043386 (maligne) : probabilité PyTorch à 1,1×10⁻⁹ au-dessus du seuil, ONNX la passe juste en dessous. L'int8 la garde en `a_examiner` (0,000706).

## Question 3.1

Chez moi, le rappel de PyTorch mesuré par `comparer.py` (0,9153, 54/59) est celui du meta ; c'est ONNX float32 qui perd une maligne : ISIC_5043386, la plus proche du seuil (PyTorch 1,1×10⁻⁹ au-dessus, ONNX juste en dessous), la même lésion qu'en question 4.1 de S4.

Les décisions changées semblent meilleures : elles montrent exactement quelles lésions bougent, même pour un problème d'arrondi. Mais on veut aussi s'assurer qu'il n'y a pas de grandes variations entre chaque lésion. Le taux de rappel peut être le même par hasard, mais les résultats derrière complètement différents.

## Question 3.2

Sur mon poste, ONNX est plus rapide (p50 16,9 ms contre 28,8 ms, 1 fil chacun), mais ça ne prouve rien pour le vCPU de B1, qui est un processeur complètement différent de celui de mon poste (autre modèle, partagé, pas forcément les mêmes instructions de calcul). Il reste quand même un gain, celui du poids de ce qu'il faut installer : PyTorch pèse des centaines de Mo (1,2 Go pour `torch` dans mon `.venv`), `onnxruntime` beaucoup moins (68 Mo).

## Question 3.3

La version int8 a un taux de rappel suffisant (de justesse, 0,881 > 0,88) mais 47 décisions changées et un écart de 0,23, soit bien au-dessus de notre seuil de 10⁻⁵ (23 000×). C'est donc un nouveau modèle, il faudrait le publier sous la version 2.1.0.
Au vu de ces données, il vaut mieux publier le modèle ONNX float32 plutôt que le modèle int8 : le modèle int8 est certes un peu plus efficace, il est 4× plus léger, mais pas réellement plus rapide (p95 similaire à ONNX) et bien moins précis.

Exception déclarée au critère « 0 décision changée » : la seule décision changée par ONNX float32 est ISIC_5043386, à 1,1×10⁻⁹ du seuil, avec des poids identiques. C'est un artefact d'arrondi : le même `modele.pt` sur un autre processeur ou une autre version de PyTorch pourrait la faire basculer de la même façon. ONNX float32 reste le modèle `2.0.0`.

| Décision de déploiement | Ma valeur                    |
| ----------------------- | ---------------------------- |
| Variante déployée       | ONNX float32 (`modele.onnx`) |
| Version du modèle servi | `2.0.0`                      |

## Question 3.4

Il faudrait refaire la même batterie de tests et de mesures qu'en S4 (matrice de confusion au seuil, rappel, précision en validation), ainsi que mettre à jour nos chiffres sur la fiabilité du modèle présentés commercialement (model card).
Faite partiellement aujourd'hui : la première, avec `comparer.py` (rappel, alertes, ROC-AUC sur les 1 058 vignettes de validation), sans la matrice complète ni un jeu indépendant.

## Question 4.1

- Le moteur d'inférence : le moteur est passé de Torch à ONNX, les résultats sont similaires mais ONNX est plus léger.
- Covariables : 4 champs facultatifs mais contrôlés ont été ajoutés pour plus facilement mesurer une dérive dans les données d'entrée.
- Ligne de journal : une journalisation plus fine et pseudonymisée a été ajoutée pour plus facilement suivre les événements et les évolutions exactes.
- `/model/info` : des informations supplémentaires ont été ajoutées pour plus de transparence pour l'utilisateur et de traçabilité.

Globalement, les changements ont surtout pour objectif un meilleur suivi de la vie du modèle et des potentiels imprévus, avec un changement de moteur pour une optimisation « gratuite ».

## Question 4.2

Contre l'option 1 : l'API tabulaire de S2 est un autre service, avec d'autres appels et d'autres patients, ce n'est pas le flux que reçoit réellement notre modèle d'images.
Contre l'option 2 : une statistique de l'image comme la luminance moyenne peut nous dire que les images ont changé, mais pas pourquoi (nouvel appareil, autre partie du corps...), on ne saurait pas quoi corriger.
La faiblesse de l'option 3 : les covariables sont fournies par le poste de consultation, l'API ne peut pas les vérifier sur l'image. S'il les omet, elles sont comptées comme absentes et le PSI est calculé sans elles, la dérive peut passer inaperçue. S'il ment (par exemple « 3D: white » envoyé par défaut), la dérive est masquée et on a une fausse sécurité.

## Question 4.3

On garde le champ facultatif pour garder une compatibilité avec les systèmes existants (backward compatibility), malgré les implications : pas de suivi sur ces informations pour les postes antérieurs. Par contre, sur des données nouvelles, il faut absolument que l'on soit au courant des changements de systèmes, pour indiquer ce qu'il sait gérer et ce qu'il ne sait pas, et ainsi prévenir une dérive.
Une modalité inconnue acceptée ferait exploser le PSI (proportion plancher dans la référence) ; une absence se suit à part, dans le taux d'absence.

## Question 4.4

Chaque paquet ajouté à une image est un nouveau risque de CVE, il est donc préférable d'avoir le moins de dépendances possible. Dans notre cas, nous démarrons le conteneur avec `--network none`, le SDK ne pourra donc pas publier ses données à Azure.
De plus, le service que l'on utilise, App Service, récupère déjà la sortie standard du conteneur. On pourrait imaginer le même comportement sur un système en production où le modèle tourne sur Docker, qui publie lui-même le stdout (standard output) sur un Grafana pour une gestion centralisée.

## 4.2 — Écarts par rapport à l'énoncé

- Le `.dockerignore` ne faisait pas partie des fichiers distribués : reconstruit à partir de celui de S4 (`api-s4/.dockerignore`), plus `**/*.csv`, `**/*.zip` et `**/*.pt`. Mes `.dockerignore` de S1 à S4 n'avaient pas les lignes `**/*.csv` et `**/*.zip` que l'énoncé dit héritées de S2.
- Le `Dockerfile` distribué diffère du mien de S4 par plus que `MODEL_PATH` : base Wolfi figée par digest, paquets `apk`, `CMD`, et surtout mon Dockerfile S4 contenait `chown -R appuser /app` (voir question 4.5).
- Blancs : `cp model/modele.onnx api-s5/model/modele.onnx`, `m["version"], m["variante"] = "2.0.0", "onnx"`.

## Question 4.5

Contrairement à l'énoncé, mon Dockerfile S4 contenait `RUN adduser -D -u 10001 appuser && chown -R appuser /app`. `docker history dermascan-api:2.0.0` : cette couche pèse 44,8 MB, comme la couche `COPY model/modele.pt` juste avant.

a) 44,8 MB, soit le poids du modèle.
b) L'API ne fait que lire ses fichiers. Même si le fichier est la propriété de root et que l'utilisateur est `appuser`, il possède par défaut la permission de lecture pour les autres utilisateurs. Le `chown` est inutile.

## Question 4.6

Test (contexte jetable avec `racine.pt`, `racine.csv`, `model/modele.pt`, `model/manifeste.csv`) : avec `*.pt` et `*.csv`, `model/modele.pt` et `model/manifeste.csv` entrent dans l'image ; avec `**/*.pt` et `**/*.csv`, aucun des quatre.

`*.pt` ne matche que les fichiers à la racine, alors que `**/*.pt` matche, quelle que soit leur position, tous les fichiers finissant par `.pt`.
Dans notre cas actuel, ça ne change rien puisque seul le dossier `model/` est copié et qu'il ne contient rien de privé, mais en cas d'erreur, le `.dockerignore` garantit qu'aucun fichier d'entraînement en `.csv` ou `.pt` n'entre dans notre image.

## 4.3 — Version de l'image

`VERSION=2.1.0` (tag de l'image et `MODEL_VERSION` ; le modèle reste `2.0.0` dans le meta). S'il n'y avait que le moteur, j'aurais dit 2.0.1, mais comme il y a modification avec les covariables (on peut considérer que l'appel sans covariable est noté deprecated sans pour autant être abandonné tout de suite), on peut dire 2.1.0.
Note : aujourd'hui, rien dans l'API ne signale cette dépréciation ; il faudrait noter un avertissement deprecated quelque part (documentation, en-tête de réponse) pour faciliter les montées de version futures.

## Mesure 5 — l'image S5 (`dermascan-api:2.1.0`)

Écart : le terminal utilisé tourne dans un environnement réseau isolé (proxy HTTP local) qui n'atteint pas le `localhost` du poste. Les commandes `curl` (et plus loin les boucles de latence et `rejouer_flux.py`) sont lancées depuis un conteneur client qui partage le réseau du conteneur de l'API (`docker run --network container:dermascan-api-s5`, dossier S5 monté). Mêmes commandes, mêmes URL `http://localhost:8000`.

| Relevé                                                                                 | Ma valeur                                                                            |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Code retour de `docker scout cves --exit-code`, et décompte C / H / M / L              | 0 ; 0 / 0 / 0 / 0 (108 paquets, `captures/docker_scout_cves_2.1.0.txt`)              |
| Durée de construction                                                                  | 58,5 s                                                                               |
| `probabilite_maligne` de l'image de contrôle servie par le conteneur                   | 0,062464 (`a_examiner`)                                                              |
| Probabilité de contrôle de la même variante dans la mesure 3, et écart                 | 0,062464 ; écart 0 à 10⁻⁶ près                                                       |
| `sha256_fichier_servi` de `/model/info`, égal à l'empreinte de la variante (oui / non) | oui (`88b0919750a3c7fa…`) ; `version` 2.0.0, `version_deployee` 2.1.0, `format` onnx |
| Le `patient_ref` journalisé contient-il `IP_0000001` en clair ?                        | non : `f35b47092a7af141` (sha256 salé, 16 caractères)                                |

Appel avec `tbp_tile_type=UV` : `400`, `{"detail":"tbp_tile_type inconnu : 'UV'","error":"covariable invalide"}`, journalisé avec `http_status` 400.

Démarrage hors ligne (`--network none`) jusqu'au premier `/health` à 200 : 1,2 s.

Ligne de journal complète d'un appel avec covariables :

```json
{"ts": "2026-11-17T14:49:39.596Z", "request_id": "bd3dd00f-6cbd-4a04-ae50-5edc00de44d6", "model_version": "2.0.0", "image_digest": null, "patient_ref": "f35b47092a7af141", "probabilite_maligne": 0.062464, "seuil_applique": 0.000682614483230122, "rappel_cible": 0.9, "decision": "a_examiner", "covariables": {"age_tranche": "60-69", "sex": "male", "anatom_site_general": null, "tbp_tile_type": "3D: white"}, "inference_ms": 18.4, "http_status": 200, "input_schema_version": "2.0", "env": "local"}
```

## Mesure 6 — S4 contre S5, sur mon poste

Boucle de latence de S4 réécrite dans `latence.py` (5 appels de chauffe, 50 mesurés sur `/predict`, image de contrôle), lancée depuis le conteneur client (voir mesure 5). Les conteneurs `--cpus 1` sont interrogés sur leur propre port 8000 (réseau partagé), pas sur 8001 / 8002.

| Grandeur                                                        | S4                              | S5                                |
| --------------------------------------------------------------- | ------------------------------- | --------------------------------- |
| Taille de l'image (`docker images`)                             | 1,13 Go                         | 280 Mo                            |
| Taille du fichier de modèle                                     | 44 780 171 octets (`modele.pt`) | 44 781 762 octets (`modele.onnx`) |
| Démarrage jusqu'au premier `/health` à `200` (hors ligne)       | 4,5 s                           | 1,2 s                             |
| Mémoire au repos (`docker stats`, après les 55 appels)          | 314,4 MiB                       | 157,9 MiB                         |
| Latence `/predict` p50 / p95, 50 appels                         | 15,1 ms / 17,1 ms               | 19,1 ms / 22,4 ms                 |
| Latence p50 / p95 sous `--cpus 1`, `ORT_THREADS` par défaut (1) | —                               | 19,0 ms / 21,9 ms                 |
| Latence p50 / p95 sous `--cpus 1`, `ORT_THREADS=8`              | —                               | 96,0 ms / 98,5 ms                 |
| Architecture du poste (amd64 natif ou émulé)                    | amd64 natif (x86_64)            | amd64 natif (x86_64)              |

`docker history dermascan-api:2.1.0` : couche Python + dépendances 168 Mo (contre 1,02 Go pour PyTorch en S4), modèle 44,8 Mo, plus de couche `chown` de 44,8 Mo.

## Question 4.7

Avec 8 threads pour 1 cœur, chaque thread se bat pour le même cœur : ils doivent attendre leur tour et changer de contexte, ce qui entraîne un overhead pour toutes les opérations et donc une latence plus élevée (96,0 ms contre 19,0 ms de p50).
Dans l'annexe B de la séance 3 (ACI, `--cpu 1`, `--workers 2 --threads 4`), Gunicorn traite déjà plusieurs requêtes en parallèle : si chacune lançait 8 fils ONNX, des dizaines de fils se battraient pour un seul cœur. `app.py` fixe donc 1 fil par défaut, ce qui correspond à notre environnement de production (un vCPU sur B1), et au projet, à tout conteneur sous quota CPU (Kubernetes).

## Mesure 11 — S4 contre S5 sur `B1`, mêmes paliers

Même scénario qu'en S4 (`locustfile_s4.py`, `wait_time = between(2, 5)`, poids 10 / 2 / 1, `-r 5`, 3 minutes), lancé avec `lanceur_locust.py` (seul `trust_env` remis à True pour passer par le proxy de l'environnement, même écart qu'en S4). Paliers le 18/11 : 10:32:46 – 10:35:46 et 10:35:46 – 10:38:47 UTC (`deploiement/paliers.txt`). Lignes `Aggregated` de `s5_palier*_stats.csv`, CPU du plan par minute dans `deploiement/metriques_plan.txt`. Un premier essai, interrompu au palier 2, a été jeté.

| Palier | S4 : débit, p50, p95 (mesure 19) | S5 : débit, p50, p95 | S5 : CPU max du plan |
|---|---|---|---|
| 1 (5 utilisateurs) | 1,37 req/s ; 160 ms ; 390 ms | 1,39 req/s ; 110 ms ; 220 ms (0 échec / 249) | 25 % |
| 2 (20 utilisateurs) | 5,02 req/s ; 210 ms ; 2 200 ms | 5,47 req/s ; 120 ms ; 310 ms (0 échec / 978) | 34 % |

`POST /predict` seul : p50 120 ms / p95 220 ms au palier 1, p50 130 ms / p95 360 ms au palier 2. Mémoire du plan 72–77 % (81–82 % en S4). CPU max en S4 : 53 %.

## Question 5.7

Oui, l'engagement de S3 (« jusqu'à 20 utilisateurs, 95 % des prédictions en moins de 1,2 s, moins de 1 % d'échecs ») tient de nouveau avec S5 : à 20 utilisateurs, le p95 passe de 2,2 s en S4 à 310 ms (360 ms pour `/predict`), sans aucun échec, et le CPU du plan ne dépasse pas 34 %.
Tout le gain revient au moteur et à son réglage, puisque je n'ai pas retenu la variante int8 (3.3) : le modèle servi est le même, en float32. La mesure 6 montre d'où il vient : une image 4 fois plus légère (280 Mo contre 1,13 Go), deux fois moins de mémoire au repos (158 contre 314 MiB) et un démarrage plus rapide. En local avec tous les cœurs, ONNX n'est pas plus rapide que PyTorch (19,1 contre 15,1 ms), mais il est réglé sur un seul fil (`ORT_THREADS=1`), ce qui correspond au vCPU unique de B1 ; sous `--cpus 1`, 8 fils coûtent 5 fois plus cher (96 ms).
