from django.urls import path

from core.views.base import (
    ApplicationReviewDetailView,
    ApplicationReviewListView,
    MarkUserOrientationCompletedView,
)

urlpatterns = [
    path(
        "applications/",
        ApplicationReviewListView.as_view(),
        name="application_review_list",
    ),
    path(
        "applications/<uuid:application_id>/",
        ApplicationReviewDetailView.as_view(),
        name="application_review_detail",
    ),
    path(
        "users/<uuid:user_id>/mark-orientation-completed/",
        MarkUserOrientationCompletedView.as_view(),
        name="mark_user_orientation_completed",
    ),
]
