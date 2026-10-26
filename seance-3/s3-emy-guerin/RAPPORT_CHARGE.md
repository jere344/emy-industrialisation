# RAPPORT_CHARGE — Séance 3

## Critère de rupture, posé avant toute mesure (2026-10-26 16:03:09)

| Élément du critère | Votre choix | Justification en une ligne |
|---|---|---|
| Seuil de taux d'échec jugé inacceptable | `1`% | 1 échec sur 100 semble raisonnable, surtout si un retry est en place côté client. |
| Seuil de p95 jugé inacceptable | `3` fois le p95 du palier 1 | 3x est un palier qui commence à être visible par les utilisateurs, sans pour autant empêcher l'utilisation du produit. |
| Le point de rupture est atteint quand | l'un des deux critères | Pour le médecin si le service devient trop lent le résultat final est le même qu'une erreur, le service est inutilisable. |

## Paliers décidés avant mesure

| Palier | `--users` | `--spawn-rate` | Fichiers produits |
|---|---|---|---|
| 1 | 5 | 1 | `palier1_stats.csv`, `palier1.html` |
| 2 | 20 | 2 | `palier2_*` |
| 3 | 60 | 5 | `palier3_*` |
| 4 | 150 | 10 | `palier4_*` |

## Question 5.1

**Question 5.1** — Justifiez vos trois poids en une phrase chacun, à partir de l'usage réel décrit dans le contexte métier : des dermatologues qui soumettent une lésion depuis leur poste de consultation. Un poids identique sur les trois tâches produit une mesure qui ne représente aucun usage réel.

> Les /health et /model/info ne sont basiquement jamais utilisés par les logiciels des médecins. Leur utilisation consiste à faire des prédictions avec le /predict. Il faut s'attendre à quelques requêtes régulières vers /health de la part d'Azure et /model/info périodiquement par les utilisateurs si leurs logiciels veulent afficher ces données.

## Mesure 13 — débit, percentiles et taux d'échec sur les quatre paliers

Valeurs lues sur la ligne `Aggregated` de chaque `palier*_stats.csv` (3 minutes par palier, stabilisation comprise). Exécution depuis le poste de travail, de 16:03 à 16:16 (heure locale).

| Palier | Utilisateurs | Débit (req/s) | p50 (ms) | p95 (ms) | p99 (ms) | Taux d'échec (%) | Échecs les plus fréquents |
|---|---|---|---|---|---|---|---|
| 1 | 5 | 1.36 | 85 | 520 | 850 | 0 (0 / 243) | aucun |
| 2 | 20 | 5.24 | 97 | 1200 | 2500 | 0 (0 / 940) | aucun |
| 3 | 60 | 11.90 | 330 | 8200 | 12000 | 0 (0 / 2133) | aucun |
| 4 | 150 | 17.34 | 4700 | 7600 | 8200 | 0 (0 / 3108) | aucun |

## Mesure 14 — ligne de base réseau

| Ligne de base | Votre valeur |
|---|---|
| Temps d'établissement de connexion, médiane sur 20 mesures | `22.3 ms` (min 18.6 ms, max 72.2 ms) |
| Part que cela représente dans votre p50 du palier 1 | environ 26 % (22.3 / 85) |

## Mesure 15 — point de rupture constaté

Critère posé avant mesure : taux d'échec supérieur à 1 %, **ou** p95 supérieur à 3 fois le p95 du palier 1 (soit 3 × 520 = 1560 ms).

| Conclusion | Votre réponse |
|---|---|
| Palier où le critère est franchi pour la première fois | palier 3 (60 utilisateurs) : p95 = 8200 ms, supérieur à 1560 ms. Le taux d'échec reste à 0 % sur tous les paliers : c'est le critère de p95 qui est franchi. |
| Nombre d'utilisateurs simultanés supporté, borné entre deux paliers | entre 20 (critère respecté, p95 = 1200 ms) et 60 (critère franchi) utilisateurs |
| Débit maximal observé avant dégradation, en requêtes par seconde | 5.24 req/s (palier 2) |
| Ressource qui sature en premier, d'après les métriques de la partie 4.3 | Le processeur du plan : `CpuPercentage` atteint 97 à 100 % pendant le palier 4 (minutes 15:13 à 15:16 UTC), alors que `MemoryPercentage` reste stable entre 69 et 76 % sur toute la période. |
| Ce que valait `Http5xx` au palier le plus chargé | `0` (aucune réponse 5xx sur la fenêtre des paliers, 5795 requêtes comptées par la plateforme) |

Métriques du plan (`az monitor metrics list --resource "$PLAN_ID" --metric CpuPercentage MemoryPercentage --interval PT1M`), minute par minute, heure UTC (heure locale moins 1 h) :

| Palier | Fenêtre (UTC) | CpuPercentage par minute | MemoryPercentage |
|---|---|---|---|
| 1 | 15:03 – 15:06 | 44, 22, 86, 29 (le pic à 86 % pendant un palier à 5 utilisateurs n'est pas expliqué) | 69 – 75 |
| 2 | 15:06 – 15:09 | 29, 27, 75 | 70 – 71 |
| 3 | 15:09 – 15:12 | 44, 41, 68, 84 | 71 – 72 |
| 4 | 15:13 – 15:16 | 97, 65, 99, 100 | 72 – 73 |

## Question 5.2

**Question 5.2** — Sur votre palier le plus chargé, comparez p50 et p99. Un écart faible et un écart important ne décrivent pas le même problème. Dites lequel des deux vous observez, et ce qu'il implique pour un praticien qui soumet une lésion en consultation : dans quelle proportion des cas subit-il le p99 ? Quatre lignes.

> Sur notre palier 4 l'écart entre p50 et p99 est plutôt faible, ~ 2x, ce qui indique un service généralement saturé. Dans le palier 1 l'écart est très élevé, autour de 10x ce qui indique un système instable même si généralement rapide.
> La cause de l'instabilité du palier 4 est probablement un service saturé, le service doit passer d'une réponse à l'autre trop rapidement et accumule une charge de travail qui ne s'équilibre que quand les requêtes ralentissent, conséquence du ralentissement du système. La cause des pics d'instabilité du palier 1 est probablement 2 requêtes simultanées servies par un seul worker Gunicorn, une file d'attente se crée entre les requêtes au détriment du deuxième arrivé.
>
> Les cas p99 et plus se produisent dans 1% des cas, 1 consultation sur 100.

## Question 5.3

**Question 5.3** — À partir de vos seules mesures, écrivez pour DermaScan un engagement de service en une phrase, de la forme : « jusqu'à N utilisateurs simultanés, 95 % des prédictions sont rendues en moins de X ms, avec moins de Y % d'échecs. » Les trois valeurs sont les vôtres et doivent être adossées à un palier mesuré. Un engagement pris sur un palier non mesuré ne vaut rien.

> Avec jusqu'à 20 utilisateurs simultanés, 95 % des prédictions sont rendues en moins de 1,2 secondes pour moins de 1 % d'échec.
> Justification : palier 2 : 20 utilisateurs, p95 = 1200 ms et 0 erreur. < 1 % d'erreurs parce que l'on ne peut jamais garantir 0 erreur.

## Question 5.4

**Question 5.4** — DermaScan annonce l'ouverture de deux centres supplémentaires, soit une charge doublée. Sans rien mesurer de plus, quelles sont vos **deux** options pour tenir l'engagement que vous venez d'écrire ? Nommez-les avec les termes techniques exacts, et dites laquelle vous testeriez en premier et pourquoi.

> Les deux options sont un scaling vertical (machine plus puissante, plus de CPU, plus de RAM) ou un scaling horizontal (plusieurs machines, load balancing).
> Je testerai en priorité un scaling vertical avec plus de workers Gunicorn, l'architecture est plus simple, moins onéreuse, et largement envisageable au vu de notre instance et utilisation actuelle.

## Question 5.5

**Question 5.5** — Votre API charge le modèle **une fois au démarrage du processus**, décision prise en séance 2. Qu'auriez-vous mesuré aujourd'hui si elle le rechargeait à chaque requête ? Dites sur laquelle des colonnes de la mesure 13 l'effet serait le plus visible, et pourquoi ce n'est pas le débit **aux paliers non saturés**.

> Si le modèle était rechargé à chaque requête, on aurait mesuré un coût fixe ajouté à chaque requête, donc des latences plus élevées dès le palier 1, et une saturation du CPU bien plus tôt. L'effet serait le plus visible sur le p50, puisque toutes les requêtes sont touchées et que c'est le chiffre qui représente le mieux l'ensemble des requêtes. Le débit ne bougerait pas (sauf ralentissement aux paliers saturés, au fur et à mesure que les utilisateurs ne peuvent plus utiliser le service) : il est fixé par les utilisateurs. Tant que le serveur suit, il sert toutes les requêtes.
