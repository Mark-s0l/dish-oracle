from food_hub.models import TasteTag

def choose_taste_tags(rating, category):
    if rating == 5:
        tags = TasteTag.positive.filter(categories__name=category).order_by('?')
    elif rating == 4:
        tags1 = list(TasteTag.positive.filter(categories__name=category).order_by('?')[:3])
        tags2 = list(TasteTag.negative.filter(categories__name=category).order_by('?')[:3])
        tags = tags1 + tags2
    else:
        tags = TasteTag.negative.filter(categories__name=category).order_by('?')[:6]
    return tags
