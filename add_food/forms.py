from django import forms

from food_hub.models import Product


class AddProductForm(forms.Form):
    ean_code = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Введите штрих-код 13 цифр",
                "inputmode": "numeric",
                "enterkeyhint": "search",
            }
        )
    )
