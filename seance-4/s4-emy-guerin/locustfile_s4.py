import os

from locust import HttpUser, between, task

# Image de controle lue une seule fois, au chargement du module
with open(os.environ["IMAGE_CONTROLE_S4"], "rb") as f:
    IMAGE = f.read()


class Dermatologue(HttpUser):
    wait_time = between(2, 5)  # celui de S3

    @task(10)
    def predire(self):
        with self.client.post(
            "/predict",
            files={"image": ("controle.jpg", IMAGE, "image/jpeg")},
            name="POST /predict",
            catch_response=True,
        ) as reponse:
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
