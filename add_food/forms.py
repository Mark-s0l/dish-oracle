from django import forms

from food_hub.models import Product


class AddProductForm(forms.ModelForm):
    ean_code = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Введите штрих-код 13 цифр",
                "inputmode": "numeric",
                "enterkeyhint": "search",
            }
        )
    )

    class Meta:
        model = Product
        fields = ["ean_code"]
