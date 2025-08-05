from django import forms
from food_hub.models import Product

class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['ean_code']