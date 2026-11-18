# Lanceur : meme scenario que locustfile_s4.py, seul trust_env est remis a True pour passer
# par le proxy HTTP de l'environnement (meme ecart qu'en S4).
from locustfile_s4 import Dermatologue
Dermatologue.on_start = lambda self: setattr(self.client, "trust_env", True)
