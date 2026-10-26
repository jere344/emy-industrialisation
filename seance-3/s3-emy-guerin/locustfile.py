import json
import random

from locust import HttpUser, between, task

# charge.json de S2, chargé une seule fois au démarrage du module
with open("charge.json", encoding="utf-8") as f:
    CHARGE_BASE = json.load(f)

# (variable, amplitude, minimum, maximum) : plages observées en S2
PERTURBATIONS = [
    ("age_approx", 5.0, 5.0, 85.0),
    ("clin_size_long_diam_mm", 0.10, 1.0, 28.4),  # amplitude relative (±10 %)
    ("tbp_lv_A", 1.0, -2.49, 48.19),
    ("tbp_lv_B", 1.0, -0.73, 54.31),
]


def charge_utile_perturbee():
    charge = dict(CHARGE_BASE)
    for nom, amplitude, bas, haut in PERTURBATIONS:
        if nom == "clin_size_long_diam_mm":
            valeur = charge[nom] * (1 + random.uniform(-amplitude, amplitude))
        else:
            valeur = charge[nom] + random.uniform(-amplitude, amplitude)
        charge[nom] = round(min(max(valeur, bas), haut), 5)
    return charge


class Dermatologue(HttpUser):
    wait_time = between(2, 5)

    @task(10)
    def predire(self):
        with self.client.post("/predict", json=charge_utile_perturbee(),
                              name="POST /predict", catch_response=True) as reponse:
            if reponse.status_code == 200:
                reponse.success()
            else:
                reponse.failure(f"statut {reponse.status_code}")

    @task(2)
    def sante(self):
        self.client.get("/health", name="GET /health")

    @task(1)
    def info_modele(self):
        self.client.get("/model/info", name="GET /model/info")
