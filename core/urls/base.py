from django.urls import path

from core.views.base import AboutView, ContactView, HomeView, RegisterView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("accounts/register/", RegisterView.as_view(), name="register"),
]
