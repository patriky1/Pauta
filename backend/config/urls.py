"""Rotas raiz do projeto."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import robots_txt, sitemap_noticias

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls_auth")),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.categories.urls")),
    path("api/", include("apps.news.urls")),
    path("api/", include("apps.comments.urls")),
    path("api/", include("apps.interactions.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.analytics.urls")),
    # documentacao
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # SEO
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap_noticias, name="sitemap"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
