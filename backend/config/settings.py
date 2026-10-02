"""Configuracao do projeto Pauta (Django + DRF)."""
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(chave, padrao=""):
    return os.environ.get(chave, padrao)


def env_bool(chave, padrao=False):
    return str(env(chave, str(padrao))).strip().lower() in {"1", "true", "yes", "on"}


def env_list(chave, padrao=""):
    return [item.strip() for item in env(chave, padrao).split(",") if item.strip()]


SECRET_KEY = env("SECRET_KEY", "dev-inseguro-somente-para-desenvolvimento")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1") or ["localhost", "127.0.0.1"]
SITE_URL = env("SITE_URL", "http://localhost:5173").rstrip("/")
SITE_NAME = env("SITE_NAME", "Pauta")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # terceiros
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # aplicacoes do projeto
    "apps.core",
    "apps.users",
    "apps.categories",
    "apps.news",
    "apps.comments",
    "apps.interactions",
    "apps.notifications",
    "apps.analytics",
    "apps.coleta",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if env("DB_ENGINE", "postgres") == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "pauta"),
            "USER": env("DB_USER", "postgres"),
            "PASSWORD": env("DB_PASSWORD", "postgres"),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------- DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticatedOrReadOnly",),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.PaginacaoPadrao",
    "PAGE_SIZE": 12,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "EXCEPTION_HANDLER": "apps.core.exceptions.tratar_excecao",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "20/min",
        "escrita": "60/min",
        "busca": "120/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Pauta API",
    "DESCRIPTION": "API REST da plataforma de noticias Pauta.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ---------------------------------------------------------------- CORS
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# ---------------------------------------------------------------- Cache
# Com REDIS_URL o cache fica compartilhado entre o Django, o worker e o beat do Celery
# (necessario para o carrossel atualizar na hora em producao; a trava da coleta nao
# depende mais do cache, ver COLETA_TRAVA_BACKEND).
REDIS_URL = env("REDIS_URL", "")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "KEY_PREFIX": "pauta",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "pauta-cache",
        }
    }

# ---------------------------------------------------------------- Celery (coleta agendada)
COLETA_INTERVALO_MINUTOS = int(env("COLETA_INTERVALO_MINUTOS", "5"))

CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", "") or None
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
# arquivo onde o beat guarda a ultima execucao: e o que faz o agendamento continuar do
# ponto certo depois de reiniciar (em container, aponte para um volume persistente)
CELERY_BEAT_SCHEDULE_FILENAME = env(
    "CELERY_BEAT_SCHEDULE_FILENAME", str(BASE_DIR / "celerybeat-schedule"))
CELERY_BEAT_SCHEDULE = {
    "coletar-noticias": {
        "task": "apps.coleta.tasks.coletar_noticias",
        "schedule": timedelta(minutes=COLETA_INTERVALO_MINUTOS),
        # se o worker ficar fora do ar, a tarefa vencida e descartada (nao acumula fila)
        "options": {"expires": max(COLETA_INTERVALO_MINUTOS * 60 - 60, 60)},
    },
}

# ---------------------------------------------------------------- Coleta de noticias
COLETA_USUARIO = env("COLETA_USUARIO", "coleta-automatica")
COLETA_NOME_AUTOR = env("COLETA_NOME_AUTOR", "Agregador Pauta")
COLETA_USER_AGENT = env("COLETA_USER_AGENT", f"PautaBot/1.0 (+{SITE_URL})")
COLETA_TIMEOUT_CONEXAO = float(env("COLETA_TIMEOUT_CONEXAO", "5"))
COLETA_TIMEOUT_LEITURA = float(env("COLETA_TIMEOUT_LEITURA", "20"))
COLETA_TAMANHO_MAXIMO_MB = float(env("COLETA_TAMANHO_MAXIMO_MB", "5"))
COLETA_IDADE_MAXIMA_DIAS = int(env("COLETA_IDADE_MAXIMA_DIAS", "7"))
COLETA_RETENCAO_LOGS_DIAS = int(env("COLETA_RETENCAO_LOGS_DIAS", "30"))
COLETA_PONTUACAO_MINIMA = int(env("COLETA_PONTUACAO_MINIMA", "2"))
# trava contra coletas simultaneas: auto | banco (PostgreSQL) | arquivo | cache (ver apps/coleta/trava.py)
COLETA_TRAVA_BACKEND = env("COLETA_TRAVA_BACKEND", "auto")
COLETA_TRAVA_ARQUIVO = env("COLETA_TRAVA_ARQUIVO", str(BASE_DIR / ".coleta.lock"))
COLETA_TRAVA_SEGUNDOS = int(env("COLETA_TRAVA_SEGUNDOS", str(30 * 60)))  # so p/ backend "cache"
# ao iniciar o beat sem historico, coleta na hora se a ultima coleta tiver mais de 40 min
COLETA_EXECUTAR_AO_INICIAR = env_bool("COLETA_EXECUTAR_AO_INICIAR", True)
# so ligue em desenvolvimento, para testar com um feed servido na sua propria maquina
COLETA_PERMITIR_REDE_INTERNA = env_bool("COLETA_PERMITIR_REDE_INTERNA", False)
CARROSSEL_CACHE_SEGUNDOS = int(env("CARROSSEL_CACHE_SEGUNDOS", "60"))

# Faixa "Urgente" do topo: alem das noticias marcadas como urgentes, mostra sozinha as
# ultimas noticias publicadas (inclusive as coletadas) das ultimas URGENTE_JANELA_HORAS.
URGENTE_AUTOMATICO = env_bool("URGENTE_AUTOMATICO", True)
URGENTE_JANELA_HORAS = int(env("URGENTE_JANELA_HORAS", "6"))
URGENTE_MAXIMO = int(env("URGENTE_MAXIMO", "5"))

# ---------------------------------------------------------------- E-mail
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "nao-responda@pauta.local")

# ---------------------------------------------------------------- Seguranca
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simples": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simples"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "apps.coleta": {
            "handlers": ["console"],
            "level": env("COLETA_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# log da coleta tambem em arquivo, com rotacao (opcional)
if env("COLETA_LOG_ARQUIVO"):
    LOGGING["handlers"]["arquivo_coleta"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": env("COLETA_LOG_ARQUIVO"),
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 5,
        "encoding": "utf-8",
        "formatter": "simples",
    }
    LOGGING["loggers"]["apps.coleta"]["handlers"].append("arquivo_coleta")
