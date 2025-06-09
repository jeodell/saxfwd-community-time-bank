from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Service, ServiceRequest, UserProfile


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
            "username",
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
        fields = ["title", "description", "category"]


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ["requested_date", "hours_requested", "description"]


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(required=False)
    address = forms.CharField(required=False)
    bio = forms.CharField(required=False)
    image = forms.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "address",
            "image",
            "bio",
        ]
