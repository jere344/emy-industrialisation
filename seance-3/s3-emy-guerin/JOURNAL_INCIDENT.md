# JOURNAL_INCIDENT — Séance 3

## 4.1 — Journalisation et flux de logs

Journalisation activée à 14:55:50 : `az webapp log config --docker-container-logging filesystem --application-logging filesystem --level information`. L'activation a provoqué un recyclage du conteneur (nouveau conteneur démarré à 13:56:45 UTC, prêt à 13:57:51 UTC après 65 s de sonde de démarrage, ancien conteneur arrêté à 13:58:12 UTC).

Trafic généré à 14:56:10 puis à 14:57:53 et 14:58:44 (heure locale) : un `GET /health` (200), un `GET /model/info` (200) et un `POST /predict` incomplet `-d '{"age_approx": 55}'` (400, corps : `{"error":"colonnes manquantes","manquantes":[...]}`).

**Mesure 9** — ce que le flux de logs de la plateforme laisse réellement voir, charge utile comprise.

| Observation dans le flux de logs | Votre relevé |
|---|---|
| Le nom du conteneur apparaît-il en préfixe de chaque ligne ? | Non. Les lignes de la plateforme nomment le conteneur dans leur texte (`Starting container: c4e220e5edd2_dermascan-eg08`), mais les lignes de l'application (Gunicorn) ne portent qu'un horodatage UTC, sans nom de conteneur. Seul un ancien conteneur est signalé par le préfixe `[Previous Container]`. |
| Retrouve-t-on la ligne d'accès de Gunicorn pour chaque requête ? | Non : aucune ligne d'accès pour mes trois requêtes. Le journal de l'application ne contient que les lignes de démarrage de Gunicorn (`Starting gunicorn`, `Listening at: http://0.0.0.0:8000`, `Using worker: sync`, `Booting worker`). |
| Que journalise votre API sur un `/predict` incomplet ? | Rien : aucune ligne n'apparaît pour la requête incomplète. |
| La liste des variables manquantes apparaît-elle dans les logs ? | Non : elle n'est que dans le corps de la réponse HTTP 400, pas dans les logs. |
| Délai approximatif entre la requête et l'apparition de sa ligne | Non mesurable : aucune ligne n'apparaît pour ces requêtes. (Les lignes de la plateforme, elles, apparaissent dans le flux avec quelques secondes de décalage.) |
| La charge utile complète du `POST` apparaît-elle dans les logs ? | Non. |

Autre ligne relevée au démarrage de Gunicorn : `[ERROR] Control server error: [Errno 13] Permission denied: '/home/appuser'` (le service fonctionne malgré tout).

## 4.2 — Compte rendu d'incident : panne provoquée du démarrage

**Symptôme.** Après `WEBSITES_PORT=9999` (posé à 15:03:37) et `az webapp restart` (15:03:39), `/health` ne répond plus : sondé toutes les 30 s avec `curl -m 60`, le client voit d'abord `code=000 duree=60.00s` (délai dépassé), puis `503` à partir de 15:08:39 (`duree=33.57s`), puis `503` et `000` en alternance jusqu'à la correction.

**Ligne de log fautive** (extraite du flux de la plateforme, journal `docker.log` de l'archive) :

```
2026-10-26T14:09:05.9867218Z Site startup probe failed after 230.0452433 seconds.
LastErrorDetails: Container did not respond to startup probe on port 9999 within the expected time limit of 230s. Port mismatch detected: the container is listening on port 8000 but the platform is probing port 9999. Set the WEBSITES_PORT app setting to match the port your application listens on. If your application needs more time to start, increase WEBSITES_CONTAINER_START_TIME_LIMIT. Please inspect your container logs for more details as this could indicate an issue with your application.
```

**Cause.** `WEBSITES_PORT` (port que la plateforme sonde) ne correspondait plus au port d'écoute réel de Gunicorn (`PORT=8000`) : la plateforme frappait sur le port 9999, où personne n'écoute.

**Correction.** `az webapp config appsettings set --settings WEBSITES_PORT="8000"` à 15:18:05, sans redémarrage explicite.

**Délai de retour au service.** 202 s (premier `200` à 15:21:27).

**Mesure 10** — diagnostic de la panne provoquée : code vu du client, ligne de log fautive, nombre de tentatives.

| Élément du diagnostic | Votre relevé |
|---|---|
| Code HTTP vu par le client | `000` (délai client de 60 s dépassé) pendant les 5 premières minutes, puis `503` en alternance avec `000` |
| Délai avant la réponse d'erreur | environ 5 min (premier `503` à 15:08:39, soit 5 min après le redémarrage) ; le `503` lui-même a mis 33.57 s à répondre |
| **Ligne de log exacte** qui nomme la cause, recopiée intégralement | voir le bloc ci-dessus |
| Combien de fois la plateforme a-t-elle retenté avant d'abandonner ? | Au moins 2 tentatives de démarrage relevées, chacune de 230 s : conteneur `5921c87fe211` démarré à 14:05:15 UTC (sonde en échec à 14:09:05), puis conteneur `6f1f8e4388c3` démarré à 14:10:09 UTC (sonde en échec à 14:14:00). La plateforme n'a pas « abandonné » dans la fenêtre observée : elle a continué à relancer le démarrage. |
| Le processus applicatif a-t-il démarré, oui ou non ? | Oui : dans chaque tentative, Gunicorn a démarré (`Starting gunicorn`, `Listening at: http://0.0.0.0:8000`, `Booting worker`). L'application fonctionnait, c'est la plateforme qui sondait le mauvais port. |
| Temps écoulé entre le redémarrage et la ligne fautive | 14:03:39 UTC → 14:09:05 UTC, soit environ 5 min 26 s (dont 230 s de sonde de démarrage) |

**Mesure 11** — délai de retour au service après correction.

| Élément | Votre relevé |
|---|---|
| Durée entre la correction et le premier `200` | `202 s` (15:18:05 → 15:21:27) |
| A-t-il fallu un redémarrage explicite, ou la plateforme a-t-elle repris seule ? | Aucun redémarrage explicite : la plateforme a repris seule, le changement du réglage a recyclé le conteneur. |

## Question 4.1

**Question 4.1** — Le code HTTP vu par le client est le même que celui que vous aviez relevé en partie 2.2, avant d'accorder le rôle sur le registre. Les deux causes n'ont pourtant rien à voir. Répondez à ces trois questions dans `JOURNAL_INCIDENT.md` :

1. Qu'est-ce qui distingue les deux cas **du point de vue du client** ? Si rien, dites-le.
2. Qu'est-ce qui les distingue **dans les logs** ? Citez pour chaque cas la ligne discriminante.
3. Quelle conclusion en tirez-vous sur la valeur d'un code HTTP comme élément de diagnostic ?

> 1. Rien, même erreur HTTP générique.
> 2. Dans le 1er cas les logs indiquent "Failed to pull image: dermascaneg08.azurecr.io/dermascan-api:1.0.1. Image pull failed with forbidden or unauthorized. Check registry credentials.", dans le 2ème cas ils indiquent "Container did not respond to startup probe on port 9999 within the expected time limit of 230s. Port mismatch detected: the container is listening on port 8000 but the platform is probing port 9999…"
> 3. Le code HTTP seul n'est pas suffisant pour faire un diagnostic, alors que les logs nous permettent de viser bien plus exactement la source du problème.

## 4.3 — Métriques de plateforme

Relevé à 15:26 (heure locale) avec `az monitor metrics list --resource "$APP_ID" --metric Requests Http5xx HttpResponseTime --interval PT1H`, sur l'heure écoulée, incident de 4.2 compris.

**Mesure 12** — métriques agrégées de la plateforme sur l'heure écoulée.

| Métrique | Votre relevé sur l'heure écoulée |
|---|---|
| Nombre total de requêtes | `83` |
| Nombre de réponses `5xx` | `14` |
| Temps de réponse moyen | `32.92 s` (moyenne pondérée, tirée vers le haut par les requêtes de l'incident qui atteignaient 30 à 60 s) |

**Question 4.2** — Ces métriques suffisent-elles à répondre à « mon service est-il lent pour mes utilisateurs ? » Justifiez en une phrase, en vous appuyant sur ce que vous allez mesurer en partie 5. La réponse tient en un mot, et ce mot n'est pas « moyenne ».

> Ces métriques ne suffisent pas à répondre à cette question, pour obtenir une vraie idée de l'expérience utilisateur il faut prendre en compte les cas extrêmes (ici les périodes d'indisponibilité de nos tests précédents), et pour cela on utilise les percentiles, soit le p50 (médiane), p95 et p99.
