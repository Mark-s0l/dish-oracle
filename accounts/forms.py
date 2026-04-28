from django import forms
from accounts.models import CustomUser
from django.core.exceptions import ValidationError

class ChangeEmailUser(forms.ModelForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже занят")
        return email

    class Meta:
        model = CustomUser
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={
                "class": "email-input",
                "placeholder": "example_mail@example.com",
            })
        }