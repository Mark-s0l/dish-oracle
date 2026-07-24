from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    BaseUserCreationForm,
    PasswordChangeForm,
)
from django.core.exceptions import ValidationError

from accounts.models import CustomUser


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
            "email": forms.EmailInput(
                attrs={
                    "class": "email-input",
                    "placeholder": "example_mail@example.com",
                }
            )
        }


class EmailVerificationCode(forms.Form):
    code = forms.CharField(
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
            }
        ),
    )


class ChangePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update(
            {"placeholder": "Старый пароль"}
        )
        self.fields["new_password1"].widget.attrs.update(
            {"placeholder": "Новый пароль"}
        )
        self.fields["new_password2"].widget.attrs.update(
            {"placeholder": "Новый пароль ещё раз"}
        )


class SignUpUserForm(BaseUserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update(
            {
                "class": "auth__input",
                "placeholder": "Логин",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "class": "auth__input",
                "placeholder": "E-mail",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                "class": "auth__input",
                "placeholder": "Пароль",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "auth__input",
                "placeholder": "Пароль ещё раз",
            }
        )


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": "auth__input",
                "placeholder": "Логин или e-mail",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "auth__input",
                "placeholder": "Пароль",
            }
        )
