from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("timebank-admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("core.urls.base")),
    path("services/", include("core.urls.service")),
    path("requests/", include("core.urls.request")),
    path("users/", include("core.urls.user")),
    path("community/", include("core.urls.community")),
    path("admin/", include("core.urls.admin")),
]

# Serve static and media files in development only
if settings.DEBUG and not settings.USE_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
