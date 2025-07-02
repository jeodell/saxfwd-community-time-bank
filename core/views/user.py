from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, View

from ..forms import UserForm
from ..models import Service, ServiceRequest, TimeBankLedger, User


class UserListView(ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.all().order_by("last_name")


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

        context = {
            "profile_user": user,
            "services": Service.objects.filter(
                provider=user, is_active=True, is_deleted=False
            ),
            "requests": ServiceRequest.objects.filter(requester=user),
            "provider_transactions": TimeBankLedger.objects.filter(
                user=user, transaction_type="credit"
            ).order_by("-created_at")[:5],
            "requester_transactions": TimeBankLedger.objects.filter(
                user=user, transaction_type="debit"
            ).order_by("-created_at")[:5],
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
