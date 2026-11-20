# GOUVERNANCE - Séance 6

## 2.1 - Classer selon l'AI Act

_(en attente du sujet du projet `ProjetFilRouge_MLOps_Sujet.md`)_

## 2.2 - Ce que vous n'avez pas le droit de journaliser

Ligne de journal de S3 (`JOURNALISATION_INFERENCES.md`, partie 6.2) :

```json
{"ts":"2026-10-26T15:41:08.123Z","request_id":"3f2b8c1e-5a47-4d0e-9c1a-7e6d2b9f4a10","model_version":"1.0.0","image_digest":"sha256:0df1b9e549b1d514d6f9943fd4429e32b30b3b10fc3948b95433d5e94af8a728","patient_ref":"a1b2c3d4e5f60718","probabilite_maligne":0.8663,"seuil_applique":0.3333,"decision":"a_examiner","inference_ms":7,"http_status":200,"input_schema_version":"1","covariables":{"age_tranche":"70-79","anatom_site_general":"posterior torso","clin_size_long_diam_mm":3.9,"tbp_lv_L":49}}
```

| Champ | Conservé ? | Transformation | Durée de conservation | Besoin nommé qui la justifie |
|---|---|---|---|---|
| `ts` | oui | brut, UTC ISO 8601 à la milliseconde | 12 mois | sans ordre temporel, aucune reconstitution d'incident n'est possible |
| `request_id` | oui | brut, UUID v4 généré si absent | 12 mois | seul moyen de relier une ligne de journal à une réclamation |
| `model_version` | oui | brut | 12 mois | répond à « quel modèle a produit cette réponse », question n° 1 d'un audit |
| `image_digest` | oui | le digest, jamais le tag | 12 mois | désigne l'image exacte qui a servi (un tag peut être déplacé) |
| `patient_ref` | oui, pseudonymisé | SHA-256(sel + `patient_id`), 16 premiers caractères hexadécimaux | 12 mois | relier les lésions d'un même patient sans conserver son identité (réclamation, audit annuel) |
| `probabilite_maligne` | oui | 4 décimales | 12 mois | nécessaire à l'audit et à la dérive ; l'arrondi limite la précision exploitable |
| `decision` | oui | brut | 12 mois | c'est ce qui a été rendu au praticien |
| `covariables` | oui, sous-ensemble minimal | âge en tranche de 10 ans, site anatomique brut, taille arrondie à 1 décimale, `tbp_lv_L` arrondie à l'entier ; sexe exclu | 1 semaine | détection de dérive sur une fenêtre glissante de 200 inférences ; pas moins d'une semaine pour éviter qu'un incident n'entraîne la réinitialisation de notre fenêtre |

## Question 2.2

Une vignette de peau ne peut pas être pseudonymisée par hachage : après hachage elle ne peut plus être analysée à nouveau. Le hash peut aller dans le journal mais ne sert qu’à vérifier, si on retrouve l’image originale, que c’est la même.
La vignette étant une information pouvant identifier un patient (les lésions, grants de beauté etc... sont souvent uniques), nous ne devons pas journaliser l’image elle-même.

## Question 2.3

_(en attente du sujet du projet)_

## 2.3 - Une ligne de journal mène au commit

| Maillon | Identifiant qui mène au suivant | Où il est écrit | Présent aujourd'hui ? |
|---|---|---|---|
| Ligne de journal | `image_digest` et `model_version` | le journal JSONL (S3) | oui |
| Image | le fichier `modele.joblib` qu'elle contient, et son empreinte | l'image Docker | oui, mais rien ne relie son empreinte au registre (`model_version` = `1.0.0`) |
| Version de modèle au registre | `run_id`, et le tag `sha256_modele` | registre MLflow (`suivi/mlflow.db`) | oui (`dermascan-tabulaire` v2) |
| Run | tag `sha256_manifeste` | `suivi/mlflow.db` | oui |
| Manifeste de données | `sha256` des données et `commit` | `donnees/manifeste.json` | oui, mais `commit` = `hors-git` |
| Commit du code | - | dépôt git | non |

## Question 2.4

L'historisation de la partie applicative est rompu : nous avons historisé tout ce qui est relatif au modèle, mais rien de ce qui le fait tourner et le produit. Pour ça il faut créer un repot git pour notre projet et produire un commit pour chaque mise à niveau de notre système afin de pouvoir répliquer à l'identique notre environnement complet ultérieurement.

## Question 2.5

Afin d'avoir une historisation complète nous pouvons journaliser le sha256 du modèle. Avec ça nous aurons une clef commune entre toutes les versions à partir d'une ligne de journalisation.