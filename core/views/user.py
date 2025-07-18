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
        user = self.get_object()
        if not user:
            return redirect("home")

        # service_credit or request_credit
        all_credits = TimeBankLedger.objects.filter(
            user=user, transaction_type__in=["service_credit", "request_credit"]
        ).order_by("-created_at")[:5]

        all_debits = TimeBankLedger.objects.filter(
            user=user, transaction_type__in=["service_debit", "request_debit"]
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
            "community_donations": TimeBankLedger.objects.filter(
                user=user, transaction_type="community_donation"
            ).order_by("-created_at")[:5],
            "community_requests": TimeBankLedger.objects.filter(
                user=user, transaction_type="community_request"
            ).order_by("-created_at")[:5],
            "form": UserForm(instance=user) if request.user == user else None,
        }
        return render(request, self.template_name, context)


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("user_me")

    def get_object(self):
        return User.objects.get(id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["user"] = self.get_object()
        return context

    def post(self, request, *args, **kwargs):
        user = self.get_object()
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
