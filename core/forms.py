from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

from .models import Request, RequestTransaction, Service, ServiceTransaction

User = get_user_model()


def validate_file_size(value):
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("The maximum file size that can be uploaded is 5MB")


class UserApplicationForm(forms.ModelForm):
    referral_member = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).filter(
            application__is_referral_approved=True,
            application__is_orientation_completed=True,
        ),
        required=True,
        help_text="Please select the existing member who referred you to the timebank. If you have no referral member, please select 'No referral member'.",
        empty_label="Select a referral member",
    )
    writeup = forms.CharField(required=True)
    age_verification = forms.BooleanField(
        required=True,
        label="I confirm that I am at least 18 years old or I have received permission from a parent or guardian to apply to join the Saxapahaw Timebank.",
        error_messages={"required": "You must confirm your age to apply."},
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
            "age_verification",
            "terms_accepted",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_referral_member(self):
        referral_member = self.cleaned_data.get("referral_member")
        # If the value is "none" (from the "No referral member" option), return None
        if referral_member == "none":
            return None
        # If the field is empty (from the disabled placeholder), raise validation error
        if not referral_member:
            return None
        return referral_member

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


class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            "title",
            "description",
            "category",
            "preferred_date",
            "estimated_hours",
            "num_users_needed",
            "priority",
        ]


class ServiceTransactionForm(forms.ModelForm):
    class Meta:
        model = ServiceTransaction
        fields = ["requested_date", "hours_requested", "description"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_hours_requested(self):
        hours_requested = self.cleaned_data.get("hours_requested")

        if self.user and hours_requested:
            if not self.user.can_afford_hours(hours_requested):
                current_balance = self.user.time_balance
                effective_balance = self.user.get_effective_balance()
                pending_hours = self.user.get_pending_hours()
                new_balance = self.user.get_minimum_balance_after_transaction(
                    hours_requested
                )

                if pending_hours > 0:
                    raise forms.ValidationError(
                        f"This transaction would put your effective balance at {new_balance} hours, which is below the minimum of -3 hours. "
                        f"Your current balance is {current_balance} hours, but you have {pending_hours} hours in pending transactions. "
                        f"Your effective balance is {effective_balance} hours. "
                        f"Please reduce the hours requested, complete pending transactions, or earn more hours before making this request."
                    )
                else:
                    raise forms.ValidationError(
                        f"This transaction would put your balance at {new_balance} hours, which is below the minimum of -3 hours. "
                        f"Your current balance is {current_balance} hours. "
                        f"Please reduce the hours requested or earn more hours before making this request."
                    )

        return hours_requested


class RequestTransactionForm(forms.ModelForm):
    class Meta:
        model = RequestTransaction
        fields = ["proposed_hours", "message"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_proposed_hours(self):
        proposed_hours = self.cleaned_data.get("proposed_hours")

        if self.user and proposed_hours:
            if not self.user.can_afford_hours(proposed_hours):
                current_balance = self.user.time_balance
                effective_balance = self.user.get_effective_balance()
                pending_hours = self.user.get_pending_hours()
                new_balance = self.user.get_minimum_balance_after_transaction(
                    proposed_hours
                )

                if pending_hours > 0:
                    raise forms.ValidationError(
                        f"This transaction would put your effective balance at {new_balance} hours, which is below the minimum of -3 hours. "
                        f"Your current balance is {current_balance} hours, but you have {pending_hours} hours in pending transactions. "
                        f"Your effective balance is {effective_balance} hours. "
                        f"Please reduce the hours proposed, complete pending transactions, or earn more hours before making this offer."
                    )
                else:
                    raise forms.ValidationError(
                        f"This transaction would put your balance at {new_balance} hours, which is below the minimum of -3 hours. "
                        f"Your current balance is {current_balance} hours. "
                        f"Please reduce the hours proposed or earn more hours before making this offer."
                    )

        return proposed_hours


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


class RequestTransactionCompleteForm(forms.ModelForm):
    class Meta:
        model = RequestTransaction
        fields = ["hours_completed"]


class RequestTransactionRejectForm(forms.Form):
    rejection_reason = forms.CharField(
        required=True,
        help_text="Please provide a reason for rejecting this offer",
    )


class RequestTransactionCancelForm(forms.Form):
    cancellation_reason = forms.CharField(
        required=False,
        help_text="Please provide a reason for canceling this offer",
    )


class UserDonationForm(forms.Form):
    hours = forms.DecimalField(
        min_value=0.25,
        max_digits=4,
        decimal_places=2,
    )
    message = forms.CharField(
        required=False,
    )
