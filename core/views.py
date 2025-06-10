from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .forms import (
    ServiceForm,
    ServiceRequestForm,
    UserForm,
    UserRegistrationForm,
)
from .models import (
    Service,
    ServiceCategory,
    ServiceRequest,
    TimeBankLedger,
    User,
)

"""
HOME
"""


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ServiceCategory.get_featured_categories()
        return context


class ContactView(View):
    def post(self, request):
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"New Contact Form Submission from {name}"
        email_message = f"""
        Name: {name}
        Email: {email}

        Message:
        {message}
        """

        try:
            send_mail(
                subject=subject,
                message=email_message,
                from_email=email,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent successfully!")
        except Exception as e:
            print(f"Email error: {str(e)}")
            messages.error(
                request,
                "There was an error sending your message. Please try again later.",
            )

        return redirect("home")

    def get(self, request):
        return redirect("home")


class AboutView(TemplateView):
    template_name = "core/about.html"


"""
REGISTRATION
"""


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


"""
User
"""


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
            "given_transactions": TimeBankLedger.objects.filter(
                user=user, transaction_type="credit"
            ).order_by("-created_at")[:5],
            "received_transactions": TimeBankLedger.objects.filter(
                user=user, transaction_type="debit"
            ).order_by("-created_at")[:5],
            "form": UserForm(instance=user) if request.user == user else None,
        }
        return render(request, self.template_name, context)


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "users/user_edit.html"
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


"""
SERVICES
"""


class ServiceListView(ListView):
    model = Service
    template_name = "services/service_list.html"
    context_object_name = "services"

    def get_queryset(self):
        # Get category filter
        category_id = self.request.GET.get("category")
        category = None
        if category_id:
            try:
                category = ServiceCategory.objects.get(id=category_id)
            except (ServiceCategory.DoesNotExist, ValueError):
                pass

        # Get search filter
        search = self.request.GET.get("search", "")

        # Get view type filter
        view_type = self.request.GET.get("view", "public")

        # Show offered services if the user is authenticated
        if view_type == "offered" and self.request.user.is_authenticated:
            # Show only services offered by the current user
            services = Service.objects.filter(
                Q(title__icontains=search) | Q(description__icontains=search),
                provider=self.request.user,
            )
            if category:
                services = services.filter(category=category)
            return services
        else:
            # Show public services (excluding user's own services)
            return Service.get_active_services(
                exclude_user=self.request.user
                if self.request.user.is_authenticated
                else None,
                category=category,
                search=search,
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "categories": ServiceCategory.get_all_categories(),
                "services": self.get_queryset(),
            }
        )
        return context


class ServiceCreateView(LoginRequiredMixin, CreateView):
    form_class = ServiceForm
    template_name = "services/service_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ServiceCategory.get_all_categories()
        return context

    def form_valid(self, form):
        form.instance.provider = self.request.user
        messages.success(self.request, "Service created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the service.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("service_detail", kwargs={"pk": self.object.pk})


class ServiceDetailView(DetailView):
    model = Service
    template_name = "services/service_detail.html"
    context_object_name = "service"

    def post(self, request, *args, **kwargs):
        service = self.get_object()
        if request.user != service.provider:
            messages.error(request, "You do not have permission to edit this service.")
            return redirect("service_detail", pk=service.pk)

        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully!")
            return redirect("service_detail", pk=service.pk)
        return render(
            request, "services/service_form.html", {"form": form, "service": service}
        )

    def delete(self, request, *args, **kwargs):
        service = self.get_object()
        service.delete()
        messages.success(request, "Service deleted successfully!")
        return redirect("service_list")


class ServiceRequestView(LoginRequiredMixin, CreateView):
    form_class = ServiceRequestForm
    template_name = "requests/request_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["service"] = get_object_or_404(Service, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        form.instance.service = get_object_or_404(Service, pk=self.kwargs["pk"])
        form.instance.requester = self.request.user
        messages.success(self.request, "Service request submitted successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        messages.error(self.request, "There was an error submitting the request.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={"pk": self.object.pk})


"""
REQUESTS
"""


class RequestListView(LoginRequiredMixin, ListView):
    model = ServiceRequest
    template_name = "requests/request_list.html"
    context_object_name = "requests"

    def get_queryset(self):
        queryset = ServiceRequest.objects.filter(
            Q(requester=self.request.user) | Q(service__provider=self.request.user)
        )

        status = self.request.GET.get("status")
        if status:
            if status == "active":
                queryset = queryset.filter(status__in=["pending", "accepted"])
            else:
                queryset = queryset.filter(status=status)
        else:
            queryset = queryset.filter(status__in=["pending", "accepted"])

        return queryset.order_by("-created_at")


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = ServiceRequest
    template_name = "requests/request_detail.html"
    context_object_name = "request"

    def get_object(self):
        obj = super().get_object()
        if (
            self.request.user != obj.requester
            and self.request.user != obj.service.provider
        ):
            messages.error(
                self.request, "You do not have permission to view this request."
            )
            return redirect("home")
        return obj


class RequestAcceptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.service.provider:
            messages.error(request, "Only the service provider can accept requests.")
            return redirect("home")

        try:
            service_request.accept_request()
            messages.success(request, "Request accepted successfully!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("request_detail", pk=pk)


class RequestRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.service.provider:
            messages.error(request, "Only the service provider can reject requests.")
            return redirect("home")

        try:
            service_request.reject_request()
            messages.success(request, "Request rejected successfully!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("request_detail", pk=pk)


class RequestCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)

        try:
            is_fully_completed = service_request.complete_request(request.user)
            if is_fully_completed:
                messages.success(
                    request,
                    "Request completed successfully! Time credits have been transferred.",
                )
            else:
                messages.success(
                    request,
                    "Completion status updated. Waiting for the other party to complete.",
                )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("home")

        return redirect("request_detail", pk=pk)


class LedgerView(ListView):
    model = TimeBankLedger
    template_name = "core/ledger.html"
    context_object_name = "transactions"
    paginate_by = 50  # Show 50 transactions per page

    def get_queryset(self):
        # Get all transactions and order by created_at
        transactions = TimeBankLedger.objects.all().order_by("-created_at")

        # Group transactions by service request
        grouped_transactions = {}
        for transaction in transactions:
            # Use service request as the key for grouping
            key = transaction.service_request_id
            if key not in grouped_transactions:
                grouped_transactions[key] = {
                    "created_at": transaction.created_at,
                    "service_request": transaction.service_request,
                    "hours": transaction.hours,
                    "description": transaction.service_request.service.title
                    if transaction.service_request
                    else "Community Hours",
                    "from_user": transaction.service_request.requester
                    if transaction.service_request
                    else None,
                    "to_user": transaction.service_request.service.provider
                    if transaction.service_request
                    else None,
                }

        # Convert the grouped transactions to a list and sort by date
        return sorted(
            grouped_transactions.values(), key=lambda x: x["created_at"], reverse=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_transactions"] = len(self.get_queryset())
        context["total_hours_exchanged"] = sum(t["hours"] for t in self.get_queryset())
        return context


class RequestCommunityHoursView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_request_community_hours():
            messages.error(
                request, "This request cannot be converted to a community request."
            )
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "requests/community_request_form.html",
            {"request": service_request},
        )

    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.requester:
            messages.error(
                request, "Only the requester can convert to a community request."
            )
            return redirect("request_detail", pk=pk)

        if not service_request.can_request_community_hours():
            messages.error(
                request, "This request cannot be converted to a community request."
            )
            return redirect("request_detail", pk=pk)

        reason = request.POST.get("reason", "")
        if not reason:
            messages.error(
                request, "Please provide a reason for requesting community hours."
            )
            return redirect("request_detail", pk=pk)

        service_request.request_community_hours(reason)
        messages.success(request, "Community hours request submitted successfully!")
        return redirect("request_detail", pk=pk)


class ApproveCommunityRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_be_approved():
            messages.error(request, "This request cannot be approved.")
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "requests/community_request_review.html",
            {"request": service_request},
        )

    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_be_approved():
            messages.error(request, "This request cannot be approved.")
            return redirect("request_detail", pk=pk)

        notes = request.POST.get("notes", "")
        try:
            service_request.approve_community_request(request.user, notes)
            messages.success(request, "Community hours request approved successfully!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("request_detail", pk=pk)


class RejectCommunityRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_be_rejected():
            messages.error(request, "This request cannot be rejected.")
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "requests/community_request_review.html",
            {"request": service_request},
        )

    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_be_rejected():
            messages.error(request, "This request cannot be rejected.")
            return redirect("request_detail", pk=pk)

        notes = request.POST.get("notes", "")
        service_request.reject_community_request(request.user, notes)
        messages.success(request, "Community hours request rejected.")
        return redirect("request_detail", pk=pk)
