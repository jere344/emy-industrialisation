# MESURES - Séance 6

## Mesure 1 - `python preparer.py`

| Grandeur | Valeur |
|---|---|
| Lignes de test et positifs en test, graine 42 | 100 054 lignes, 130 positifs |
| Lignes de test et positifs en test, graine 7 | 101 995 lignes, 108 positifs |
| Les 12 premiers caractères de l'empreinte de `donnees/manifeste.json` | `977af58e9a22` |

Sortie :

```
graine 42 : 301,005 / 100,054 lignes, 130 positifs en test, intersection vide
graine 7 : 299,064 / 101,995 lignes, 108 positifs en test, intersection vide
manifeste : donnees/manifeste.json  sha256 977af58e9a22
```

## Question 1.1

Le test fait un découpage par partient. Hors les patient avec des lésions malignes ont plusieurs photos, il est probable que les 130/108 lignes de positifs entre la gaine 42 et 7 ne correspondent quelques patient de différences, ou même à un même nombre de patient mais avec un nombre différent de photos correspond à leurs lésions malignes. La variation est donc un artefact de notre faible échantillon, exacerbé par notre manière de découper les graine par patient au lieu de ligne.

## Mesure 2 - `python entrainer_suivi.py --approche reference --graine 42`

Blancs remplis : `SUIVI = "sqlite:///suivi/mlflow.db"`, `artifact_location=str(Path("suivi/artefacts").resolve())`, `"sha256_manifeste": meta["sha256_manifeste"]`.

```
reference-g42  PR-AUC 0.0507  precision@90% 0.0041  seuil 0.2839  28 s  run 0f08c186610d4e109b889ba2c9385a4d
```

| Grandeur | Valeur |
|---|---|
| PR-AUC | 0,0507 |
| Précision au rappel cible (90 %) | 0,0041 |
| Seuil | 0,2839 |
| Durée | 28 s |
| Identifiant du run | `0f08c186610d4e109b889ba2c9385a4d` |

## Question 1.2

Le seuil obtenu maintenant est différent de celui de S2, 0.2839 au lieu de 0.333
Cela ne prouve rien sur la reproductibilité de notre chaine, les données d'entrées sont différentes (0.20 contre 0.25% des données dans nos tests)

## Mesure 3 - le suivi ouvert sur `poste/`, avant `importer_suivi.py`

| Observation | Valeur |
|---|---|
| Les métriques et paramètres du run sont-ils lisibles ? | oui (5 métriques, 7 paramètres, tags) - `captures/mesure3_overview.png` |
| Les artefacts (`model/modele.joblib`) sont-ils lisibles ? | non : « No Artifacts Recorded » - `captures/mesure3_artifacts_avant_import.png` |
| Le chemin indiqué pour les artefacts, dans les détails du run | `/home/guerin/Desktop/cours/indus/s6-emy-guerin/session/suivi/artefacts/0f08c186610d4e109b889ba2c9385a4d/artifacts` (lu dans `runs.artifact_uri` de `suivi/mlflow.db` : pointe vers `session/`, qui n'existe plus) |

Après `python importer_suivi.py` : artefacts lisibles (`model/modele.joblib`, 9,95 Ko, et `modele_meta.json`), chemin affiché `/home/guerin/Desktop/cours/indus/s6-emy-guerin/poste/suivi/artefacts/0f08c186610d4e109b889ba2c9385a4d/artifacts/model/...` - `captures/mesure3_artifacts_apres_import.png`. Dans `suivi/mlflow.db`, `experiments.artifact_location` et `runs.artifact_uri` pointent désormais vers `poste/suivi/artefacts`.

Sortie de `python importer_suivi.py` :

```
experiments.artifact_location : 1 ligne(s) /home/guerin/Desktop/cours/indus/s6-emy-guerin/session/suivi/artefacts -> /home/guerin/Desktop/cours/indus/s6-emy-guerin/poste/suivi/artefacts
runs.artifact_uri : 1 ligne(s) /home/guerin/Desktop/cours/indus/s6-emy-guerin/session/suivi/artefacts -> /home/guerin/Desktop/cours/indus/s6-emy-guerin/poste/suivi/artefacts
model_versions.source : 0 ligne(s) /home/guerin/Desktop/cours/indus/s6-emy-guerin/session/suivi/artefacts -> /home/guerin/Desktop/cours/indus/s6-emy-guerin/poste/suivi/artefacts
model_versions.storage_location : 0 ligne(s) /home/guerin/Desktop/cours/indus/s6-emy-guerin/session/suivi/artefacts -> /home/guerin/Desktop/cours/indus/s6-emy-guerin/poste/suivi/artefacts
```

## Question 1.3

(a) Les métriques ont survécu à l'export car elles sont stockées en db, alors que les artefacts sont concervé dans des fichiers dont le chemin n'existe plus après l'export.
(b) `importer_suivi.py` remplace, dans la base, l'ancien préfixe absolu (`.../session/suivi/artefacts`) par celui du poste (`.../poste/suivi/artefacts`) dans les colonnes `experiments.artifact_location`, `runs.artifact_uri` et `model_versions.source` / `storage_location`.
(c) Le même problème se poserait entre deux postes du groupe : les fichiers sont copiés mais la db garde les chemin absolu du poste précédent (`/home/<utilisateur>/...`) ; il faudrait relancer l'import sur chaque poste.

## Mesure 4 - quatre runs, depuis `poste/` (vue Compare : `captures/mesure4_comparaison.png`)

```
reference-g7  PR-AUC 0.0653  precision@90% 0.0061  seuil 0.4947  20 s  run ffab1ab299a0484dbee254fe1dfdbd00
variante-g42  PR-AUC 0.0834  precision@90% 0.0051  seuil 0.0615  3 s  run 2f107a1ec4914d98b8d3256faa4e0677
variante-g7  PR-AUC 0.0469  precision@90% 0.0052  seuil 0.1810  2 s  run b43d2984793b4f8dbb47a155df2bb686
```

| Run | PR-AUC | Précision au rappel cible | Durée d'entraînement |
|---|---|---|---|
| `reference-g42` | 0,0507 | 0,00408 | 28,5 s |
| `reference-g7` | 0,0653 | 0,00611 | 19,7 s |
| `variante-g42` | 0,0834 | 0,00507 | 2,5 s |
| `variante-g7` | 0,0469 | 0,00518 | 1,8 s |

## Mesure 5 - écarts (métrique d'arbitrage : précision au rappel cible ; PR-AUC en départage)

| Grandeur | Précision au rappel cible | PR-AUC |
|---|---|---|
| Écart variante - référence, graine 42 | +0,00098 (+24,1 %) | +0,0327 (+64,5 %) |
| Écart variante - référence, graine 7 | -0,00093 (-15,2 %) | -0,0184 (-28,2 %) |
| Variation de la référence entre ses deux graines (g7 - g42) | +0,00203 (+49,7 %) | +0,0146 (+28,9 %) |
| Variation de la variante entre ses deux graines (g7 - g42) | +0,00012 (+2,3 %) | -0,0365 (-43,8 %) |

## Question 1.4

L'écart entre approches ne dépasse pas la variation d'une même approche. Mais prenant en compte tout les critère, la variance me semble meilleure. Ceci contredit nos attentes et nos règles précédente qui ommettent le temps d'entrainement et la stabilité dans les résutats du modèle.
Non allons donc devoir faire quelque chose d'interdit, modifier nos critères de choix après observation de nos métriques, en ajoutant le 3ème critère stabilité et le 4ème temps d'entrainement.

## Mesure 6 - registre et chaîne de traçabilité

Blancs remplis dans `promouvoir.py` : `ALIAS_SERVI = "production"` (alias lu par `verifier_chaine.py`), `ALIAS_REPLI = "repli"`. Run retenu pour l'approche variante : `variante-g42` (même graine que la version de repli `reference-g42`).

```
$ python promouvoir.py --run 0f08c186610d4e109b889ba2c9385a4d --validateur "Emy GUERIN"
dermascan-tabulaire v1 -> production (run reference-g42, valide par Emy GUERIN) ; repli : aucune
$ python promouvoir.py --run 2f107a1ec4914d98b8d3256faa4e0677 --validateur "Emy GUERIN"
dermascan-tabulaire v2 -> production (run variante-g42, valide par Emy GUERIN) ; repli : 1
$ python verifier_chaine.py model/variante-g42/modele.joblib
registre : dermascan-tabulaire v2, valide par Emy GUERIN, repli 1
OK  fichier servi = version promue     ab9c358230d9a9dd
run : variante-g42  graine 42  PR-AUC 0.0834
OK  artefact du run = fichier servi    ab9c358230d9a9dd
OK  manifeste du run = manifeste local 977af58e9a22755b
OK  donnees du manifeste = donnees locales 536e8208cfb3502b
commit du code qui a produit les donnees : hors-git
```

| Relevé | Valeur |
|---|---|
| Version promue | `dermascan-tabulaire` v2 (run `variante-g42`), validée par Emy GUERIN |
| Version de repli | v1 (run `reference-g42`) |
| Maillon 1 - fichier servi = version promue | OK (`ab9c358230d9a9dd`) |
| Maillon 2 - artefact du run = fichier servi | OK (`ab9c358230d9a9dd`) |
| Maillon 3 - manifeste du run = manifeste local | OK (`977af58e9a22755b`) |
| Maillon 4 - données du manifeste = données locales | OK (`536e8208cfb3502b`) |

Vérification sur l'autre fichier (`reference-g42`, comme si le mauvais fichier avait été copié dans l'image) :

```
$ python verifier_chaine.py model/reference-g42/modele.joblib ; echo "code de sortie : $?"
registre : dermascan-tabulaire v2, valide par Emy GUERIN, repli 1
KO  fichier servi = version promue     4c612fc5c585ef7c  (attendu ab9c358230d9a9dd)
code de sortie : 1
```

## Question 1.5

La vérification du hash « fichier servi = version promue » échoue, et le code de sortie est 1 (différent de 0) qui indique une erreur. Ce script peut servir de test automatique au projet : une simple exécution après la construction de l'image, sur le fichier qui est dedans, avant de la pousser, et une vérification du code de sortie permettrait de bloquer le déploiement d'un mauvais fichier de modèle ou de mauvaises données.
