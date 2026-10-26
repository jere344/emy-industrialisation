**Séance 2 — Du modèle à l'API d'inférence** 

**Master 2 · YNOV Campus Montpellier · Industrialisation de l'IA dans le Cloud · 2026-2027** 

## **En-tête de séance** 

| **Durée**     | 3 h 30 de TP                                                                               |
| ------------- | ------------------------------------------------------------------------------------------ |
| **Modalité**  | Individuel, poste personnel, compte Azure for Students                                     |
| **Marche**    | Pipeline scikit-learn sur données tabulaires, API d'inférence                              |
| **ajoutée**   |                                                                                            |
| **Prérequis** | L'image publiée en séance 1,**votre registre ACR toujours actif**(<br>`az acr show --name` |
|               | `"$ACR_NAME"`doit répondre), Docker en marche, Python 3.10 ou plus                         |
| **Livrable**  | Un dossier<br>`s2-<votre-nom>/`déposé avant la fin de la séance                            |



**Ce que vous saurez faire en sortant.** Caractériser un tableau de données avant de modéliser. Écarter les variables qui trahissent la réponse. Découper un jeu sans fuite quand les lignes ne sont pas indépendantes. Construire un pipeline scikit-learn qui apprend ses prétraitements sur le seul ensemble d'entraînement. **Choisir une métrique et un seuil défendables quand une classe est mille fois plus rare que l'autre.** Emballer le tout dans une API et publier l'artefact. 

**Ce que vous ne ferez pas aujourd'hui.** Vous ne **déployez** rien : aucun service ne tournera dans le cloud à la fin de la séance. Votre image, elle, y part bien — vous la publiez dans votre registre en partie 4, et c'est tout ce qui franchit la frontière. La mise en ligne, c'est la séance 3, et elle ne prendra votre artefact que s'il respecte le contrat d'interface rappelé plus bas. 

## **Contexte métier — le fil rouge du module** 

**DermaScan** est un service de télédermatologie. Des cabines de photographie corporelle totale installées en pharmacie photographient la peau de patients volontaires, découpent automatiquement chaque lésion repérée en une vignette de 15 mm, et en extraient une quarantaine de mesures : taille, couleur, régularité du contour, symétrie, position anatomique. 

Un dermatologue ne peut pas relire les centaines de lésions qu'un seul patient produit. La question posée à l'ingénieur est donc une question de **tri** : quelles lésions méritent un examen humain ? 

C'est une question de santé, et elle a deux coûts asymétriques. Manquer une lésion maligne peut coûter une vie. Signaler à tort immobilise un créneau de dermatologue, inquiète un patient, et coûte un examen. **Il n'existe aucun réglage qui annule les deux.** Votre travail n'est pas de trouver ce réglage inexistant : c'est de choisir le compromis, de le chiffrer, et de l'assumer par écrit. 

**Les données sont réelles.** Elles viennent du jeu ISIC 2024, publié par l'International Skin Imaging Collaboration, et agrègent des lésions de neuf institutions hospitalières. Ce sont des **données de santé** : la partie 5 vous demandera d'en tirer les conséquences. 

## **Convention de lecture de l'énoncé** 

Les blancs `_______` sont à compléter. Ils ne sont jamais décoratifs : chacun porte une décision. 

- **L'énoncé n'affirme aucun chiffre.** Les volumétries, les scores, les seuils et les durées sont **vos** mesures. Deux apprenants n'obtiendront pas exactement les mêmes valeurs, et un chiffre recopié sur le voisin se repère immédiatement. 

- Les relevés sont numérotés `**Mesure k**` , les questions `**Question p.q**` . Le barème du corrigé les désigne par ces numéros. 

- Les commandes se lancent depuis la racine `s2-dermascan/` sauf mention contraire. 

## **Tableau de décisions** 

À compléter **avant** de commencer, et à reporter en tête de `MESURES.md` . 

| **Décision**                                            | **Votre valeur**                |
| ------------------------------------------------------- | ------------------------------- |
| Suffixe personnel, identique à la séance 1              | `_______`                       |
| Nom du groupe portant le registre, créé en séance 1     | `rg-dermascan-registre-_______` |
| Nom du registre ACR de la séance 1                      | `_______`                       |
| Rappel visé, décidé**avant**de voir le moindre résultat | `_______`                       |
| Date portée par l'étiquette<br>`a_detruire`             | `_______`                       |



**Question 0.1** — Le rappel visé se décide avant la première mesure. Pourquoi ce n'est pas une coquetterie méthodologique : qu'est-ce qui se passerait si vous le choisissiez après avoir vu la courbe ? 

## **Contrat d'interface à respecter** 

La séance 3 déploiera votre image. Elle attend exactement ceci, et le contrôle est automatique : 

| **Élément**                   | **Valeur imposée**                                               |
| ----------------------------- | ---------------------------------------------------------------- |
| Nom du dépôt dans le registre | `dermascan-api`                                                  |
| Tag                           | `1.0.0`                                                          |
| Port d'écoute                 | lu dans la variable<br>`PORT` , défaut<br>`8000`                 |
| Sonde de santé                | `GET /health` , code 200 si et seulement si le modèle est chargé |
| Carte du modèle               | `GET /model/info`                                                |
| Prédiction                    | `POST /predict` , corps JSON                                     |
| Chemin du modèle dans l'image | lu dans<br>`MODEL_PATH` , défaut<br>`model/modele.joblib`        |



**Partie 1 — Exploration et préparation des données** 

### **Durée indicative : 50 minutes.** 

On ne modélise pas un jeu de données qu'on n'a pas regardé. Cette partie ne produit aucun modèle : elle produit les **chiffres** sans lesquels vous ne saurez pas, en partie 2, si votre modèle est bon ou seulement chanceux. 

## **1.1 — Environnement et obtention des données** 

```
# Dossier de travail de la séance, à côté de celui de la séance 1 et non dedans.
mkdir -p s2-dermascan/{data,model,captures} && cd s2-dermascan
```

```
# Environnement virtuel dédié : l'image, elle, installera ses dépendances seule.
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install pandas scikit-learn joblib flask gunicorn requests kaggle
```

Les données se récupèrent depuis Kaggle. **La procédure complète est en annexe A** : création du jeton, acceptation des règles de la compétition, téléchargement. Faites-la maintenant, elle prend cinq minutes et elle échoue de deux façons prévisibles que l'annexe nomme. 

```
# Produit data/train-metadata.csv. Seul le fichier d'annotation est
# nécessaire aujourd'hui : les images ne servent qu'en séance 4.
ls -lh data/train-metadata.csv
```

**Mesure 1** — versions et volumétrie du fichier. 

| **Relevé**              | **Commande**                                                   | **Votre**<br>**valeur** |
| ----------------------- | -------------------------------------------------------------- | ----------------------- |
| Version de Python       | `python3 --version`                                            |                         |
| Version de scikit-learn | `python3 -c "import sklearn;`<br>`print(sklearn.__version__)"` |                         |
| Version de pandas       | `python3 -c "import pandas; print(pandas.__version__)"`        |                         |
| Poids du fichier        | `ls -lh`                                                       |                         |
| d'annotation            |                                                                |                         |



## **1.2 — Volumétrie et structure** 

Créez `explorer.py` . Ce script ne produit aucun modèle : il produit les chiffres que vous recopierez dans `EXPLORATION.md` . Vous l'écrivez vous-même, à partir de la liste ci-dessous. 

Il doit afficher : le nombre de lignes et de colonnes ; le nombre de **patients distincts** ; le nombre de lésions par patient — minimum, médiane, maximum ; et le type de chaque colonne. 

```
import pandas as pd
d = pd.read_csv("data/train-metadata.csv", low_memory=_______)
print("lignes, colonnes :", d.shape)
print("patients distincts :", d["_______"].nunique())
tailles = d.groupby("_______").size()
print("lesions par patient :", tailles.min(), int(tailles.median()), tailles.max())
```

`low_memory` mérite une seconde d'attention : sur un fichier de 55 colonnes dont plusieurs sont partiellement vides, le réglage par défaut fait deviner les types bloc par bloc et produit des avertissements de type mixte. 

```
python3 explorer.py
```

**Mesure 2** — volumétrie et structure. 

| **Relevé**                                        | **Votre valeur** |
| ------------------------------------------------- | ---------------- |
| Nombre de lignes                                  |                  |
| Nombre de colonnes                                |                  |
| Nombre de patients distincts                      |                  |
| Lésions par patient : minimum / médiane / maximum |                  |



**Question 1.1** — Comparez le nombre de lignes au nombre de patients. Une ligne est-elle une observation indépendante des autres ? Votre réponse commande le découpage de la partie 2.1 : dites laquelle des deux grandeurs détermine la taille réelle de votre échantillon. 

## **1.3 — Les colonnes qui trahissent la réponse** 

Un tableau de données issu d'un contexte médical contient presque toujours des colonnes renseignées **après** le diagnostic. Les garder, c'est prédire la réponse avec la réponse : le modèle affiche un score parfait en validation et s'effondre en production, où ces colonnes n'existent pas encore. 

Étendez `explorer.py` : pour chaque colonne suspecte, affichez le nombre de valeurs renseignées, et **parmi les lignes renseignées, combien sont malignes** . 

```
SUSPECTES = ["iddx_full", "iddx_1", "mel_thick_mm", "mel_mitotic_index", "_______"]
for c in SUSPECTES:
    rempli = d[c].notna().sum()
    malignes = d.loc[d[c].notna(), "_______"].sum()
print(f"{c:<22} rempli {rempli:>7}  dont malignes {int(malignes):>4}")
```

Le rapport qui compte n'est pas « combien de valeurs », c'est **« combien de malignes parmi les lignes renseignées »** , rapporté au nombre total de malignes. 

**Mesure 3** — colonnes à écarter pour cause de fuite. 

| **Colonne**         | **Valeurs renseignées** | **Dont malignes** | **Écartée ?** |
| ------------------- | ----------------------- | ----------------- | ------------- |
| `iddx_1`            |                         |                   |               |
| `iddx_full`         |                         |                   |               |
| `mel_thick_mm`      |                         |                   |               |
| `mel_mitotic_index` |                         |                   |               |
| `lesion_id`         |                         |                   |               |



**Question 1.2** — `lesion_id` est un identifiant, pas une mesure clinique. Pourtant il doit être écarté. Regardez votre relevé et dites **pourquoi** : qu'est-ce que sa seule présence révèle, et à quel moment du parcours d'un patient cet identifiant est-il attribué ? 

**Question 1.3** — Un camarade vous dit : « `iddx_1` donne 100 % de bonnes réponses, je le garde. » Formulez en deux phrases ce qui ne va pas, en distinguant ce que le modèle apprend de ce qu'il saura faire le jour où une nouvelle lésion arrive. 

## **1.4 — Valeurs manquantes et colonnes sans information** 

```
na = d.isna().sum()
print(na[na > 0].sort_values(ascending=_______))
constantes = [c for c in d.columns if d[c].nunique(dropna=True) <= _______]
print("constantes :", constantes)
```

**Mesure 4** — colonnes à valeurs manquantes et colonnes constantes. 

| **Relevé**                                                                         | **Votre valeur** |
| ---------------------------------------------------------------------------------- | ---------------- |
| Colonnes comportant au moins une valeur manquante, hors colonnes de fuite          |                  |
| Pour chacune : taux de valeurs manquantes                                          |                  |
| Colonnes constantes, c'est-à-dire à une seule modalité                             |                  |
| Nombre de variables restantes après retrait des fuites, identifiants et constantes |                  |



**Question 1.4** — Une colonne constante ne gêne aucun algorithme : elle est simplement ignorée. Donnez malgré tout **une** raison de la retirer explicitement, et **une** raison de consigner son existence plutôt que de l'oublier. 

## **1.5 — Distribution de la cible** 

**Mesure 5** — déséquilibre de la cible. 

| **Relevé**                        | **Votre valeur** |
| --------------------------------- | ---------------- |
| Nombre de lésions<br>`target = 1` |                  |
| Nombre de lésions<br>`target = 0` |                  |
| Taux de positifs, en pourcentage  |                  |



Rapport « une maligne pour N bénignes » 

**Question 1.5** — Un classifieur qui répond « bénin » à **toutes** les lésions atteint quelle exactitude sur ce jeu ? Calculez-la à partir de votre mesure 5, et dites ce que cette valeur vous apprend sur l'exactitude comme critère de choix. 

**Partie 2 — Pipeline scikit-learn : entraînement, évaluation, seuil** 

**Durée indicative : 70 minutes.** 

## **2.1 — Découpage sans fuite** 

Votre réponse à la question 1.1 commande cette partie. Un découpage aléatoire ligne à ligne placerait les lésions d'un **même patient** des deux côtés de la barrière : le modèle serait évalué sur des patients qu'il a déjà vus, et son score serait flatteur. 

```
from sklearn.model_selection import GroupShuffleSplit
decoupe = GroupShuffleSplit(n_splits=1, test_size=_______, random_state=_______)
train, test = next(decoupe.split(X, y, groups=_______))
```

**La preuve se fait par comptage, pas par confiance** : l'intersection des patients des deux côtés doit être vide. 

```
assertnot (set(groupes[train]) & set(groupes[test])), "fuite de patients"
```

**Mesure 6** — découpage. 

| **Relevé**         | **Entraînement** | **Test** |
| ------------------ | ---------------- | -------- |
| Nombre de lignes   |                  |          |
| Nombre de patients |                  |          |
| Nombre de positifs |                  |          |
| Taux de positifs   |                  |          |



**Question 2.1** — Vos deux taux de positifs sont-ils identiques ? `GroupShuffleSplit` ne stratifie pas. Dites ce que cela implique quand la classe rare compte quelques centaines de cas, et nommez la conséquence sur la **stabilité** de vos scores d'une graine à l'autre. 

## **2.2 — Construction du pipeline** 

Les prétraitements doivent **apprendre leurs statistiques sur l'entraînement seul** . Une imputation calculée sur le tableau complet fait entrer l'information du test dans le modèle. 

```
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
```

```
pre = ColumnTransformer([
    ("num", Pipeline([("imputation", SimpleImputer(strategy="_______")),
                      ("echelle", StandardScaler())]), colonnes_numeriques),
    ("cat", Pipeline([("imputation", SimpleImputer(strategy="_______")),
                      ("encodage", OneHotEncoder(handle_unknown="_______"))]),
colonnes_categorielles),
])
```

**Question 2.2** — `handle_unknown` : que se passe-t-il, en production, si une cabine remonte une position anatomique jamais vue à l'entraînement ? Comparez les deux comportements possibles et dites lequel vous retenez pour un service de tri médical. 

**Question 2.3** — Pourquoi l'imputation est-elle une **étape du pipeline** et non un traitement appliqué au tableau avant le découpage ? Une phrase, qui nomme ce qui entrerait dans le modèle dans le second cas. 

## **2.3 — Entraînement et le piège de l'exactitude** 

Entraînez d'abord une **référence qui n'apprend rien** : `DummyClassifier(strategy="most_frequent")` . Puis votre modèle : une régression logistique, avec `class_weight="balanced"` . 

```
from sklearn.linear_model import LogisticRegression
modele = Pipeline([("pre", pre),
                   ("clf", LogisticRegression(max_iter=1000, class_weight="_______"))])
```

```
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, average_precision_score
```

```
reference = DummyClassifier(strategy="_______").fit(X.iloc[train], y[train])
proba = modele.predict_proba(X.iloc[test])[:, _______]
print("exactitude", accuracy_score(y[test], modele.predict(X.iloc[test])))
print("PR-AUC   ", average_precision_score(y[test], proba))
print("hasard   ", y[test]._______())
```

**Mesure 7** — comparaison des deux modèles, sur l'ensemble de test. 

| **Modèle**                      | **Exactitude** | **ROC-AUC** | **PR-AUC** |
| ------------------------------- | -------------- | ----------- | ---------- |
| `DummyClassifier`               |                |             |            |
| Régression logistique           |                |             |            |
| Valeur du hasard pour la PR-AUC | —              | —           |            |



**Question 2.4** — Regardez la colonne « Exactitude ». Lequel des deux modèles est le meilleur selon ce seul critère ? Lequel l'est réellement ? **Cette contradiction est le cœur de la séance** : expliquez-la en nommant ce que l'exactitude compte et ce qu'elle ne compte pas. 

**Question 2.5** — La PR-AUC du hasard vaut exactement le taux de positifs. Vérifiez-le sur vos chiffres, puis dites pourquoi la PR-AUC est plus informative que la ROC-AUC quand la classe positive est très rare. 

## **2.4 — Choix du seuil** 

Un modèle de classification ne décide pas : il attribue une probabilité. **C'est vous qui décidez** , en posant un seuil. Et ce seuil n'est pas un détail technique : c'est un arbitrage clinique, qui se justifie devant un médecin. 

Produisez le tableau du compromis sur votre ensemble de test. 

**Mesure 8** — compromis rappel / précision. 

| **Seuil** | **Rappel** | **Précision** | **Vrais positifs** | **Faux positifs** | **Faux négatifs** | **Alertes pour 1000 lésions** |
| --------- | ---------- | ------------- | ------------------ | ----------------- | ----------------- | ----------------------------- |
| 0,50      |            |               |                    |                   |                   |                               |
| 0,80      |            |               |                    |                   |                   |                               |
| 0,90      |            |               |                    |                   |                   |                               |
| 0,99      |            |               |                    |                   |                   |                               |



Puis déterminez le seuil qui atteint le **rappel que vous avez inscrit au tableau de décisions** , avant d'avoir vu quoi que ce soit. 

```
from sklearn.metrics import precision_recall_curve
precision, rappel, seuils = precision_recall_curve(y_test, proba)
# precision_recall_curve renvoie un seuil de MOINS que de points.
# Plus petit seuil garantissant au moins le rappel vise :
i = np.where(rappel >= _______)[0][_______]
seuil_retenu = seuils[min(i, len(seuils) - 1)]
# Cout du compromis, exprime comme un clinicien le comprend :
print("lesions examinees par maligne trouvee :", round(1 / precision[i]))
```

**Mesure 9** — seuil retenu et son coût. 

| **Relevé**                                          | **Votre valeur** |
| --------------------------------------------------- | ---------------- |
| Rappel visé, décidé en début de séance              |                  |
| Seuil correspondant                                 |                  |
| Précision à ce seuil                                |                  |
| **Nombre de lésions examinées par maligne trouvée** |                  |
| Faux négatifs restants                              |                  |



**Question 2.6** — Votre dernière ligne : combien de lésions un dermatologue doit-il examiner pour trouver une maligne, à votre seuil ? Présentez ce chiffre comme vous le feriez devant le médecin-chef de DermaScan, et dites ce que vous lui répondez s'il juge le nombre inacceptable. 

**Question 2.7** — Les faux négatifs ne tombent jamais à zéro. Formulez en une phrase, **sans adverbe** , ce que votre service promet et ce qu'il ne promet pas. 

## **2.5 — Sérialisation avec métadonnées** 

Le paquet sérialisé doit permettre à un tiers de servir votre modèle **sans vous** . Un pipeline seul n'y suffit pas. 

```
paquet = {
"pipeline": modele,
"version": "_______",
"colonnes_attendues": _______,
"seuil": _______,
"rappel_cible": _______,
"metriques": {...},
"prevalence_entrainement": _______,
"entraine_le": _______,
}
joblib.dump(paquet, "model/modele.joblib")
```

**Mesure 10** — paquet produit. 

| **Relevé**                             | **Votre valeur** |
| -------------------------------------- | ---------------- |
| Taille du fichier, en Ko               |                  |
| Nombre de colonnes attendues déclarées |                  |
| Durée de l'entraînement, en secondes   |                  |



**Question 2.8** — Pourquoi `prevalence_entrainement` figure-t-elle dans le paquet ? Elle ne sert à aucun calcul au moment de la prédiction. À quoi servira-t-elle en séance 5, quand il faudra décider si le flux reçu ressemble encore à celui de l'entraînement ? 

**Question 2.9** — Citez deux conséquences concrètes, pour l'API de la partie 3, de l'absence de `colonnes_attendues` dans le paquet. 

# **Partie 3 — API d'inférence** 

**Durée indicative : 50 minutes.** 

## **3.1 — Chargement du modèle** 

Le paquet se charge **une fois** , au démarrage du processus, et non à chaque requête. 

```
# Chargement au demarrage, PAS dans la fonction de vue.
try:
    PAQUET = joblib.load(os.environ.get("MODEL_PATH", "_______"))
    PIPELINE = PAQUET["pipeline"]
    SEUIL = float(os.environ.get("SEUIL", PAQUET["_______"]))
except Exception as exc:
    PIPELINE = None
    ERREUR = f"{type(exc).__name__}: {exc}"
```

Un modèle absent ne doit **pas** empêcher le processus de démarrer : c'est la sonde qui signalera l'indisponibilité, pas un plantage. 

**Question 3.1** — Chiffrez l'enjeu à partir de votre mesure 10 : quelle serait la latence ajoutée à chaque appel si le modèle était rechargé à chaque requête ? 

## **3.2 — Les trois endpoints** 

| **Endpoint**    | **Comportement attendu**                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------- |
| `GET /health`   | 200 si le modèle est chargé,**503 sinon**— le processus vivant et le service en état de servir ne |
|                 | sont pas la même chose                                                                            |
| `GET`           | Version, seuil, rappel visé, métriques, prévalence d'entraînement, colonnes attendues             |
| `/model/info`   |                                                                                                   |
| `POST /predict` | Probabilité, seuil appliqué,**décision**, version du modèle                                       |



**Validez avant de prédire.** Une charge utile incomplète doit produire un `400` nommant ce qui manque, jamais un `500` . 

```
manquantes = [c for c in COLONNES if c notin charge]
if manquantes:
return jsonify({"error": "_______", "manquantes": manquantes[:10]}), _______
```

```
return jsonify({
"probabilite_maligne": round(proba, 6),
"seuil": SEUIL,
"decision": "_______"if proba >= SEUIL else"_______",
"version_modele": PAQUET["version"],
```

```
"rappel_cible": PAQUET["rappel_cible"],
})
```

**Question 3.2** — Votre `/predict` renvoie `decision` **et** `seuil` **et** `rappel_cible` . Pourquoi renvoyer les trois plutôt que la seule décision ? Pensez au dermatologue qui recevra cette réponse dans six mois, quand le seuil aura changé. 

## **3.3 — Tests locaux** 

```
PORT=8000 python3 app.py &
curl -s -i http://localhost:8000/health | head -1
curl -s http://localhost:8000/model/info
# Prediction sur une ligne reelle extraite de votre jeu de test.
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" -d @charge.json
```

**Mesure 11** — réponses de l'API. 

| **Appel** |                                | **Code HTTP** | **Élément relevé**                       |
| --------- | ------------------------------ | ------------- | ---------------------------------------- |
| `GET`     | `/health`                      |               | champ<br>`model_loaded`                  |
| `GET`     | `/model/info`                  |               | nombre de colonnes attendues             |
| `POST`    | `/predict` , charge valide     |               | `probabilite_maligne`et<br>`decision`    |
| `POST`    | `/predict` , charge incomplète |               | nombre de variables manquantes signalées |
| `POST`    | `/predict` , corps vide        |               |                                          |



**Mesure 12** — latence de dix appels successifs sur charge valide : minimum, médiane, maximum. **Question 3.3** — Retirez temporairement `model/modele.joblib` et relancez l'API. Quel code renvoie 

`/health` ? Pourquoi est-ce **préférable** à un plantage au démarrage, du point de vue de la plateforme qui hébergera ce service en séance 3 ? 

**Partie 4 — Conteneurisation et publication** 

### **Durée indicative : 40 minutes.** 

Vous ne réécrivez pas votre Dockerfile de la séance 1. Vous l'étendez : trois lignes de dépendances supplémentaires et un fichier de modèle à copier. 

```
# Les dependances d'abord, le code ensuite : l'ordre de la seance 1 tient toujours.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Le modele est un artefact, pas du code : il a sa propre ligne.
COPY _______ ./model/
COPY app.py ./
CMD ["gunicorn", "-b", "0.0.0.0:_______", "app:app"]
```

**Question 4.1** — Votre `requirements.txt` passe de une à cinq dépendances directes. À partir de votre mesure de la séance 1, estimez l'écart de taille d'image attendu, puis vérifiez. 

**Mesure 13** — image de la séance 2, comparée à celle de la séance 1. 

| **Relevé**                             | **Séance 1** | **Séance 2** |
| -------------------------------------- | ------------ | ------------ |
| Taille de l'image                      |              |              |
| Nombre de couches                      |              |              |
| Durée de construction à froid          |              |              |
| Nombre de paquets dans<br>`pip freeze` |              |              |



**Question 4.2** — Le modèle pèse quelques kilo-octets, les dépendances plusieurs centaines de mégaoctets. Qu'est-ce que cela vous dit sur ce qui coûte cher dans un artefact d'inférence, et sur ce qu'il faudrait optimiser en premier si la taille devenait un problème ? 

## **4.3 — L'artefact est lié à la version qui l'a produit** 

Lancez votre conteneur et appelez `/predict` . **Il est probable que vous obteniez une erreur** , alors que le même appel fonctionnait hors conteneur quelques minutes plus tôt. 

```
docker run -d --name dermascan-api -p 8000:8000 dermascan-api:1.0.0
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" -d @charge.json
```

Un pipeline scikit-learn sérialisé n'est **pas** un format d'échange : c'est un graphe d'objets Python, et il ne se recharge pas dans une version de bibliothèque différente de celle qui l'a produit. Votre environnement virtuel et votre image n'ont aucune raison d'avoir les mêmes versions — sauf si vous les y forcez. 

**Mesure 15** — cohérence des versions entre l'entraînement et l'image. 

**Relevé Votre valeur** 

| Version de scikit-learn ayant entraîné le modèle — champ<br>`versions`du paquet |
| ------------------------------------------------------------------------------- |
| Version de scikit-learn épinglée dans<br>`requirements.txt`                     |
| Sont-elles identiques ?                                                         |
| Message d'erreur exact, s'il y en a un                                          |



Corrigez en épinglant dans `requirements.txt` **les versions relevées à la mesure 1** , puis reconstruisez. **Question 4.3** — Vous auriez pu ne pas épingler du tout et laisser `pip` installer la dernière version. Donnez les deux moments où cette image aurait cessé de fonctionner, et dites lequel des deux est le plus dangereux pour un service déjà en production. 

## **4.4 — Publication** 

```
# Reconstruction pour la cible du cloud, comme en seance 1.
docker build --platform linux/amd64 --provenance=false -t "$IMAGE_FULL" .
docker push "$IMAGE_FULL"
az acr repository show-tags --name "$ACR_NAME" --repository dermascan-api --output table
```

**Mesure 16** — publication : durée du push, digest obtenu, tags présents dans le registre. 

**Partie 5 — Gouvernance : model card** 

### **Durée indicative : 25 minutes.** 

Les données que vous venez d'exploiter sont des **données de santé** , collectées dans neuf institutions hospitalières. Une model card n'est pas un exercice de style : c'est ce qui permet à quelqu'un d'autre de décider s'il peut utiliser votre modèle, et pour quoi. 

Rédigez `MODEL_CARD.md` avec ces rubriques : 

| **Rubrique**                      | **Ce qu'on y attend**                                                                  |
| --------------------------------- | -------------------------------------------------------------------------------------- |
| Usage prévu                       | Le tri, et rien d'autre                                                                |
| **Usage explicitement exclu**     | Nommez-le                                                                              |
| Données d'entraînement            | Origine, volumétrie, prévalence,**et le fait qu'elle diffère de la prévalence réelle** |
| Variables utilisées               | Nombre, et les familles                                                                |
| Variables écartées, avec le motif | Les fuites, nommément                                                                  |
| Performance                       | PR-AUC, et la valeur du hasard en regard                                               |
| Seuil et compromis                | Le chiffre de votre mesure 9                                                           |
| Populations et angles morts       | Qui est sous-représenté dans neuf hôpitaux occidentaux ?                               |
| Versions                          | Modèle, image, digest                                                                  |



**Question 5.1** — Votre modèle a été entraîné sur une prévalence de l'ordre de 0,1 %. Si DermaScan l'installe dans une consultation spécialisée où une lésion sur vingt est maligne, votre seuil reste-t-il valable ? Justifiez, et dites ce qu'il faudrait refaire. 

**Question 5.2** — Citez une population pour laquelle vous **refuseriez** de garantir les performances annoncées, et dites sur quelle colonne de votre jeu vous vous appuyez pour l'affirmer. 

# **Nettoyage obligatoire** 

Le nettoyage n'est pas la destruction aveugle de ce que vous avez produit : c'est la **décision explicite** de ce qui survit et de ce qui disparaît, avec sa raison et sa date. 

**Pourquoi cette section décide de la suite du module.** Votre abonnement _Azure for Students_ n'est pas seulement une réserve d'argent : c'est lui qui vous donne accès à `Microsoft.ContainerRegistry` et `Microsoft.ContainerInstance` . **Un crédit épuisé ne vous laisse pas un abonnement pauvre : il le fait basculer sur l'offre** **_Starter_ , qui interdit purement et simplement ces deux fournisseurs.** Vous n'y perdez pas la possibilité de payer, vous y perdez votre registre — donc l'artefact que les séances suivantes consomment. Épuiser son crédit en séance 3, c'est ne plus pouvoir faire la séance 4, la séance 5, ni le projet fil rouge. Le nettoyage n'est pas une bonne pratique de plus : c'est ce qui vous permet de terminer le module. 

Comme en séance 1, vous laissez volontairement une ressource active — la même, votre registre. Raison de plus pour relever votre crédit : comparez-le au relevé de la séance 1, c'est l' **écart** entre deux mesures qui révèle ce qui tourne à votre insu. 

```
# Conteneurs de la seance, puis images locales : l'image publiee, elle, reste.
docker rm -f _______ 2>/dev/null
docker system prune -f
deactivate
```

**Décision sur les ressources Azure.** Cette séance **ne crée aucun groupe de ressources** : elle publie dans le registre créé en séance 1, qui est conservé **jusqu'à la fin du module** — la séance 4 et le projet fil rouge y publient encore. Vous ne détruisez donc rien côté Azure, et vous contrôlez que ce que vous laissez actif est bien ce que vous croyez — une ressource, et une date d'échéance encore valide. 

```
az resource list --resource-group "$RG" --output table
az group show --name "$RG" --query "tags" --output json
```

**Mesure 17** — contrôles de nettoyage et coût de ce que vous laissez actif. 

| **Contrôle de fin de séance**                     | **Votre observation** |
| ------------------------------------------------- | --------------------- |
| Espace disque libéré par<br>`docker system prune` |                       |
| Espace libéré en séance 1, pour comparaison       |                       |
| Nombre de ressources laissées actives             |                       |
| Coût journalier estimé du SKU<br>`Basic`          |                       |
| Date portée par l'étiquette<br>`a_detruire`       |                       |
| Crédit restant, relevé dans<br>`Cost Management`  |                       |
| Écart avec le relevé de la séance précédente      |                       |



**Question 6.1** — En séance 1 vous avez rédigé la phrase de ticket qui justifie de laisser ce registre actif. Relisez-la : est-elle encore exacte ? Le registre ne contient plus la même chose qu'il y a une semaine, et sa date d'échéance a peut-être été écrite avant que vous sachiez combien de séances en dépendraient. Corrigez-la, et dites en une ligne ce qui vous a fait la corriger — ou pourquoi elle tient toujours. 

## **Avant de quitter la salle — extinction** 

**Toute ressource active est une ressource que vous payez.** Vous payez la _réservation_ , pas l'usage : un service que personne n'appelle, la nuit et le week-end, coûte exactement le même prix qu'un service sollicité. C'est cette règle, et elle seule, qui décide si vous finirez le module avec du crédit. 

Trois gestes, dans cet ordre. Aucun n'est facultatif, et ils se font **avant** de fermer votre session, pas « plus tard depuis chez vous » — un oubli du vendredi se paie jusqu'au lundi. 

1. **Côté Azure. rien n'a été créé aujourd'hui, et rien ne doit l'être.** Cette séance n'a fait que publier une image dans le registre de la séance 1. Contrôlez qu'aucun groupe ne s'est ajouté à votre insu. 

2. **Côté poste — arrêtez ce qui tourne encore.** Conteneurs de la séance supprimés, Docker Desktop **quitté** (un démon laissé actif relance vos conteneurs au prochain démarrage et consomme mémoire et batterie), environnement virtuel désactivé. 

3. **Éteignez votre machine.** Éteinte, pas en veille. 

```
docker ps -a                 # plus aucun conteneur de la séance
az group list --output table # toujours un seul groupe, celui du registre
```

| **Contrôle d'extinction**                                         | **Fait** |
| ----------------------------------------------------------------- | -------- |
| `az group list`ne montre toujours qu'un groupe, celui du registre |          |
| Aucun conteneur de la séance dans<br>`docker ps -a`               |          |
| Docker Desktop quitté                                             |          |
| Machine éteinte                                                   |          |



# **Livrable attendu** 

Un dossier `s2-<votre-nom>/` déposé sur le dépôt de classe avant la fin de la séance. 

| **Fichier**                          | **Contenu**                                                                |
| ------------------------------------ | -------------------------------------------------------------------------- |
| `EXPLORATION.md`                     | Les mesures 1 à 5 et les questions 0.1 à 1.5                               |
| `explorer.py`                        | Votre script d'exploration                                                 |
| `entrainer.py`                       | Pipeline, découpage par patient, évaluation, choix du seuil, sérialisation |
| `app.py`                             | L'API, trois endpoints, validation avant prédiction                        |
| `MESURES.md`                         | Les mesures 6 à 17 et les questions 2.1 à 6.1                              |
| `MODEL_CARD.md`                      | Les neuf rubriques de la partie 5                                          |
| `Dockerfile` ,<br>`requirements.txt` | L'artefact                                                                 |
| `captures/`                          | Le dépôt visible dans le portail ACR, et une réponse de<br>`/predict`      |



**Ne déposez pas** `data/train-metadata.csv` ni `model/modele.joblib` : le premier pèse 246 Mo, le second se régénère par `python3 entrainer.py` . 

**Annexe A — Récupération des données** 

Le fichier d'annotation vient de la compétition Kaggle ISIC 2024. Deux étapes, et chacune échoue de façon prévisible si elle est sautée. 

**Étape 1 — accepter les règles.** Rendez-vous sur la page de la compétition, onglet _Rules_ , et cliquez sur _I Understand and Accept_ . **Sans cette acceptation, le téléchargement échoue en** **`403 Forbidden` même authentifié** , et le message d'erreur ne dit pas pourquoi. 

**Étape 2 — s'authentifier.** 

```
kaggle auth login     # ouvre un navigateur, met les identifiants en cache
```

**Étape 3 — télécharger le fichier d'annotation seul.** 

```
kaggle competitions download -c isic-2024-challenge -f train-metadata.csv -p data/
unzip -o data/train-metadata.csv.zip -d data/ && rm data/train-metadata.csv.zip
ls -lh data/train-metadata.csv
```

Les images, qui pèsent plusieurs centaines de méga-octets, **ne sont pas nécessaires aujourd'hui** . Elles le seront en séance 4. 

# **Annexe B — Plan de repli sans Azure** 

Si la publication sur le registre échoue, ou si votre crédit est épuisé, les parties 1 à 3 restent intégralement faisables : elles ne touchent pas au cloud. Pour la partie 4, construisez l'image localement et conservez la sortie de `docker images` et de `docker inspect` comme preuve. La séance 3 vous fournira un chemin de rattrapage. 

# **Annexe C — Dépannage** 

| **Symptôme**                                      | **Cause probable**                                | **Correction**                                          |
| ------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------- |
| `403 Forbidden`au téléchargement<br>Kaggle        | Règles de la compétition non<br>acceptées         | Annexe A, étape 1                                       |
| `KeyError: 'target'`                              | Vous avez téléchargé<br>`test-`<br>`metadata.csv` | La cible n'existe que dans le fichier<br>d'entraînement |
| Score parfait en validation                       | Une colonne de fuite est restée                   | Mesure 3 : vérifiez que les neuf sont<br>écartées       |
| `ValueError: Found unknown`<br>`categories`       | `handle_unknown`mal réglé                         | Question 2.2                                            |
| L'exactitude baisse quand le modèle<br>s'améliore | Comportement**attendu**                           | Question 2.4 : ce n'est pas un bug                      |
| `/predict`renvoie 500                             | Validation absente avant prédiction               | Partie 3.2                                              |
| `/health`renvoie 200 sans modèle<br>chargé        | Sonde de complaisance                             | Elle doit renvoyer 503                                  |



# **Annexe D — Ce que vous emportez vers la séance 3** 

| **Artefact**                   | **Nom verrouillé**                                    |
| ------------------------------ | ----------------------------------------------------- |
| Dépôt dans le registre         | `dermascan-api` , tag<br>`1.0.0`                      |
| Variables d'environnement lues | `PORT` ,<br>`MODEL_PATH` ,<br>`SEUIL`                 |
| Endpoints                      | `/health` ,<br>`/model/info` ,<br>`/predict`          |
| Groupe de ressources conservé  | celui de cette séance, étiqueté<br>`a_detruire`       |
| Seuil et rappel visé           | consignés dans le paquet**et**dans<br>`MODEL_CARD.md` |



