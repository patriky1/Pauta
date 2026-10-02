# Imagem do backend (API + worker + beat da coleta). Usada pelo docker-compose.yml da raiz.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# arquivos estaticos do admin/API servidos pelo WhiteNoise
RUN SECRET_KEY=somente-para-o-build python manage.py collectstatic --noinput \
    && useradd --create-home --uid 1000 pauta \
    && mkdir -p /app/media /data/beat \
    && chown -R pauta:pauta /app /data

USER pauta
EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
