from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView, View

from ..forms import UserForm
from ..models import Request, Service, TimeBankLedger, User


class UserView(LoginRequiredMixin, View):
    template_name = "users/user.html"

    def get_object(self):
        try:
            user_id = self.kwargs.get("pk", self.request.user.id)
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(self.request, "User not found.")
            return None

    def get(self, request, *args, **kwargs):
        user: User | None = self.get_object()
        if not user:
            return redirect("home")

        # service_credit and request_credit
        all_credits = TimeBankLedger.objects.filter(
            user=user, transaction_type__in=["service_credit", "request_credit"]
        ).order_by("-created_at")[:5]

        # service_debit and request_debit
        all_debits = TimeBankLedger.objects.filter(
            user=user, transaction_type__in=["service_debit", "request_debit"]
        ).order_by("-created_at")[:5]

        # community_donation
        community_donations = TimeBankLedger.objects.filter(
            user=user, transaction_type="community_donation"
        ).order_by("-created_at")[:5]

        # community_request and application_credit
        community_requests_and_credits = TimeBankLedger.objects.filter(
            user=user, transaction_type__in=["community_request", "application_credit"]
        ).order_by("-created_at")[:5]

        # user_donation (both received and given)
        user_donations = TimeBankLedger.objects.filter(
            user=user, transaction_type="user_donation"
        ).order_by("-created_at")[:5]

        context = {
            "profile_user": user,
            "services": Service.objects.filter(
                provider=user, is_active=True, is_deleted=False
            ),
            "requests": Request.objects.filter(
                requester=user, is_active=True, is_deleted=False
            ),
            "all_credits": all_credits,
            "all_debits": all_debits,
            "community_donations": community_donations,
            "community_requests": community_requests_and_credits,
            "user_donations": user_donations,
            "form": UserForm(instance=user) if request.user == user else None,
        }

        return render(request, self.template_name, context)


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_me")

    def get_object(self):
        try:
            return User.objects.get(id=self.request.user.id)
        except User.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["user"] = self.get_object()
        return context

    def post(self, request, *args, **kwargs):
        user: User | None = self.get_object()
        if not user:
            return redirect("home")

        if request.user != user:
            messages.error(request, "You do not have permission to update this user.")
            return redirect("home")

        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            user.process_image()
            messages.success(request, "User updated successfully!")
            return redirect("user", pk=user.id)

        context = self.get_context_data(user=user, form=form)
        return render(request, self.template_name, context)


class UserDonationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        recipient_id = self.kwargs.get("pk")
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("home")

        # Don't allow donating to yourself
        if request.user == recipient:
            messages.error(request, "You cannot donate to yourself.")
            return redirect("user", pk=recipient_id)

        hours = request.POST.get("hours")
        message = request.POST.get("message", "")

        # Validate hours
        try:
            hours = Decimal(hours)
            if hours < Decimal("0.25"):
                messages.error(request, "Minimum donation is 0.25 hours.")
                return redirect("user", pk=recipient_id)
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid number of hours.")
            return redirect("user", pk=recipient_id)

        # Check if donor has enough hours and won't go below 0 hours
        donor_balance = request.user.time_balance
        if donor_balance < hours:
            messages.error(
                request, f"You only have {donor_balance} hours available to donate."
            )
            return redirect("user", pk=recipient_id)

        # Check if donation would put donor below 0 hours
        if not request.user.can_afford_hours(hours, is_donation=True):
            effective_balance = request.user.get_effective_balance()
            pending_hours = request.user.get_pending_hours()
            new_balance = request.user.get_minimum_balance_after_transaction(hours)

            if pending_hours > 0:
                messages.error(
                    request,
                    f"This donation would put your effective balance at {new_balance} hours, which is below the minimum of 0 hours. "
                    f"Your current balance is {donor_balance} hours, but you have {pending_hours} hours in pending transactions. "
                    f"Your effective balance is {effective_balance} hours. "
                    f"Please reduce the donation amount, complete pending transactions, or earn more hours before making this donation.",
                )
            else:
                messages.error(
                    request,
                    f"This donation would put your balance at {new_balance} hours, which is below the minimum of 0 hours. "
                    f"Your current balance is {donor_balance} hours. "
                    f"Please reduce the donation amount or earn more hours before making this donation.",
                )
            return redirect("user", pk=recipient_id)

        # Create the donation transaction
        description = (
            f"Donation from {request.user.first_name} {request.user.last_name}"
        )
        if message:
            description += f": {message}"

        # Create debit for donor
        TimeBankLedger.objects.create(
            user=request.user,
            transaction_type="user_donation",
            hours=hours,
            description=f"Donation to {recipient.first_name} {recipient.last_name}",
            donated_by=request.user,
        )

        # Create credit for recipient
        TimeBankLedger.objects.create(
            user=recipient,
            transaction_type="user_donation",
            hours=hours,
            description=f"Donation from {request.user.first_name} {request.user.last_name}",
            donated_by=request.user,
        )

        messages.success(
            request,
            f"Successfully donated {hours} hours to {recipient.first_name} {recipient.last_name}!",
        )
        return redirect("user", pk=recipient_id)
