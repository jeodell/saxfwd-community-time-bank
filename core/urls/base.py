from django.urls import path

from core.views.base import AboutView, HomeView, RegisterView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("accounts/register/", RegisterView.as_view(), name="register"),
]
