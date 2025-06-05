from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("services/", views.service_list, name="service_list"),
    path("services/create/", views.service_create, name="service_create"),
    path("services/<int:pk>/", views.service_detail, name="service_detail"),
    path("services/<int:pk>/request/", views.service_request, name="service_request"),
    path("requests/", views.request_list, name="request_list"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/accept/", views.request_accept, name="request_accept"),
    path("requests/<int:pk>/reject/", views.request_reject, name="request_reject"),
    path(
        "requests/<int:pk>/complete/", views.request_complete, name="request_complete"
    ),
    path("profile/", views.profile, name="profile"),
    path("profile/<str:username>/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("ledger/", views.ledger, name="ledger"),
]
