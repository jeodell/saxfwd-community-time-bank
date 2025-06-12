from django.urls import include, path

urlpatterns = [
    path("", include("core.urls.base")),
    path("", include("core.urls.service")),
    path("", include("core.urls.request")),
    path("", include("core.urls.user")),
    path("", include("core.urls.ledger")),
]
