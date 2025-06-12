from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView, View

from ..forms import UserForm, UserRegistrationForm
from ..models import Service, ServiceRequest, TimeBankLedger, User


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.terms_accepted = form.cleaned_data["terms_accepted"]
        user.terms_accepted_at = timezone.now()
        user.save()

        messages.success(
            self.request, "Account created successfully! You can now log in."
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating your account.")
        return render(self.request, self.template_name, {"form": form})


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
            "user": user,
            "services": Service.objects.filter(provider=user),
            "requests": ServiceRequest.objects.filter(requester=user),
            "provider_transactions": TimeBankLedger.objects.filter(
                user=user, transaction_type="credit"
            ).order_by("-created_at")[:5],
            "requester_transactions": TimeBankLedger.objects.filter(
                user=user, transaction_type="debit"
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

        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully!")
            return redirect("user", pk=user.id)

        context = self.get_context_data(user=user, form=form)
        return render(request, self.template_name, context)
