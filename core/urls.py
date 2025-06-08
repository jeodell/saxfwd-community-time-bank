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
        "services/<int:pk>/", views.ServiceDetailView.as_view(), name="service_detail"
    ),
    path(
        "services/<int:pk>/request/",
        views.ServiceRequestView.as_view(),
        name="service_request",
    ),
    path("requests/", views.RequestListView.as_view(), name="request_list"),
    path(
        "requests/<int:pk>/", views.RequestDetailView.as_view(), name="request_detail"
    ),
    path(
        "requests/<int:pk>/accept/",
        views.RequestAcceptView.as_view(),
        name="request_accept",
    ),
    path(
        "requests/<int:pk>/reject/",
        views.RequestRejectView.as_view(),
        name="request_reject",
    ),
    path(
        "requests/<int:pk>/complete/",
        views.RequestCompleteView.as_view(),
        name="request_complete",
    ),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("ledger/", views.LedgerView.as_view(), name="ledger"),
    path(
        "requests/<int:pk>/community/",
        views.RequestCommunityHoursView.as_view(),
        name="request_community_hours",
    ),
    path(
        "requests/<int:pk>/community/approve/",
        views.ApproveCommunityRequestView.as_view(),
        name="approve_community_request",
    ),
    path(
        "requests/<int:pk>/community/reject/",
        views.RejectCommunityRequestView.as_view(),
        name="reject_community_request",
    ),
]
