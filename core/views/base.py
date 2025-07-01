from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView

from ..forms import ContactForm, UserRegistrationForm
from ..models import MeetingNotes, ServiceCategory


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
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

        return redirect("home")


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meeting_notes"] = MeetingNotes.objects.all()
        return context


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
