from django import forms
from food_hub.models import Product

class SearchForm(forms.Form):
    query = forms.CharField()
    
class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['ean_code']