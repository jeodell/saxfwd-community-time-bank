from django import forms

from .models import Service, ServiceRequest, UserProfile


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["title", "description", "category"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ["requested_date", "hours_requested", "description"]
        widgets = {
            "requested_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["bio", "phone_number", "email", "address"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }
