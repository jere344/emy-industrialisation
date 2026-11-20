# JOURNAL - Séance 6

## Tableau de décisions (2026-11-20)

| Décision | Contrainte | Ma valeur |
|---|---|---|
| Métrique d'arbitrage entre deux approches | calculée par `entrainer_suivi.py` | Précision au rappel cible (90 %) : Utiliser la PR-AUC comme métrique entraine des résultats plus efficaces dans certains cas et divers avantage. On peut par exemple viser une certaine flexibilité de notre seuil selon l'occupation de l'hopital : Un hopital libre peut appliquer un seuil plus faible car il peuvent se permettre de travailler légèrement plus pour une meilleure détection, alors qu'un hôpital sous l'eau va augmenter son seuil afin de d'utiliser le plus efficacement leurs ressources limités. Cependant ce n'est pas l'utilisation que nous avons définie de notre modèle, ce qui nous importe va être la meilleure précision dans le choix de notre système entre bénin et malin, ainsi seul notre propre seuil est important et se retranscrira dans une utilisation réelle en production. |
| Écart minimal pour déclarer une approche meilleure | à confronter au bruit (partie 1.4) | ≥ 5 % relatif **et** supérieur à la variation entre graines de chaque approche |
| Critère de départage si l'écart est sous le bruit | une grandeur que le run enregistre | la PR-AUC, justement pour le cas où les médecins utilisent leurs propres seuils. Même si non supporté officiellement par notre système, c'est une possibilité donc bien de le supporter. |
| Nom du validateur au registre | une personne, pas un rôle | Emy GUERIN |

> **Ajout APRÈS la question 1.4 (après observation des métriques des 4 runs)** - critères de départage supplémentaires, dans l'ordre, après la PR-AUC : 3. stabilité entre graines ; 4. temps d'entraînement. Ils ne faisaient pas partie des décisions prises avant la première mesure.

## Question 0.1

Un écart supérieur à notre écart minimal décidé plus haut sera une victoire. Cela correspond à un écart qui ne peut pas être confondu avec du bruit et est suffisamment significatif pour justifier une mise en production.
