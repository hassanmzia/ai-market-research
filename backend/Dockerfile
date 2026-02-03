FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput 2>/dev/null || true
EXPOSE 8063
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py create_default_admin 2>/dev/null; uvicorn config.asgi:application --host 0.0.0.0 --port 8063"]
