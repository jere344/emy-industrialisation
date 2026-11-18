# SURVEILLANCE — Séance 5

## Mesure 7 — la référence (`reference_covariables.json`, jeu d'entraînement du manifeste S4)

| Covariable | Modalités et proportions | Taux d'absence |
|---|---|---|
| `tbp_tile_type` | `3D: white` 52,90 % ; `3D: XP` 47,10 % | 0 % |
| `age_tranche` (les trois plus fréquentes) | 60-69 : 34,45 % ; 50-59 : 23,44 % ; 70-79 : 17,31 % (7 tranches au total) | 0,71 % |
| `anatom_site_general` (les deux plus fréquentes) | posterior torso 30,75 % ; lower extremity 26,09 % (5 modalités) | 1,75 % |
| `sex` | male 70,71 % ; female 29,29 % | 1,58 % |
| Nombre de vignettes de la référence | 4 236 | — |

## Question 5.1

La référence ne prend que le jeu d'entraînement du manifeste (4 236 vignettes, 52,90 % de `3D: white`), alors que le manifeste de la mesure 20 contient aussi la validation (5 294 vignettes, 55,23 %).

Notre modèle est entraîné sur un jeu restreint, le jeu d'entraînement, et non pas sur l'archive entière. Il est normal que la référence corresponde au jeu réel utilisé pour créer notre modèle, même si l'on a des données supplémentaires : le modèle n'a pas été entraîné sur ces données supplémentaires.

## Question 5.2

| Modalité | p (référence) | q (`train-metadata.csv` complet) | q − p | ln(q/p) | (q − p)·ln(q/p) |
|---|---|---|---|---|---|
| `3D: white` | 0,5290 | 0,2871 | −0,2419 | −0,6112 | 0,1479 |
| `3D: XP` | 0,4710 | 0,7129 | +0,2419 | +0,4146 | 0,1003 |
| **PSI** | | | | | **0,2482** |

Le PSI est encore sous la limite, de très peu (0,2482 < 0,25). L'alarme ne sonne pas, alors que ce flux est une vraie dérive (71 % de XP contre 47 % à l'entraînement). Soit notre seuil d'alarme est trop haut pour détecter ce cas, et il aurait fallu le choisir à partir d'un scénario de dérive connu plutôt que de la convention, soit notre processus d'entraînement n'est pas représentatif et notre modèle ne répond pas aux besoins réels.

## Mesure 8 — la dérive provoquée, en local (levier `eclairage`, fenêtre 200, seuil 0,25)

`rejouer_flux.py` : conforme 400 appels, tous en 200, `a_examiner` 81 (20,2 %) ; dérive (éclairage) 400 appels, tous en 200, `a_examiner` 73 (18,2 %). Journal : `journal_local.jsonl` (800 appels), fenêtres : `sorties/psi_fenetres_local_eclairage.csv`.

| Covariable | PSI max en flux conforme | PSI de la dernière fenêtre | Délai d'alerte (inférences après le début de la dérive) |
|---|---|---|---|
| `tbp_tile_type` | 0,0052 | 4,9333 | 82 |
| `age_tranche` | 0,1146 | 0,1224 | aucune alerte |
| `anatom_site_general` | 0,0585 | 0,0366 | aucune alerte |
| `sex` | 0,0294 | 0,0012 | aucune alerte |
| Taux de `a_examiner` : flux conforme / flux dérivé | 20,25 % / 18,25 % | | |

## Mesure 9 — second levier (`age`, conteneur redémarré, journal vierge)

`rejouer_flux.py` : conforme 400 appels en 200, `a_examiner` 81 (20,2 %) ; dérive (âge ≥ 70) 400 appels en 200, `a_examiner` 102 (25,5 %). Journal : `journal_local_age.jsonl`, fenêtres : `sorties/psi_fenetres_local_age.csv`.

| Relevé | Ma valeur |
|---|---|
| Levier | `age` (`age_approx >= 70`) |
| Covariable qui alerte, et délai | `age_tranche`, 52 appels après le début de la dérive (PSI de la dernière fenêtre 7,11) |
| Autre covariable qui bouge sans alerter, et son PSI | `sex` : 0,1108 sur la dernière fenêtre (0,0294 au maximum en flux conforme), au-dessus du seuil de surveillance, sous l'alerte |
| Taux de `a_examiner` : flux conforme / flux dérivé | 20,25 % / 25,50 % |

## Question 5.3

Taux de `a_examiner` conforme / dérivé : éclairage 20,25 % / 18,25 % (−2 points, soit 4 lésions sur une fenêtre de 200) ; âge 20,25 % / 25,50 % (+5 points).

Pour l'éclairage, un tableau de bord qui ne suivrait que la sortie du modèle n'aurait pas vu la dérive, alors que la surveillance des entrées oui (PSI 4,93, alerte après 82 appels).
Pour l'âge, les deux auraient vu la dérive.
On veut les deux car ils surveillent des choses différentes, et nos métriques peuvent chacune manquer quelque chose.

## Question 5.4

La covariable `age_tranche` a dépassé le seuil de surveillance pendant le flux conforme (maximum 0,1146, 6 fenêtres sur 201 au-dessus de 0,1).
Après mesure, l'archive a une distribution d'âge quasiment identique à notre référence d'entraînement (PSI 0,0048). C'est du bruit, dû à notre fenêtre relativement courte (200 appels) pour 7 tranches d'âge : environ 30 appels par tranche en moyenne, quelques-uns pour les tranches rares. En simulation de bruit pur, une fenêtre de 200 dépasse 0,1 dans 2,4 % des cas ; l'éclairage, à 2 modalités, reste à 0,005.

## Question 5.5

Avec une fenêtre deux fois plus petite (100), l'alerte arriverait plus vite après une dérive réelle, mais le nombre de fausses alertes augmenterait (bruit de l'âge jusqu'à 0,159 au lieu de 0,085). Avec une fenêtre plus grande, c'est l'inverse : moins de fausses alertes, mais il faut attendre plus longtemps avant d'avoir une alerte.

Délai théorique pour l'éclairage : quand une fraction f de la fenêtre est en `3D: XP` pur et le reste conforme à la référence (47,10 % de XP), la part de XP vaut 0,4710 + f × 0,5290. Le PSI atteint 0,25 pour une part de XP de 71,4 %, soit f = 0,459 : environ 46 % de la fenêtre, 92 appels sur 200 (46 sur 100). Mesuré en local : 82 appels, un peu plus tôt, car la partie conforme de la fenêtre n'est pas exactement à 47,10 % de XP.

## Mesure 10 — la surveillance en ligne (Azure, `dermascan-api-s5-EG08`, image `2.1.0`, digest `sha256:661dc2e7…`)

Rejeu (`deploiement/rejeu_azure.txt`) : conforme 600 appels à 1/s de 16:04:13 à 16:14:18 UTC, `a_examiner` 21,0 % ; dérive (éclairage) 600 appels de 16:14:18 à 16:24:23 UTC, `a_examiner` 17,3 % ; tous en 200. Journal : `journal_azure.jsonl`, fenêtres : `sorties/psi_fenetres_azure_eclairage.csv`.

| Relevé | Ma valeur |
|---|---|
| Délai entre un appel et son apparition dans Log Analytics | 2 min 44 s (appel de test à 16:03:56, `ingestion_time()` 16:06:40) ; fin du rejeu à 16:24:23, 1 200 lignes présentes à 16:26:46 |
| Nombre de lignes exportées / nombre d'appels envoyés | 1 201 / 1 201 (1 200 du rejeu + l'appel de test) |
| PSI de l'éclairage par fenêtre de 5 min, phase conforme (min – max) | 0,000004 – 0,029 (fenêtre de 16:00, partielle : 44 appels). La fenêtre de 16:10 (296 appels, dont environ 40 dérivés à partir de 16:14:18) reste à 0,007 |
| Première fenêtre de 5 min au-dessus du seuil d'alerte, et heure de début de la dérive | fenêtre de 16:15 UTC (PSI 4,93, 300 appels) ; dérive commencée à 16:14:18 UTC |
| Délai d'alerte de `derive.py` sur le journal Azure (inférences) | 97 appels après le début de la dérive (PSI max en flux conforme 0,0303 ; 82 en local) |
| Capture du tableau de bord (requêtes 2, 3, 4) dans `captures/` | `captures/tableau_de_bord.png` (tableau de bord partagé `dermascan-s5`, groupe `dashboards`, France Central, plage 17/11 16:00–16:35 UTC) ; `captures/requete2_composition_eclairage.png`. Sur la tuile de la requête 3, la colonne `appels` (0–300) écrase l'axe : le saut du PSI à 4,93 y est invisible ; il aurait fallu projeter seulement `psi` et `seuil_alerte` |

Requête 3 exécutée en CLI (`az monitor log-analytics query`) : 16:00 → 0,0293 (44 appels) ; 16:05 → 0,000004 (300) ; 16:10 → 0,0072 (296) ; 16:15 → 4,9333 (300) ; 16:20 → 4,9333 (261).
Probabilité de l'image de contrôle servie sur Azure : 0,062463 (0,062464 en local). `/model/info` : `captures/model_info_azure.json`.

## Question 5.6

Entre le premier patient « dérivé » et le moment où un humain voit l'alerte, il y a plusieurs délais qui s'additionnent :
1. remplir la fenêtre : il faut qu'environ 46 % de la fenêtre soit dérivée avant que le PSI franchisse le seuil (97 appels sur Azure, 82 en local) ;
2. la fenêtre de 5 minutes du tableau de bord : une tranche n'est complète qu'à sa fin ; la dérive a commencé à 16:14:18, la fenêtre de 16:10 est restée à 0,007 (trop peu d'appels dérivés), la première en alerte est celle de 16:15, complète à 16:20 ;
3. l'ingestion dans Log Analytics : environ 2 min 44 s entre l'appel et son apparition ;
4. le rafraîchissement du tableau de bord, et surtout qu'un humain le regarde.

Celui que l'on pourrait réduire sans rien changer à notre seuil, c'est le dernier : une alerte automatique Azure Monitor (la requête 3 évaluée toutes les 5 minutes, annexe C) préviendrait quelqu'un sans attendre qu'il ouvre le tableau de bord. On pourrait aussi réduire la tranche de 5 minutes, mais avec moins d'appels par tranche le PSI serait plus bruité.

## Mesure 12 — fin de séance

| Contrôle | Mon observation |
|---|---|
| Nombre et types de ressources du groupe avant destruction | 3 : `plan-dermascan-s5-EG08` (plan App Service), `dermascan-api-s5-EG08` (Web App), `law-dermascan-s5-EG08` (espace Log Analytics) |
| `az group exists` sur le groupe de séance | `false` (10:43:40 UTC, environ 1 min après le lancement de la suppression) |
| Le groupe du registre est-il toujours là ? | oui, `az group exists` sur `rg-dermascan-registre-EG08` : `true` ; plus aucune attribution de rôle sur le registre |
| Tags du dépôt `dermascan-api` | `1.0.0`, `1.0.1`, `2.0.0`, `2.1.0` |
| Le tableau de bord partagé survit-il à la destruction du groupe ? Ses graphiques affichent-ils encore quelque chose ? | oui, il survit : la ressource `dermascan-s5` (`Microsoft.Portal/dashboards`, groupe `dashboards`, France Central) est toujours listée après destruction (`captures/tableau_de_bord_apres_destruction.png`). Rouvert après destruction (`captures/tableau_de_bord_apres_destruction_tuiles.png`) : les trois tuiles affichent encore des courbes, y compris le test de charge du 18/11, alors que l'espace a été supprimé à 10:42:34 UTC. Même après un rafraîchissement manuel des tuiles, les courbes restent : sans doute un délai côté Azure (cache des résultats, ou suppression pas encore propagée au service de requêtes). Aucune nouvelle donnée ne peut plus y arriver |
| Crédit restant, et écart avec la séance 4 | 83 USD restants sur 90 (7 USD consommés depuis le début du crédit) ; Cost analysis le 18/11 : 6,51 € consommés depuis le début de l'année (prévision 12,89 €), dont 6,29 € de Container Registry, 0,24 € d'App Service, 0,00 € de Log Analytics (`captures/cout_azure_2026-11-18.png`). Pas de relevé de crédit en S4 pour comparer |

Attribution `AcrPull` supprimée le 18/11 à 10:42:02 UTC, espace Log Analytics supprimé avec `--force` à 10:42:34, suppression du groupe lancée à 10:42:36. Les ressources ont tourné du 17/11 16:01 au 18/11 10:42 UTC (séance interrompue la veille au soir). En local (Linux, Docker Engine, pas de Docker Desktop à quitter) : conteneurs de la séance supprimés, alias de registre et image client retirés, images `dermascan-api:1.0.0`, `2.0.0`, `2.1.0` gardées pour le projet.

## Question 6.1

Le tableau de bord ne stocke aucune donnée : chaque tuile est une requête KQL pointée vers l'espace `law-dermascan-s5-EG08`. Une fois l'espace détruit avec le groupe de séance, le tableau de bord existe toujours (il est dans le groupe `dashboards`). Juste après la destruction, ses tuiles affichent encore les derniers résultats gardés en cache, ce qui peut tromper : elles ne reçoivent plus aucune donnée, et à leur prochain rafraîchissement elles interrogeront un espace qui n'existe plus.
Pour que la surveillance survive aux séances, il faudrait garder l'espace Log Analytics dans un groupe durable, comme celui du registre, et pas dans le groupe jetable de la séance. La Web App et le plan peuvent être recréés à chaque séance, en branchant leur paramètre de diagnostic sur cet espace permanent.
