from django.urls import path

from core.views.ledger import LedgerView

urlpatterns = [
    path("ledger/", LedgerView.as_view(), name="ledger"),
]
