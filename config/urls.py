"""Top-level URL routing."""

from django.http import HttpResponse
from django.urls import include, path, re_path
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def frontend(request):
    """Serve the SvelteKit single-page application entry point."""
    content = (settings.BASE_DIR / "frontend" / "build" / "index.html").read_bytes()
    return HttpResponse(content, content_type="text/html")

urlpatterns = [
    path("v1/", include("api.urls")),
    path("health", include("api.health_urls")),
    path("openapi.json", SpectacularAPIView.as_view(), name="schema"),
    path("docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    re_path(r"^(?!static/).*$", frontend),
]
