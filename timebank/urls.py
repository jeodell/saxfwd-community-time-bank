from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Non-internationalized URLs
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

# Internationalized URLs
urlpatterns += i18n_patterns(
    path("timebank-admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("core.urls.base")),
    path("services/", include("core.urls.service")),
    path("requests/", include("core.urls.request")),
    path("users/", include("core.urls.user")),
    path("community/", include("core.urls.community")),
    path("admin/", include("core.urls.admin")),
    prefix_default_language=False,
)

# Serve static and media files in development only
if settings.DEBUG and not settings.USE_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
