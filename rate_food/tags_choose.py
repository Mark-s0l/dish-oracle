import logging

from food_hub.models import TasteTag

logger = logging.getLogger("rate_food")


def choose_taste_tags(rate, category):
    try:
        base_orm_request = category.taste_tags.all()
        if rate == 5:
            ids = list(
                base_orm_request.filter(
                    taste_type=TasteTag.TypeTag.POSITIVE
                ).values_list("id", flat=True)[:6]
            )

        elif rate in (3, 4):
            ids_p = list(
                base_orm_request.filter(
                    taste_type=TasteTag.TypeTag.POSITIVE
                ).values_list("id", flat=True)[:3]
            )
            ids_n = list(
                base_orm_request.filter(
                    taste_type=TasteTag.TypeTag.NEGATIVE
                ).values_list("id", flat=True)[:3]
            )
            ids = ids_p + ids_n

        elif rate in (1, 2):
            ids = list(
                base_orm_request.filter(
                    taste_type=TasteTag.TypeTag.NEGATIVE
                ).values_list("id", flat=True)[:6]
            )
        else:
            logger.error(f"[TAGS_CHOOSE] Invalid rate value: {rate}")
            return TasteTag.objects.none()
    except AttributeError:
        logger.error(f"[TAGS_CHOOSE] Invalid category: {category}")
        return TasteTag.objects.none()
    return TasteTag.objects.filter(id__in=ids)
