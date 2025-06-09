from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("services/", views.ServiceListView.as_view(), name="service_list"),
    path("services/create/", views.ServiceCreateView.as_view(), name="service_create"),
    path(
        "services/<uuid:pk>/",
        views.ServiceDetailView.as_view(),
        name="service_detail",
    ),
    path(
        "services/<uuid:pk>/request/",
        views.ServiceRequestView.as_view(),
        name="service_request",
    ),
    path("requests/", views.RequestListView.as_view(), name="request_list"),
    path(
        "requests/<uuid:pk>/", views.RequestDetailView.as_view(), name="request_detail"
    ),
    path(
        "requests/<uuid:pk>/accept/",
        views.RequestAcceptView.as_view(),
        name="request_accept",
    ),
    path(
        "requests/<uuid:pk>/reject/",
        views.RequestRejectView.as_view(),
        name="request_reject",
    ),
    path(
        "requests/<uuid:pk>/complete/",
        views.RequestCompleteView.as_view(),
        name="request_complete",
    ),
    path("users/me/", views.UserView.as_view(), name="user_me"),
    path("users/me/edit/", views.UserEditView.as_view(), name="user_me_edit"),
    path("users/<uuid:pk>/", views.UserView.as_view(), name="user"),
    path("users/<uuid:pk>/edit/", views.UserEditView.as_view(), name="user_edit"),
    path("ledger/", views.LedgerView.as_view(), name="ledger"),
    path(
        "requests/<uuid:pk>/community/",
        views.RequestCommunityHoursView.as_view(),
        name="request_community_hours",
    ),
    path(
        "requests/<uuid:pk>/community/approve/",
        views.ApproveCommunityRequestView.as_view(),
        name="approve_community_request",
    ),
    path(
        "requests/<uuid:pk>/community/reject/",
        views.RejectCommunityRequestView.as_view(),
        name="reject_community_request",
    ),
]
