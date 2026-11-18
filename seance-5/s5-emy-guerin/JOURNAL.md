# JOURNAL — Séance 5

## Tableau de décisions (2026-11-17)

| Décision | Contrainte | Ma valeur |
|---|---|---|
| Suffixe personnel | identique à S1 | `EG08` |
| Écart max. de probabilité, « même modèle » | ONNX contre PyTorch | 10⁻⁵ |
| Rappel minimal d'une variante | au seuil servi | 0,88 (52/59) |
| Décisions changées max., même version | entier | 0 |
| Covariable surveillée en priorité | reçue par l'API | `tbp_tile_type` : il faut s'assurer que le matériel de prise de photo ne change pas par rapport à l'entraînement |
| Statistique de dérive | calculée par `derive.py` | PSI |
| Seuil d'**alerte** du PSI | avant la mesure | 0,25 |
| Seuil de **surveillance** du PSI | sous l'alerte | 0,1 |
| Fenêtre glissante | en inférences | 200 |
| Levier de dérive provoquée | `eclairage`, `age`, `site` | `eclairage` : c'est celui qui est le plus susceptible de poser problème et d'être critique (résultats faussés) dans un contexte réel |

## Question 0.1

Le seuil d'alerte doit être fixé avant de regarder les mesures de dérive, sinon l'analyste sera tenté d'ajuster ses chiffres selon ces mesures (par exemple 0,2 si le PSI monte à 0,18 en flux conforme et à 0,22 en dérive).
Cela pourrait masquer des comportements réels et donner une fausse sécurité.

## Question 0.2

La surveillance est nécessaire au système : sans elle, il y a un risque de donner des résultats faussés, avec des conséquences réelles sur la santé du patient. Sacrifier la quantization est bien moins risqué : le risque est un ralentissement ou un plantage du système, ou une simple augmentation des coûts, ce qui a des conséquences bien moins importantes.
