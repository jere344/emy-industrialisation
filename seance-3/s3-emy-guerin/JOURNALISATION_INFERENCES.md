# JOURNALISATION_INFERENCES — Séance 3

## 6.1 — Grille : que journaliser, que ne jamais journaliser

| Donnée | Journaliser ? | Forme | Justification |
|---|---|---|---|
| Horodatage de la requête, en UTC | Toujours | Brut | Sans ordre temporel, aucune reconstitution d'incident n'est possible |
| Identifiant de corrélation de la requête | Toujours | Brut, généré si absent | Seul moyen de relier une ligne de log à une réclamation client |
| Version du modèle et digest de l'image | Toujours | Brut | Répond à « quel modèle a produit cette réponse », question n° 1 d'un audit |
| Identifiant du patient (`patient_id`) | Oui, pseudonymisé | `patient_ref` : SHA-256(sel + identifiant), 16 premiers caractères hexadécimaux | Relier les lésions d'un même patient sans conserver son identité |
| Identifiant de la lésion (`isic_id`) | Non | Rien | L'identifiant de corrélation suffit à retrouver une requête ; l'identifiant de lésion n'apporte rien de plus |
| Âge et sexe (`age_approx`, `sex`) | Âge oui, sexe non | Âge en tranche de 10 ans | La tranche d'âge suffit à la détection de dérive ; le sexe croisé à l'âge et au site rapproche d'une réidentification |
| Site anatomique (`anatom_site_general`) | Oui | Brut (catégorie) | Catégorie large, peu identifiante seule, utile à la détection de dérive |
| Valeurs brutes des variables morphologiques (`tbp_lv_*`) | Non, sauf `tbp_lv_L` | `tbp_lv_L` arrondie à l'entier | Les valeurs brutes décrivent la lésion d'un patient ; un seul indicateur grossier suffit à la dérive |
| Probabilité maligne prédite | Toujours | 4 décimales | Nécessaire à l'audit et à la dérive ; l'arrondi limite la précision exploitable |
| **Seuil appliqué** et rappel visé | Toujours | Brut | Sans le seuil, la décision ne peut pas être justifiée a posteriori |
| Décision rendue (`a_examiner` / `surveillance`) | Toujours | Brut | C'est ce qui a été rendu au praticien |
| Latence d'inférence | Toujours | En millisecondes | Surveillance des performances |
| Code HTTP et message d'erreur éventuel | Toujours | Message sans le corps de la requête | Diagnostic d'incident ; le corps de la requête contiendrait des données de santé |
| Adresse IP source de l'appel | Jamais | Rien | Donnée personnelle sans utilité ici ; la plateforme en conserve déjà une copie |
| Identité du praticien ayant déclenché l'appel | Jamais | Rien | Hors du format de ligne imposé ; donnée personnelle inutile à l'audit du modèle |
| Jeton d'authentification ou clé d'API | Jamais | Rien | Un secret dans un journal est un secret divulgué |
| Sel de pseudonymisation `INFERENCE_LOG_SALT` | Jamais | Rien | Le sel divulgué rend la pseudonymisation réversible |

## 6.2 — Format de ligne de journal et pseudonymisation

Une ligne JSON par inférence, sans rien de ce que la grille interdit :

```json
{"ts":"2026-10-26T15:41:08.123Z","request_id":"3f2b8c1e-5a47-4d0e-9c1a-7e6d2b9f4a10","model_version":"1.0.0","image_digest":"sha256:0df1b9e549b1d514d6f9943fd4429e32b30b3b10fc3948b95433d5e94af8a728","patient_ref":"a1b2c3d4e5f60718","probabilite_maligne":0.8663,"seuil_applique":0.3333,"decision":"a_examiner","inference_ms":7,"http_status":200,"input_schema_version":"1","covariables":{"age_tranche":"70-79","anatom_site_general":"posterior torso","clin_size_long_diam_mm":3.9,"tbp_lv_L":49}}
```

| Champ | Ce que je décide |
|---|---|
| `ts` | Rien, c'est imposé : UTC ISO 8601 à la milliseconde |
| `request_id` | Repris de l'en-tête `X-Request-ID` de l'appelant ; s'il est absent, un UUID v4 généré par le service |
| `model_version` | Lue dans le paquet sérialisé du modèle |
| `image_digest` | Le digest, et non le tag : un tag peut être déplacé (question 2.1), le digest désigne l'image exacte |
| `patient_ref` | `sha256(sel + ":" + patient_id)`, 16 premiers caractères hexadécimaux, jamais l'identifiant en clair |
| `probabilite_maligne` | 4 décimales : assez pour comparer des distributions ; moins de précision lisserait les écarts utiles à la dérive |
| `seuil_applique` | Le seuil effectif au moment de l'appel : la variable d'environnement `SEUIL` si elle est posée, sinon celui du paquet. Les deux ne disent pas la même chose : le paquet dit ce qui a été validé à l'entraînement, la variable ce qui a réellement été appliqué |
| `decision` | `a_examiner` ou `surveillance`, vocabulaire repris de la séance 2 |
| `inference_ms` | La durée de l'appel au pipeline (`predict_proba`) seul, sans la lecture de la requête ni le réseau |
| `http_status` | Rien |
| `input_schema_version` | À incrémenter dès que la liste ou le type des colonnes attendues change |

**Covariables pour la détection de dérive (séance 5).** Je conserve un sous-ensemble minimal : `age_approx` en tranche de 10 ans, `anatom_site_general` brut, `clin_size_long_diam_mm` arrondie à 1 décimale et `tbp_lv_L` arrondie à l'entier, sous la clé `covariables`. Rien d'autre : plus de variables rendrait la réidentification plus facile (question 6.2).

**Pseudonymisation de `patient_id`.** On concatène le sel lu dans l'environnement (`INFERENCE_LOG_SALT`, jamais en dur dans le code) et l'identifiant, on hache le tout en SHA-256, et on ne conserve que les 16 premiers caractères hexadécimaux. `patient_id` n'est pas une variable du modèle : il arrive hors de la charge utile, dans l'en-tête `X-PatientRef` émis par le poste de consultation.

## 6.3 — Durées de conservation

| Catégorie de trace | Durée de conservation | Besoin qui la justifie | Ce qui se passe à l'échéance |
|---|---|---|---|
| Journal d'inférence complet | 12 mois | Réclamation d'un patient revenu des mois plus tard, et audit annuel | Suppression automatique |
| Journal d'erreurs applicatives | 30 jours | Diagnostic d'incident | Suppression automatique |
| Métriques agrégées, sans identifiant | 13 mois | Comparaison d'une année sur l'autre | Suppression (elles ne portent aucun identifiant) |
| Journal d'accès de la plateforme | 30 jours | Diagnostic de disponibilité | Suppression automatique |

## Question 6.1

**Question 6.1** — Le RGPD distingue les données à caractère personnel (article 4) et, parmi elles, les **données concernant la santé**, qui relèvent des catégories particulières de l'article 9 et dont le traitement est interdit par principe, sauf exception nommée. Vos variables ISIC ne tombent pas toutes dans la même case. Traitez les quatre cas séparément, en deux lignes chacun, et dites pour chacun **article 4, article 9, ou ni l'un ni l'autre** :

1. les variables morphologiques `tbp_lv_*` seules, sans aucun identifiant ;
2. les mêmes, associées à `patient_id` — sachant qu'un seul patient porte jusqu'à 9 184 lésions dans ce jeu ;
3. les mêmes, associées à `age_approx`, `sex` et `anatom_site_general`, sans `patient_id` ;
4. la **probabilité maligne prédite**, associée à un patient identifiable.

Le cas 4 est le plus instructif : une prédiction n'est pas une donnée collectée, c'est une donnée **produite** par vous. Dites si cela change quelque chose à sa qualification.

> 1. Ni l'un ni l'autre. Des mesures de ce type seules sans identifiant ne peuvent pas être rattachées à une personne : ce ne sont pas des données à caractère personnel.
> 2. Article 9. Associées à `patient_id`, elles décrivent l'état de santé d'une personne identifiable : ce sont des données concernant la santé, donc des catégories particulières.
> 3. Article 4, potentiellement 9. Sans `patient_id` la personne n'est pas identifiée, mais l'âge, le sexe et le site anatomique peuvent être suffisants pour retrouver la personne. On doit donc les traiter avec précaution pour qu'elles ne soient pas comprises sous l'article 9.
> 4. Article 9. La probabilité de cancer associée à un patient identifiable est une information sur son état de santé.

## Question 6.2

**Question 6.2** — Le cas 3 porte un piège classique de la réidentification. Avec quelques variables non identifiantes prises isolément — un âge approché, un sexe, un site anatomique, une taille de lésion —, à partir de combien de variables croisées estimez-vous qu'un patient d'un centre donné redevient identifiable ? Vous ne pouvez pas le calculer aujourd'hui : nommez la mesure qu'il faudrait pour y répondre.

> Probablement 3 variables suffiraient à identifier un patient parmi ceux du centre. Il faudrait savoir parmi les patients quelle est l'occurrence de ces caractéristiques, la k-anonymité des données.

## Question 6.3

**Question 6.3** — Votre journal fuite intégralement sur un forum public. Pour chaque ligne de votre grille marquée « Toujours », dites en trois mots ce que l'attaquant en tire. Si l'une d'elles lui donne un avantage sérieux, c'est qu'elle n'aurait pas dû être marquée « Toujours ». Traitez à part le cas de la ligne « probabilité maligne » : une fuite de prédiction est-elle moins grave qu'une fuite de diagnostic ?

> Aucune ligne ne donne un avantage sérieux. Le digest peut indiquer si le service tourne sur une version ancienne non mise à jour et est donc vulnérable à une attaque, mais c'est une fuite acceptable.
>
> Les deux sont graves, une fuite de prédiction peut stigmatiser le patient à tort ou à raison tout comme un diagnostic. Ici elle n'est rattachée qu'à un `patient_ref`, ce qui limite les risques d'abus, mais cette information n'est que pseudonymisée : il est donc possible de recouper plusieurs lignes et d'identifier un patient.

## Question 6.4

**Question 6.4** — Répondez aux quatre questions dans votre rendu :

1. Pourquoi le sel est-il indispensable ? Un `sha256(patient_id)` sans sel serait-il réversible, sachant que le jeu ISIC compte 1 042 patients et que les identifiants suivent un format régulier ?
2. Le résultat est **stable** : le même `patient_id` donne toujours le même `patient_ref`. En quoi est-ce nécessaire pour l'exploitation — pensez au patient qui porte plusieurs lésions —, et en quoi est-ce une faiblesse ?
3. Qui, chez DermaScan, doit pouvoir remonter de `patient_ref` à `patient_id`, et par quel moyen ?
4. Le sel est stocké en réglage d'application. Que devient l'intégralité de votre journal historique si quelqu'un fait tourner ce sel ? Dites si c'est un défaut ou une propriété recherchée.

> 1. Sans sel, `sha256(patient_id)` serait réversible. Un SHA est très facile à calculer, un attaquant pourrait donc recalculer le hash de tous les identifiants possibles (format régulier) et les comparer au journal. Le sel est la protection qui rend cela impossible.
> 2. Un `patient_ref` stable est nécessaire pour pouvoir utiliser plusieurs points de donnée dans un diagnostic (le médecin a besoin de voir l'historique du patient), mais c'est un risque car, en cas d'attaque, ce sont davantage d'informations qui permettent de créer un profil pouvant être rattaché à une personne.
> 3. Seuls les médecins devraient être capables de remonter à un patient depuis sa référence, afin de pouvoir retrouver l'historique du patient dans un but médical, en recalculant le hash de l'identifiant demandé avec le sel, sur demande justifiée et tracée.
> 4. Si le sel tourne, toutes les références changent, ce qui crée une coupure dans l'historisation des patients : impossible de relier les informations du patient après la date de changement avec celles d'avant. C'est à la fois une propriété recherchée (coupe l'identification si le sel a fuité) et un défaut (perte de la continuité des données).

## Question 6.5

**Question 6.5** — Deux exigences tirent les durées dans des sens opposés : la minimisation des données et la capacité d'audit a posteriori. Nommez-les toutes les deux, puis proposez le mécanisme technique qui permet de satisfaire les deux à la fois sans choisir. Indice : il est déjà présent dans votre grille ci-dessus, à la troisième ligne.

> La minimisation des données : conserver le moins de données personnelles possible, le moins longtemps possible.
> La capacité d'audit a posteriori : pouvoir reconstituer une décision plus tard.
> On satisfait les deux avec la pseudonymisation : les données sont à tout moment joignables entre elles, mais difficilement avec un patient précis, seul un médecin le peut avec le sel.

## Question 6.6

**Question 6.6** — Vous n'implémentez pas la purge aujourd'hui. Nommez l'endroit du système où elle devrait être configurée, et dites ce qui se passe si vous la configurez uniquement dans votre code applicatif alors que la plateforme conserve ses propres copies.

> La purge doit être configurée par la plateforme (Azure ici, ou un service externe tel que Grafana) et non dans le code, pour éviter que la plateforme elle-même garde une copie de ce que le code applicatif essaie de supprimer.
