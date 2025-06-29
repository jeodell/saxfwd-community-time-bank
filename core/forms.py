from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Service, ServiceRequest

User = get_user_model()


def validate_file_size(value):
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("The maximum file size that can be uploaded is 5MB")


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        max_length=30,
    )
    last_name = forms.CharField(
        required=True,
        max_length=30,
    )
    email = forms.EmailField(
        required=True,
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the values of the Saxapahaw Timebank and I will use this platform responsibly and will not engage in malicious activities or illegal behavior.",
        error_messages={
            "required": "You must agree to our values and terms to register."
        },
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
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
        if commit:
            user.save()
        return user


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "title",
            "description",
            "availability",
            "category",
            "max_hours",
            "max_hours_per_month",
        ]


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
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


class ServiceRequestCompleteForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ["hours_completed", "cancellation_reason"]


class ServiceRequestRejectForm(forms.Form):
    rejection_reason = forms.CharField(
        required=True,
        help_text="Please provide a reason for rejecting this request",
    )


class ServiceRequestCancelForm(forms.Form):
    cancellation_reason = forms.CharField(
        required=False,
        help_text="Please provide a reason for canceling this request",
    )
