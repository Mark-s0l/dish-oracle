from django import forms
from food_hub.models import TasteTag, ProductRating

class RatingForm(forms.Form):
    RATE_CHOICES = [(i, i) for i in range(1, 6)]

    rate = forms.TypedChoiceField(
        choices=RATE_CHOICES,
        widget=forms.RadioSelect,
        coerce=int,
        required=True
    )

class TasteTagForm(forms.Form):
    taste_tags = forms.ModelMultipleChoiceField(
        queryset=TasteTag.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Теги",
    )
    