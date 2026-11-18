FROM cgr.dev/chainguard/wolfi-base:latest
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN apk add --no-cache python-3.12 py3.12-pip libstdc++ libgomp \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del --no-cache py3.12-pip

COPY model/modele.pt model/modele_meta.json ./model/
COPY app.py ./
RUN adduser -D -u 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "exec python -m gunicorn -b 0.0.0.0:${PORT:-8000} app:app"]
