FROM python:3.14-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
RUN useradd -u 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8089

CMD ["python", "app.py"]