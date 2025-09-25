from django import forms

class SearchForm(forms.Form):
    query = query = forms.CharField(label='', required=False, widget=forms.TextInput(attrs={
'placeholder': 'Поиск по названию и компании'}))