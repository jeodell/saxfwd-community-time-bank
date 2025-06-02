from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ServiceForm, ServiceRequestForm, UserProfileForm
from .models import (
    Service,
    ServiceCategory,
    ServiceRequest,
    TimeBankLedger,
    UserProfile,
)

"""
HOME
"""


def home(request):
    recent_services = Service.objects.filter(is_active=True).order_by("-created_at")[:6]
    categories = ServiceCategory.objects.all()
    return render(
        request,
        "core/home.html",
        {
            "recent_services": recent_services,
            "categories": categories,
        },
    )


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # Send email
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
                recipient_list=["admin@example.com"],  # Replace with your email
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent successfully!")
        except Exception:
            messages.error(
                request,
                "There was an error sending your message. Please try again later.",
            )

        return redirect("home")

    return redirect("home")


def about(request):
    return render(request, "core/about.html")


"""
REGISTRATION
"""


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            messages.success(
                request, "Account created successfully! You can now log in."
            )
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


"""
PROFILE
"""


@login_required
def profile(request):
    profile = UserProfile.objects.get_or_create(user=request.user)[0]
    services = Service.objects.filter(provider=request.user)
    requests = ServiceRequest.objects.filter(requester=request.user)
    return render(
        request,
        "profile/profile.html",
        {
            "profile": profile,
            "services": services,
            "requests": requests,
        },
    )


@login_required
def profile_edit(request):
    profile = UserProfile.objects.get_or_create(user=request.user)[0]
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "profile/profile_edit.html", {"form": form})


"""
SERVICES
"""


def service_list(request):
    services = Service.objects.filter(is_active=True)
    category = request.GET.get("category")
    search = request.GET.get("search")

    if category:
        services = services.filter(category__name=category)
    if search:
        services = services.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    return render(
        request,
        "services/service_list.html",
        {
            "services": services,
            "categories": ServiceCategory.objects.all(),
        },
    )


@login_required
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = request.user
            service.save()
            messages.success(request, "Service created successfully!")
            return redirect("service_detail", pk=service.pk)
    else:
        form = ServiceForm()

    return render(request, "services/service_form.html", {"form": form})


@login_required
def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)

    if request.method == "DELETE":
        if request.user != service.provider:
            messages.error(
                request, "You do not have permission to delete this service."
            )
            return redirect("service_list")
        service.delete()
        messages.success(request, "Service deleted successfully!")
        return redirect("service_list")

    if request.method == "PUT":
        if request.user != service.provider:
            messages.error(request, "You do not have permission to edit this service.")
            return redirect("service_detail", pk=pk)

        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully!")
            return redirect("service_detail", pk=service.pk)
        return render(
            request, "services/service_form.html", {"form": form, "service": service}
        )

    return render(request, "services/service_detail.html", {"service": service})


@login_required
def service_request(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.service = service
            service_request.requester = request.user
            service_request.save()
            messages.success(request, "Service request submitted successfully!")
            return redirect("request_detail", pk=service_request.pk)
    else:
        form = ServiceRequestForm()

    return render(
        request,
        "requests/request_form.html",
        {"form": form, "service": service},
    )


"""
REQUESTS
"""


@login_required
def request_list(request):
    requests = ServiceRequest.objects.filter(
        Q(requester=request.user) | Q(service__provider=request.user)
    ).order_by("-created_at")
    return render(request, "requests/request_list.html", {"requests": requests})


@login_required
def request_detail(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if (
        request.user != service_request.requester
        and request.user != service_request.service.provider
    ):
        messages.error(request, "You do not have permission to view this request.")
        return redirect("home")
    return render(request, "requests/request_detail.html", {"request": service_request})


@login_required
def request_accept(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request.user != service_request.service.provider:
        messages.error(request, "Only the service provider can accept requests.")
        return redirect("home")

    if service_request.status != "pending":
        messages.error(request, "This request cannot be accepted.")
        return redirect("request_detail", pk=pk)

    service_request.status = "accepted"
    service_request.save()
    messages.success(request, "Request accepted successfully!")
    return redirect("request_detail", pk=pk)


@login_required
def request_complete(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request.user != service_request.service.provider:
        messages.error(request, "Only the service provider can complete requests.")
        return redirect("home")

    if service_request.status != "accepted":
        messages.error(request, "This request cannot be completed.")
        return redirect("request_detail", pk=pk)

    service_request.status = "completed"
    service_request.save()

    # Update timebank ledger
    hours = service_request.hours_requested
    provider_profile = UserProfile.objects.get_or_create(
        user=service_request.service.provider
    )[0]
    requester_profile = UserProfile.objects.get_or_create(
        user=service_request.requester
    )[0]

    # Credit provider
    TimeBankLedger.objects.create(
        user=service_request.service.provider,
        service_request=service_request,
        transaction_type="credit",
        hours=hours,
        balance=provider_profile.total_hours_earned + hours,
        description=f"Completed service: {service_request.service.title}",
    )
    provider_profile.total_hours_earned += hours
    provider_profile.save()

    # Debit requester
    TimeBankLedger.objects.create(
        user=service_request.requester,
        service_request=service_request,
        transaction_type="debit",
        hours=hours,
        balance=requester_profile.total_hours_spent + hours,
        description=f"Received service: {service_request.service.title}",
    )
    requester_profile.total_hours_spent += hours
    requester_profile.save()

    messages.success(request, "Request completed successfully!")
    return redirect("request_detail", pk=pk)


@login_required
def ledger(request):
    transactions = TimeBankLedger.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    return render(request, "core/ledger.html", {"transactions": transactions})
