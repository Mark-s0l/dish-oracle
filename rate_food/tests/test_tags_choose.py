import pytest

from food_hub.models import Category, TasteTag
from rate_food.tags_choose import choose_taste_tags


@pytest.fixture
def make_taste_tag(db):
    def factory(name, taste_type, slug):
        return TasteTag.objects.create(name=name, taste_type=taste_type, slug=slug)

    return factory


@pytest.fixture
def category(db):
    category = Category.objects.create(name="Десерты")
    return category


@pytest.fixture
def category_with_tags(db, category, make_taste_tag):
    tag1 = make_taste_tag("Сладкий", TasteTag.TypeTag.POSITIVE, "sladkiy")
    tag2 = make_taste_tag("Кислый", TasteTag.TypeTag.NEGATIVE, "kisliy")
    tag3 = make_taste_tag("Горький", TasteTag.TypeTag.NEGATIVE, "gorkiy")
    tag4 = make_taste_tag("Ванильный", TasteTag.TypeTag.POSITIVE, "vanilnia")
    tag5 = make_taste_tag("Шоколадный", TasteTag.TypeTag.POSITIVE, "shokoladniy")
    tag6 = make_taste_tag("Клубничный", TasteTag.TypeTag.POSITIVE, "klubnichniy")
    tag7 = make_taste_tag("Яблочный", TasteTag.TypeTag.POSITIVE, "yabblochniy")
    tag8 = make_taste_tag("Персиковый", TasteTag.TypeTag.POSITIVE, "persikoviy")
    tag9 = make_taste_tag("Пересоленный", TasteTag.TypeTag.NEGATIVE, "peresoloniy")
    tag10 = make_taste_tag("Переперчёный", TasteTag.TypeTag.NEGATIVE, "pereperchoniy")
    tag11 = make_taste_tag("Пресный", TasteTag.TypeTag.NEGATIVE, "presniy")
    tag12 = make_taste_tag("Карамельный", TasteTag.TypeTag.POSITIVE, "karamelniy")
    tag13 = make_taste_tag("Водянистый", TasteTag.TypeTag.NEGATIVE, "vodynistiy")
    tag14 = make_taste_tag("Химический", TasteTag.TypeTag.NEGATIVE, "himichesky")
    category.taste_tags.add(
        tag1,
        tag2,
        tag3,
        tag4,
        tag5,
        tag6,
        tag7,
        tag8,
        tag9,
        tag10,
        tag11,
        tag12,
        tag13,
        tag14,
    )
    return category


class TestValidReturn:
    def test_rate_is_five(self, category_with_tags, db):
        result = choose_taste_tags(5, category=category_with_tags)
        assert len(result) == 6
        for tag in result:
            assert tag.taste_type == TasteTag.TypeTag.POSITIVE

    def test_rate_is_one(self, category_with_tags, db):
        result = choose_taste_tags(1, category=category_with_tags)
        assert len(result) == 6
        for tag in result:
            assert tag.taste_type == TasteTag.TypeTag.NEGATIVE

    def test_rate_is_two(self, category_with_tags, db):
        result = choose_taste_tags(2, category=category_with_tags)
        assert len(result) == 6
        for tag in result:
            assert tag.taste_type == TasteTag.TypeTag.NEGATIVE

    def test_rate_is_three(self, category_with_tags, db):
        result = choose_taste_tags(3, category=category_with_tags)
        assert len(result) == 6
        positive = result.filter(taste_type=TasteTag.TypeTag.POSITIVE)
        negative = result.filter(taste_type=TasteTag.TypeTag.NEGATIVE)
        assert len(positive) == 3
        assert len(negative) == 3

    def test_rate_is_four(self, category_with_tags, db):
        result = choose_taste_tags(4, category=category_with_tags)
        assert len(result) == 6
        positive = result.filter(taste_type=TasteTag.TypeTag.POSITIVE)
        negative = result.filter(taste_type=TasteTag.TypeTag.NEGATIVE)
        assert len(positive) == 3
        assert len(negative) == 3

    def test_no_tags(self, db, category):
        result = choose_taste_tags(4, category=category)
        assert len(result) == 0


class TestInvalidReturn:

    def test_invalid_rate(self, db, category_with_tags):
        result = choose_taste_tags(0, category=category_with_tags)
        assert len(result) == 0

    def test_invalid_category(self, db):
        result = choose_taste_tags(4, category="Кофе")
        assert len(result) == 0

    def test_no_category(self, db):
        result = choose_taste_tags(5, category=None)
        assert len(result) == 0
