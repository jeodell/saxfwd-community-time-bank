from django.urls import path

from core.views.ledger import CommunityView, DonateCommunityHoursView

urlpatterns = [
    path("", CommunityView.as_view(), name="community"),
    path("donate/", DonateCommunityHoursView.as_view(), name="donate_community_hours"),
]
