from django.urls import path

from core.views.request import (
    ApproveCommunityRequestView,
    RejectCommunityRequestView,
    RequestAcceptView,
    RequestCancelFormView,
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
    path("", RequestListView.as_view(), name="request_list"),
    path("<uuid:pk>/", RequestDetailView.as_view(), name="request_detail"),
    path(
        "<uuid:pk>/accept/",
        RequestAcceptView.as_view(),
        name="request_accept",
    ),
    path(
        "<uuid:pk>/reject/",
        RequestRejectView.as_view(),
        name="request_reject",
    ),
    path(
        "<uuid:pk>/reject-form/",
        RequestRejectFormView.as_view(),
        name="request_reject_form",
    ),
    path(
        "<uuid:pk>/cancel/",
        RequestCancelView.as_view(),
        name="request_cancel",
    ),
    path(
        "<uuid:pk>/cancel-form/",
        RequestCancelFormView.as_view(),
        name="request_cancel_form",
    ),
    path(
        "<uuid:pk>/complete/",
        RequestCompleteFormView.as_view(),
        name="request_complete_form",
    ),
    path(
        "<uuid:pk>/complete-action/",
        RequestCompleteView.as_view(),
        name="request_complete",
    ),
    path(
        "<uuid:pk>/community/",
        RequestCommunityHoursView.as_view(),
        name="request_community_hours",
    ),
    path(
        "<uuid:pk>/community/approve/",
        ApproveCommunityRequestView.as_view(),
        name="approve_community_request",
    ),
    path(
        "<uuid:pk>/community/reject/",
        RejectCommunityRequestView.as_view(),
        name="reject_community_request",
    ),
]
