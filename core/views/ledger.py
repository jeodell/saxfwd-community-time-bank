from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import ListView, View

from ..models import CommunityHours, TimeBankLedger


class LedgerView(ListView):
    model = TimeBankLedger
    template_name = "core/ledger.html"
    context_object_name = "transactions"
    paginate_by = 50  # Show 50 transactions per page

    def get_queryset(self):
        # Get all transactions and order by created_at
        transactions = TimeBankLedger.objects.all().order_by("-created_at")

        # Group transactions by service request or create_at for non-service transactions
        grouped_transactions = {}
        for transaction in transactions:
            key = transaction.service_request_id or f"direct_{transaction.id}"
            if key not in grouped_transactions:
                grouped_transactions[key] = {
                    "created_at": transaction.created_at,
                    "service_request": transaction.service_request,
                    "hours": transaction.hours,
                    "description": transaction.service_request.service.title
                    if transaction.service_request
                    and transaction.service_request.service
                    else transaction.description,
                    "from_user": transaction.service_request.requester
                    if transaction.service_request
                    else (
                        transaction.user
                        if transaction.transaction_type == "community_donation"
                        else None
                    ),
                    "to_user": transaction.service_request.service.provider
                    if transaction.service_request
                    and transaction.service_request.service
                    else (
                        "Community"
                        if transaction.transaction_type == "community_donation"
                        else None
                    ),
                }

        # Convert the grouped transactions to a list and sort by date
        return sorted(
            grouped_transactions.values(), key=lambda x: x["created_at"], reverse=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_transactions"] = len(self.get_queryset())
        context["total_hours_exchanged"] = sum(t["hours"] for t in self.get_queryset())

        # Get community hours balance
        community_hours, _ = CommunityHours.objects.get_or_create()
        context["community_hours_balance"] = community_hours.total_hours

        # Add user's time balance if authenticated
        if self.request.user.is_authenticated:
            context["user_time_balance"] = self.request.user.time_balance

        return context


class DonateCommunityHoursView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            hours = Decimal(request.POST.get("hours", "0"))
            description = request.POST.get("description", "Community Hours Donation")

            if hours <= 0:
                messages.error(
                    request, "Please enter a positive number of hours to donate."
                )
                return redirect("ledger")

            # Check if user has enough hours
            user_balance = request.user.time_balance
            if user_balance < hours:
                messages.error(
                    request, "You don't have enough hours to make this donation."
                )
                return redirect("ledger")

            # Create ledger entry for the donation
            TimeBankLedger.objects.create(
                user=request.user,
                transaction_type="community_donation",
                hours=hours,
                description=description,
            )

            # Update community hours balance
            community_hours, _ = CommunityHours.objects.get_or_create()
            community_hours.total_hours += hours
            community_hours.save()

            messages.success(
                request, f"Successfully donated {hours} hours to the community!"
            )
        except (ValueError, TypeError):
            messages.error(request, "Invalid hours value provided.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

        return redirect("ledger")
