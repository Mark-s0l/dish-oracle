from django import forms

from food_hub.models import TasteTag


class SearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Поиск по имени продукта, компании",
                "class": "search-input",
            }
        ),
    )


class TagSelectorForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        queryset=TasteTag.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Теги",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tags"].queryset = TasteTag.objects.order_by("name")
