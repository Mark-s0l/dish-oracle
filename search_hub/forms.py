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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["tags"].queryset = TasteTag.objects.filter(ratings__user=user).distinct().order_by("name")
