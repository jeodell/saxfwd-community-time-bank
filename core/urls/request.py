from django.urls import path

from core.views.request import (
    ApproveCommunityRequestView,
    RejectCommunityRequestView,
    RequestAcceptView,
    RequestCancelView,
    RequestCommunityHoursView,
    RequestCompleteFormView,
    RequestCompleteView,
    RequestDetailView,
    RequestListView,
    RequestRejectFormView,
    RequestRejectView,
)

urlpatterns = [
    path("requests/", RequestListView.as_view(), name="request_list"),
    path("requests/<uuid:pk>/", RequestDetailView.as_view(), name="request_detail"),
    path(
        "requests/<uuid:pk>/accept/",
        RequestAcceptView.as_view(),
        name="request_accept",
    ),
    path(
        "requests/<uuid:pk>/reject/",
        RequestRejectView.as_view(),
        name="request_reject",
    ),
    path(
        "requests/<uuid:pk>/reject-form/",
        RequestRejectFormView.as_view(),
        name="request_reject_form",
    ),
    path(
        "requests/<uuid:pk>/cancel/",
        RequestCancelView.as_view(),
        name="request_cancel",
    ),
    path(
        "requests/<uuid:pk>/complete/",
        RequestCompleteFormView.as_view(),
        name="request_complete_form",
    ),
    path(
        "requests/<uuid:pk>/complete-action/",
        RequestCompleteView.as_view(),
        name="request_complete",
    ),
    path(
        "requests/<uuid:pk>/community/",
        RequestCommunityHoursView.as_view(),
        name="request_community_hours",
    ),
    path(
        "requests/<uuid:pk>/community/approve/",
        ApproveCommunityRequestView.as_view(),
        name="approve_community_request",
    ),
    path(
        "requests/<uuid:pk>/community/reject/",
        RejectCommunityRequestView.as_view(),
        name="reject_community_request",
    ),
]
