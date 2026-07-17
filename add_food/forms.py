from django import forms

from food_hub.models import Product, valid_ean13


class AddProductForm(forms.Form):
    ean_code = forms.CharField(
        validators=[valid_ean13],
        widget=forms.TextInput(
            attrs={
                "placeholder": "Введите штрих-код 13 цифр",
                "inputmode": "numeric",
                "enterkeyhint": "search",
            }
        ),
    )
