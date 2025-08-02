from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import ListView, View

from ..models import CommunityHours, TimeBankLedger, User


class CommunityView(LoginRequiredMixin, ListView):
    model = TimeBankLedger
    template_name = "core/community.html"
    context_object_name = "transactions"
    paginate_by = 50  # Show 50 transactions per page

    def get_queryset(self):
        # Get all transactions and order by created_at
        transactions = TimeBankLedger.objects.all().order_by("-created_at")

        # Group transactions
        grouped_transactions = {}
        for transaction in transactions:
            # Create unique key for grouping
            if transaction.transaction_type == "user_donation":
                # Group user donations by the donation event (same donated_by, same hours, same timestamp)
                if transaction.donated_by:
                    # Use the donor's ID and timestamp to group related entries
                    key = f"user_donation_{transaction.donated_by.id}_{transaction.created_at.strftime('%Y%m%d_%H%M%S')}"
                else:
                    # Fallback for donations without donated_by
                    key = f"user_donation_{transaction.id}"
            else:
                key = (
                    transaction.service_transaction_id
                    or transaction.request_transaction_id
                    or f"direct_{transaction.id}"
                )

            if key not in grouped_transactions:
                description = None
                from_user = None
                to_user = None

                # Service
                if transaction.service_transaction:
                    service_transaction = transaction.service_transaction
                    description = service_transaction.service.title
                    from_user = service_transaction.requester
                    to_user = service_transaction.service.provider
                else:
                    service_transaction = None

                # Request
                if transaction.request_transaction:
                    request_transaction = transaction.request_transaction
                    description = request_transaction.request.title
                    from_user = request_transaction.request.requester
                    to_user = request_transaction.provider
                else:
                    request_transaction = None

                # Community
                if transaction.transaction_type == "community_donation":
                    description = "Community Hours Donation"
                    from_user = transaction.user
                    to_user = "Community"

                # Application Credit
                elif transaction.transaction_type == "application_credit":
                    description = transaction.description
                    from_user = "Community"
                    to_user = transaction.user

                # User Donation
                elif transaction.transaction_type == "user_donation":
                    if transaction.donated_by:
                        # This is the debit entry (donor), skip it
                        if transaction.user == transaction.donated_by:
                            continue

                        # This is the credit entry (recipient)
                        description = transaction.description
                        from_user = transaction.donated_by
                        to_user = transaction.user
                    else:
                        # Fallback for any user donations without donated_by field
                        description = transaction.description
                        from_user = "Unknown"
                        to_user = transaction.user

                grouped_transactions[key] = {
                    "created_at": transaction.created_at,
                    "service_transaction": service_transaction,
                    "request_transaction": request_transaction,
                    "hours": transaction.hours,
                    "description": description,
                    "from_user": from_user,
                    "to_user": to_user,
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
        community_hours = CommunityHours.get_instance()
        context["community_hours_balance"] = community_hours.total_hours

        # Add user's time balance if authenticated
        if self.request.user.is_authenticated:
            context["user_time_balance"] = self.request.user.time_balance

        # Add community members data
        context["users"] = User.objects.all().order_by("-date_joined")

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
                return redirect("community")

            # Check if user has enough hours and won't go below 0 hours
            user_balance = request.user.time_balance
            if user_balance < hours:
                messages.error(
                    request, "You don't have enough hours to make this donation."
                )
                return redirect("community")

            # Check if donation would put user below 0 hours
            if not request.user.can_afford_hours(hours, is_donation=True):
                effective_balance = request.user.get_effective_balance()
                pending_hours = request.user.get_pending_hours()
                new_balance = request.user.get_minimum_balance_after_transaction(hours)

                if pending_hours > 0:
                    messages.error(
                        request,
                        f"This donation would put your effective balance at {new_balance} hours, which is below the minimum of 0 hours. "
                        f"Your current balance is {user_balance} hours, but you have {pending_hours} hours in pending transactions. "
                        f"Your effective balance is {effective_balance} hours. "
                        f"Please reduce the donation amount, complete pending transactions, or earn more hours before making this donation.",
                    )
                else:
                    messages.error(
                        request,
                        f"This donation would put your balance at {new_balance} hours, which is below the minimum of 0 hours. "
                        f"Your current balance is {user_balance} hours. "
                        f"Please reduce the donation amount or earn more hours before making this donation.",
                    )
                return redirect("community")

            # Create ledger entry for the donation
            TimeBankLedger.objects.create(
                user=request.user,
                transaction_type="community_donation",
                hours=hours,
                description=description,
            )

            messages.success(
                request, f"Successfully donated {hours} hours to the community!"
            )
        except (ValueError, TypeError):
            messages.error(request, "Invalid hours value provided.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

        return redirect("community")
