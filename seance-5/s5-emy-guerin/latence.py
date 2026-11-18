"""Boucle de latence de S4 : 5 appels de chauffe, 50 mesures sur /predict (image de controle), p50 / p95."""
import sys, time, statistics, requests
url, image = sys.argv[1], sys.argv[2]
octets = open(image, "rb").read()
s = requests.Session()
appel = lambda: s.post(f"{url}/predict", files={"image": ("c.jpg", octets, "image/jpeg")}).raise_for_status()
for _ in range(5):
    appel()
d = []
for _ in range(50):
    t0 = time.perf_counter(); appel(); d.append((time.perf_counter() - t0) * 1000)
q = statistics.quantiles(d, n=100)
print(f"{url} : p50 {q[49]:.1f} ms / p95 {q[94]:.1f} ms (50 appels)")
