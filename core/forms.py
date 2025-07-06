from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from .models import Service, ServiceTransaction

User = get_user_model()


def validate_file_size(value):
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("The maximum file size that can be uploaded is 5MB")


class UserApplicationForm(forms.ModelForm):
    referral_member = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).filter(
            application__is_referral_approved=True, application__is_onboarded=True
        ),
        required=True,
        help_text="Please select the existing member who referred you to the timebank",
        empty_label="Select a referral member",
    )
    writeup = forms.CharField(
        required=True,
        help_text="Please tell us why you want to join the Saxapahaw Timebank and how you plan to contribute to our community.",
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the values of the Saxapahaw Timebank and I will use this platform responsibly and will not engage in malicious activities or illegal behavior.",
        error_messages={"required": "You must agree to our values and terms to apply."},
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "address",
            "referral_member",
            "writeup",
            "terms_accepted",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.terms_accepted = self.cleaned_data["terms_accepted"]
        user.terms_accepted_at = timezone.now()
        # Set user as inactive until approved
        user.is_active = False

        if commit:
            user.save()
        return user


class UserPasswordSetupForm(forms.Form):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Enter a strong password for your account.",
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        help_text="Enter the same password as before, for verification.",
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, user):
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True  # Activate the user account
        user.save()
        return user


class PasswordResetTokenForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput())

    def clean_token(self):
        token = self.cleaned_data.get("token")
        if not token:
            raise forms.ValidationError("Invalid token.")

        # Check if token is valid and not expired
        try:
            User = get_user_model()
            uidb64 = token.split(".")[0]
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(user, token):
                raise forms.ValidationError("Invalid or expired token.")

            if not user.is_fully_approved:
                raise forms.ValidationError(
                    "Your account has not been fully approved yet."
                )

            return token
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise forms.ValidationError("Invalid token.")


class ContactForm(forms.Form):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    message = forms.CharField(required=True)
    captcha = ReCaptchaField(widget=ReCaptchaV3)


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "title",
            "description",
            "availability",
            "experience",
            "category",
            "max_hours",
            "max_hours_per_month",
        ]


class ServiceTransactionForm(forms.ModelForm):
    class Meta:
        model = ServiceTransaction
        fields = ["requested_date", "hours_requested", "description"]


class UserForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        validators=[validate_file_size],
        help_text="Maximum file size: 5MB",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "address",
            "image",
            "bio",
        ]


class ServiceTransactionCompleteForm(forms.ModelForm):
    class Meta:
        model = ServiceTransaction
        fields = ["hours_completed", "cancellation_reason"]


class ServiceTransactionRejectForm(forms.Form):
    rejection_reason = forms.CharField(
        required=True,
        help_text="Please provide a reason for rejecting this request",
    )


class ServiceTransactionCancelForm(forms.Form):
    cancellation_reason = forms.CharField(
        required=False,
        help_text="Please provide a reason for canceling this request",
    )
