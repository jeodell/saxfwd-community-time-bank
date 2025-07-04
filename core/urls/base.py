from django.urls import path

from core.views.base import (
    AboutView,
    ApplicationSubmittedView,
    ApplicationView,
    HomeView,
    PasswordSetupView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("accounts/apply/", ApplicationView.as_view(), name="apply"),
    path(
        "accounts/application-submitted/",
        ApplicationSubmittedView.as_view(),
        name="application_submitted",
    ),
    path(
        "accounts/password-setup/", PasswordSetupView.as_view(), name="password_setup"
    ),
]
