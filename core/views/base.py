from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    View,
)

from ..forms import ContactForm, UserApplicationForm, UserPasswordSetupForm
from ..models import Application, MeetingNotes, ServiceCategory, User


class HomeView(TemplateView):
    template_name = "core/home.html"
    form_class = ContactForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ServiceCategory.get_featured_categories()
        context["recaptcha_public_key"] = settings.RECAPTCHA_PUBLIC_KEY
        context["form"] = self.form_class()
        return context

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]

            # Send email
            try:
                send_mail(
                    f"Contact Form Message from {name}",
                    f"Name: {name}\nEmail: {email}\nMessage: {message}",
                    email,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, "Your message has been sent successfully!")
            except Exception:
                messages.error(
                    request,
                    "There was an error sending your message. Please try again.",
                )

            return redirect("home")
        else:
            context = self.get_context_data()
            context["form"] = form
            return render(request, self.template_name, context)


class ApplicationView(CreateView):
    form_class = UserApplicationForm
    template_name = "registration/apply.html"
    success_url = reverse_lazy("application_submitted")

    def form_valid(self, form):
        # Save the user (this will handle all the user creation logic)
        user = form.save()

        # Create the application
        Application.objects.create(
            user=user,
            referral_member=form.cleaned_data["referral_member"],
            writeup=form.cleaned_data["writeup"],
        )

        messages.success(
            self.request,
            "Your application has been submitted successfully! We will review it and contact you once it's been processed.",
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "There was an error submitting your application. Please check the form and try again.",
        )
        return render(self.request, self.template_name, {"form": form})


class ApplicationSubmittedView(TemplateView):
    template_name = "registration/application_submitted.html"


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting_notes"] = MeetingNotes.objects.all()
        return context


class PasswordSetupView(FormView):
    form_class = UserPasswordSetupForm
    template_name = "registration/password_setup.html"
    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        # Get user from token
        token = request.GET.get("token")
        if not token:
            messages.error(request, "Invalid password setup link.")
            return redirect("login")

        try:
            uidb64 = token.split(".")[0]
            uid = urlsafe_base64_decode(uidb64).decode()
            self.user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(self.user, token):
                messages.error(request, "Invalid or expired password setup link.")
                return redirect("login")

            if not self.user.is_fully_approved:
                messages.error(request, "Your account has not been fully approved yet.")
                return redirect("login")

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "Invalid password setup link.")
            return redirect("login")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Set the password and activate the user
        form.save(self.user)
        messages.success(
            self.request,
            "Your password has been set successfully! You can now log in to your account.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context


def send_approval_email(user):
    """Send approval email with password setup link to fully approved users."""
    if not user.is_fully_approved:
        return

    # Generate token for password setup
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token_with_uid = f"{uidb64}.{token}"

    # Create password setup URL
    password_setup_url = (
        f"{settings.SITE_URL}/accounts/password-setup/?token={token_with_uid}"
    )

    # Send email
    subject = "Welcome to Saxapahaw Timebank - Set Up Your Password"
    message = f"""
        Hello {user.first_name},

        Great news! Your application to join the Saxapahaw Timebank has been fully approved.
        You can now set up your password and start using your account.

        To set up your password, please click the link below:
        {password_setup_url}

        This link will expire in 7 days for security reasons.

        If you have any questions, please don't hesitate to contact us.

        Welcome to the community!

        Best regards,
        The Saxapahaw Timebank Team
        """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending approval email to {user.email}: {str(e)}")
        print(
            f"Email settings: HOST={getattr(settings, 'EMAIL_HOST', 'Not set')}, "
            f"PORT={getattr(settings, 'EMAIL_PORT', 'Not set')}, "
            f"USER={getattr(settings, 'EMAIL_HOST_USER', 'Not set')}, "
            f"TLS={getattr(settings, 'EMAIL_USE_TLS', 'Not set')}, "
            f"SSL={getattr(settings, 'EMAIL_USE_SSL', 'Not set')}"
        )

        return False


class ApplicationReviewListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Application
    template_name = "admin/application_review_list.html"
    context_object_name = "applications"
    paginate_by = 10

    def test_func(self):
        """Check if user is staff."""
        return self.request.user.is_staff

    def get_queryset(self):
        status_filter = self.request.GET.get("status", "all")
        if status_filter == "all":
            return Application.objects.all().select_related(
                "user", "referral_member", "referral_approved_by"
            )
        else:
            return Application.objects.filter(status=status_filter).select_related(
                "user", "referral_member", "referral_approved_by"
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status", "all")
        context["status_choices"] = Application.STATUS_CHOICES
        return context


class ApplicationReviewDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Application
    template_name = "admin/application_review_detail.html"
    context_object_name = "application"
    pk_url_kwarg = "application_id"

    def test_func(self):
        """Check if user is staff."""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["application_user"] = self.object.user
        return context

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        action = request.POST.get("action")
        review_notes = request.POST.get("review_notes", "")

        if action == "approve" and application.can_be_approved:
            application.approve(request.user, review_notes)
            messages.success(
                request,
                f"Application from {application.user.full_name} has been approved.",
            )

            # Send approval email if user is now fully approved
            if application.user.is_fully_approved:
                send_approval_email(application.user)
                messages.success(
                    request, f"Approval email sent to {application.user.email}"
                )

        elif action == "reject" and application.can_be_rejected:
            application.reject(request.user, review_notes)
            messages.success(
                request,
                f"Application from {application.user.full_name} has been rejected.",
            )

        return redirect("application_review_detail", application_id=application.pk)


class MarkUserOnboardedView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Mark a user as onboarded."""

    def test_func(self):
        """Check if user is staff."""
        return self.request.user.is_staff

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        try:
            application = user.application
            application.mark_onboarded()

            # Send approval email if user is now fully approved
            if user.is_fully_approved:
                send_approval_email(user)
                messages.success(
                    request,
                    f"User marked as onboarded. Approval email sent to {user.email}",
                )
            else:
                messages.success(request, "User marked as onboarded")

        except Application.DoesNotExist:
            messages.error(request, "User does not have an application")

        return redirect("application_review_detail", application_id=application.pk)
