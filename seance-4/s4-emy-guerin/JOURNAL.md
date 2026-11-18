# JOURNAL — Séance 4

## Tableau de décisions

| Décision | Contrainte | Ma valeur |
|---|---|---|
| Nombre de négatifs tirés (`N_NEGATIFS`) | Avec GPU : 20 000 ; sans GPU : mode dégradé | 5 000 : pas de GPU, entraînement en local (voir mesure 6) |
| Graine de l'échantillonnage et du découpage | Celle du code distribué | 42 |
| Taille d'entrée du réseau | Lue dans `donnees.py` | 128 px |
| Architecture | Lue dans `entrainer.py` | ResNet18 préentraîné sur ImageNet, 1 seul logit en sortie |
| Époques backbone gelé / époques `layer4` dégelé | Lues dans `entrainer.py` | 4 / 4 |
| Taux d'apprentissage gelé / dégelé | Lus dans `entrainer.py` | 1×10⁻³ / 1×10⁻⁴ |
| Taille de lot | Lue dans `entrainer.py` | 64 |
| Part de validation | Exprimée en plis | 1 pli sur 5 (`StratifiedGroupKFold(5)`, pli 0), donc 20 % |
| Rappel visé pour le seuil de décision | À justifier par rapport à S2 | 0,90, le même qu'en S2 pour pouvoir comparer les deux modèles |
| Métrique de sélection de l'époque | Lue dans `entrainer.py` | PR-AUC de validation |
| Tag de l'image de la séance | Version sémantique | `2.0.0` : version majeure, l'entrée de `/predict` n'est plus la même (une image au lieu du JSON de `1.0.0` et `1.0.1`), les anciens clients ne marchent plus |
| Groupe de ressources de la séance | `rg-dermascan-s4-*` | `rg-dermascan-s4-EG08` |
| Registre ACR | Celui de S1 | `dermascaneg08` (groupe `rg-dermascan-registre-EG08`) |

## Mesure 1 — l'archive et l'échantillon (`python donnees.py`, sortie dans `sorties/donnees_inventaire.txt`)

| Relevé | Valeur |
|---|---|
| Vignettes dans l'archive _Permissive_ | 217 477 |
| Positifs dans l'archive, et prévalence | 294, soit 0,135 % |
| Patients distincts dans l'archive | 634 |
| Vignettes de l'échantillon : positifs + négatifs | 5 294 = 294 + 5 000 |
| Prévalence de l'échantillon | 5,55 % |
| Taille du tableau en mémoire | (5294, 128, 128, 3), uint8, 260 Mo |
| Taille d'origine des vignettes (500 premières) : médiane, min, max | 127 px, 87 px, 215 px |
| Durée de `python donnees.py`, premier lancement puis second | 10,9 s (sans cache `.npy`) puis 5,3 s (avec cache) |

J'ai refait le premier lancement le 17/11 en déplaçant le cache, pour mesurer la lecture dans le zip.

## Mesure 2 — ligne d'échantillonnage

| Effectif | Graine | Méthode | Prévalence d'entraînement | Empreinte du manifeste (16 premiers caractères) |
|---|---|---|---|---|
| 5 294 (294 positifs + 5 000 négatifs) | 42 | tous les positifs + négatifs tirés au hasard sans remise (`pandas.sample`) | 5,55 % | `64d2e25ddd474269` |

## Question 0.1

Les étapes d'échantillonage et de découpages seront identiques pour les deux apprenants, et quelque soit l'architecture puisque ce sont des processus déterministique, ils dépendent uniquement des données d'entrée et de la seed random_state=42. L'ordre des opérations pour ces étapes est toujours le même. random_state garranti donc l'ordre des lots.
Par contre les poids finaux seront différents car le CPU et le GPU exécutent les calculs d'entrainement dans des ordres différents, et que cet ordre a ici une importance à cause des arrondis. En binaire avec des virgule on a parfois (a+b)+c != a+(b+c).

## Question 0.2

L'exactitude compte chaque ligne de la même manière : un faux positif et un faux négatif sont à égalité. Or la classe positive est rare, donc un modèle qui répond toujours « bénin » obtient une exactitude très élevée sans rien détecter. La PR-AUC, elle, ne regarde que le classement des malins, donc elle choisit l'époque qui les détecte le mieux.

## Question 1.1

Raison liée à la recalibration : la correction dépend de β = N_NEGATIFS / bénins de l'archive. Avec un effectif fixe, β est un chiffre exact, écrit dans le meta (`taux_negatifs`) ; si le nombre de bénins tirés changeait sans être noté, la correction ne serait plus la bonne et les probabilités montrées aux médecins ne correspondraient plus à la réalité.

Utiliser un nombre fixe de bénin donne un résultat plus reproductible parce que ça évite de modifier la proportion de malin dans l'échantillons qui va directement impacter la qualité de notre apprentissage.

## Question 1.2

Dermascan est un service commercial destiné à la production, nous devons donc respecter les licences de nos données d'entrainement, même si cela à un coup en terme de qualité finale du produit. train-image.hdf5 de Kaggle contient des images à license "non commerciale" qui nous interdirait de commercialiser notre produit.

## Mesure 3 — exactitude du modèle constant « bénin » (N_NEGATIFS = 5000)

| Population | Calcul | Exactitude |
|---|---|---|
| Flux réel (l'archive entière) | 217 183 / 217 477 | 99,865 % |
| Échantillon d'entraînement | 5 000 / 5 294 | 94,447 % |
| Jeu de validation | 999 / 1 058 | 94,423 % |

## Question 1.3

Le plancher dépend uniquement de la proportion de malin dans la population : un modèle qui répond toujours bénin a une exactitude de 99,865 % sur le flux réel mais seulement 94,4 % sur l'échantillon, parce que celui-ci contient une quantité disproportionnée de malin. On ne se base pas sur l'exactitude pour connaître l'efficacité du modèle, parce que ce qui nous intéresse c'est de dénicher les malins, pas juste l'exactitude.

## Mesure 4 — patients communs aux deux jeux, selon le découpage (N_NEGATIFS = 5000)

| Découpage | Vignettes en validation | Positifs en validation | Patients en validation | Patients communs |
|---|---|---|---|---|
| `decouper()` (par patient) | 1 058 | 59 | 109 | 0 |
| `train_test_split` ligne à ligne | 1 059 | 59 | 394 | 384 |

Expérience de fuite : `train_test_split(m, test_size=0.2, stratify=m.cible, random_state=42)` sur `model/manifeste_echantillon.csv`.

## Question 2.1

Le découpage par ligne permettrai au modèle de s'entrainer sur des données annexes que les lesions elles-mêmes : il sait que ce type d'éclairage correspond à tel patient qui a des lesions malignes, il y a plus de chance que les autres photo avec le même éclairage appartiennent au même patient et que ses lesions sont malignes. Ainsi le cadrage de la photo par exemple deviendrait plus important que la lésion elle-même par exemple, ce qui fonctionnera avec notre jeux de validation mais pas dans une utilisation réelle. La PR-AUC de validation serait donc surestimée (trop haute) par rapport à la performance réelle sur de nouveaux patients.

## Question 2.2

Avec un échantillon si bas, il y a un risque que les patients malins se retrouvent dans le même pli, d’autant plus que plusieurs lésions malignes peuvent appartenir au même patient. Si la validation n’avait par hasard aucun malin (ou très peu), la PR-AUC serait indéfinie ou apparaitrait aléatoire, et ne correspondrait pas à la vie réelle. StratifiedGroupKFold garantit un nombre de malin similaire dans chaque pli (ici 59 positifs sur 1 058 en validation).

## Mesure 5 — le lot d'entrée, tel que le réseau le reçoit (64 premières vignettes)

| Relevé | Valeur |
|---|---|
| Forme | (64, 3, 128, 128) |
| Type | torch.float32 |
| Minimum et maximum | -2,118 et 2,249 |
| Moyenne et écart-type | 0,531 et 0,648 |

## Question 2.3

On garde la moyenne et l'écart-type d'ImageNet car ResNet18 a été préentraîné avec ces valeurs. Ma moyenne est de 0.53, loins de 0, ce qui veux dire que les vignettes sont en moyenne plus claires que les images d'entrainement d'imageNet

## Question 2.4

128 x 128 = 16384
224 x 224 = 50176
50176 / 16384 = 3,0625
Le facteur de cout de passer de 128 à 224 pixel est 3,0625

Augmenter artificiellement le nombre de pixel ne rajoute pas d'information à la photo d'origine, cela n'a donc aucun intéret pour un entrainement.

## Question 2.5

Tourner un chiffre manuscrit changerait les résultats du modèle puisque 6 se confondrait avec 9, alors qu'un lesion est toujours là même quelle que soit l'orientation par laquelle on la regarde. En revanche, changer la couleur des images serait une faute ici, puisque la couleur est un critère important dans l'interprétation de la lésion (règle clinique ABCDE "C", couleur)

## Question 2.6

L'augmentation en validation n'a pas de sens, l'augmentation sert au modèle à apprendre. De plus une augmentation aléatoire sur la validation entrainerait une PR-AUC instable, qui change selon l'execution avec le même modèle, puisque le jeux de donnée changerait aussi.

## Question 3.1

| Phase | Couches qui apprennent | Paramètres entraînables | Part du total |
|---|---|---|---|
| Tête seule | `fc` | 513 | 0,005 % |
| Dégel | `fc` + `layer4` | 8 394 241 | 75,10 % |
| Total du réseau | — | 11 177 025 | 100 % |

## Question 3.2

Cela ne suffit pas parce qu'en plus des couches classiques du modèle il existe des couches "BatchNorm" qui ne se règlent pas par gradient, mais gardent en mémoire une moyenne et une variance des valeurs vues par le réseau. Ainsi requires_grad=False ne les concerne pas : en mode train(), leur moyenne et leur variance continueraient de se mettre à jour sur nos lésions et dériveraient sans aucun message d'erreur, malgré regler_gel(). mode_entrainement() règle cela en mettant tout le réseau en eval() (statistiques figées), puis en remettant en train() seulement les couches actives (fc, et layer4 au dégel).

## Mesure 6 — conditions de l'entraînement

| Relevé | Valeur |
|---|---|
| Où | Poste, CPU (aucun GPU) |
| `N_NEGATIFS` effectivement utilisé | 5 000 |
| Vignettes d'entraînement et de validation (positifs) | 4 236 (235 pos) et 1 058 (59 pos) |
| Durée de chargement des données | 4,5 s (5,1 s avant la coupure) |

## Mesure 7 — courbe d'entraînement (identique à `sorties/historique.csv`)

| Époque | Phase | Durée (s) | Perte d'entraînement | PR-AUC | ROC-AUC | pAUC (rappel > 80 %) |
|---|---|---|---|---|---|---|
| 1 | tête | 58,7 | 0,2669 | 0,1541 | 0,5297 | 0,0116 |
| 2 | tête | 44,9 | 0,1941 | 0,2959 | 0,7922 | 0,0694 |
| 3 | tête | 44,1 | 0,1765 | 0,3329 | 0,8318 | 0,0883 |
| 4 | tête | 41,4 | 0,1716 | 0,3681 | 0,8568 | 0,1042 |
| 5 | dégel | 52,6 | 0,1805 | 0,4489 | 0,8786 | 0,1070 |
| 6 | dégel | 55,0 | 0,1275 | 0,3553 | 0,8184 | 0,0792 |
| 7 | dégel | 51,9 | 0,1079 | 0,4785 | 0,8878 | 0,1124 |
| 8 | dégel | 47,1 | 0,0894 | 0,4932 | 0,9058 | 0,1292 |

Époque retenue : la 8.

## Question 3.3

La perte diminue (0,1805 → 0,1275) alors que la PR-AUC recule (0,4489 → 0,3553) entre l'époque 5 et 6.

Deux hypothèses :

* Le modèle s'améliore sur autre chose que sur notre objectif, l'identification de lésions malignes : la perte mesure l'ajustement aux images d'entraînement, la PR-AUC la performance sur des images neuves. C'est du surapprentissage, le réseau apprend mieux ses exemples sans mieux généraliser.
* Le jeu de validation est petit : 59 malins seulement. L'écart est dû au hasard plus qu'à une régression réelle.

L'hypothèse 2 est renforcée par le résultat de l'époque suivante, puisque la PR-AUC redevient meilleure qu'avant la régression (0,4785 à l'époque 7).

La sélection sur la meilleure PR-AUC protège le modèle livré : on garde l'époque qui a donné le meilleur résultat sur des images neuves (ici l'époque 8), pas simplement la dernière, donc un recul de fin d'entraînement ne serait pas livré.

## Mesure 8 — reprise après coupure

| Relevé | Valeur |
|---|---|
| Époque pendant laquelle j'ai interrompu | 2 (environ 20 s après son début) |
| Ligne affichée au redémarrage | `reprise a l'epoque 2` |
| Époques recalculées en double | 0 (l'époque 1, terminée, n'est pas refaite ; l'époque 2, non terminée, repart de zéro) |
| Taille du point de reprise (`reprise.pt`) | 89 579 657 octets |

Écart : Python ignore Ctrl+C lancé en arrière-plan. La coupure a été faite avec SIGTERM (même effet : arrêt sans sauvegarde de l'époque en cours). Une première tentative, sans effet, a été recommencée de zéro.

## Mesure 9 — latence du réseau seul, lot de 1

| Dispositif | p50 (ms) | p95 (ms) |
|---|---|---|
| CPU | 14,3 | 16,4 |
| GPU (si disponible) | non disponible | non disponible |

## Question 3.4

En cas de surentrainement on reprend le meilleur état rencontré et pas juste le dernier. Il est donc nécessaire de sauvegarder ce meilleur état en cas de redémarrage pour ne pas "perdre" cette avancée si jamais le redémarrage a lieu alors que le modèle est déjà surentrainé.
On garde aussi l'état du générateur en mémoire, sans quoi on retournerait aux premiers aléatoires de la seed (42) après le redémarrage : l'époque reprise referait les mêmes tirages que l'époque 1, et l'entraînement ne serait plus identique à celui qui n'aurait jamais été interrompu, brisant la reproductibilité.

## Question 3.5

La force du GPU est de pouvoir calculer de nombreuses unités en parallèle, alors que le CPU en calcule quelques-unes très rapidement. Une prédiction unitaire n'est donc pas accélérée autant que l'entraînement : ce qui augmente avec un GPU, c'est le nombre d'unités traitées en parallèle (un lot de 64 images à l'entraînement), pas la vitesse d'une seule. Servir ce modèle n'exige pas un GPU, mais il rend permet traiter un batch de 64 images bien plus rapidement.
## Mesure 10 — vérification du paquet rapatrié

| Relevé | Valeur |
|---|---|
| Nombre de contrôles OK / total, et verdict | 13 / 13, RENDU RECEVABLE |
| Contrôles « SAUTE » | aucun |
| `sha256` de `modele.pt` (16 premiers caractères), égalité avec `sha256_poids` | `48f9d0e99950da7b`, égal au début de `sha256_poids` |
| Taille de `modele.pt` | 44 780 171 octets |
| `isic_id` et `probabilite_maligne` du bloc `controle` | ISIC_0104229, 0,062464 |

Entraînement fait en local (pas de Colab) : le paquet n'a pas été rapatrié, il était déjà sur le poste.

## Question 3.6

Un notebook se partage : si je mets mon secret Azure dans une cellule, toute personne qui reçoit le notebook peut le voir. De plus, le paquet contient déjà tout ce qu'il faut (poids, métadonnées, manifeste, empreintes) et se vérifie sur mon poste : Colab n'a aucune raison de détenir un accès à Azure, et l'image Docker est construite sur mon poste, c'est donc de là qu'on la pousse en gardant mes identifiants privés en local.
