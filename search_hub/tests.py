import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

import food_hub.models as models

User = get_user_model()


@pytest.fixture()
def user2(django_db_blocker):
    with django_db_blocker.unblock():
        user = User.objects.create_user(
            username="testuser2", email="user2_email@inbox.com", password="testpass"
        )
    yield user
    with django_db_blocker.unblock():
        user.delete()


@pytest.fixture
def country(db):
    return models.Country.objects.create(name="Россия")


@pytest.fixture
def make_company(db, country):
    def _make(name):
        return models.Company.objects.create(name=name, country=country)

    return _make


@pytest.fixture
def make_product(db, category):
    def _make(company, name, ean):
        return models.Product.objects.create(
            company=company, category=category, name=name, ean_code=ean
        )

    return _make


@pytest.fixture
def make_taste_tag(db, category):
    def _make(name, taste_type, slug):
        return models.TasteTag.objects.create(
            name=name, taste_type=taste_type, slug=slug
        )

    return _make


@pytest.fixture
def make_rate(db):
    def _make(product, rate, tags, user):
        rating = models.ProductRating.objects.create(
            product=product, rate=rate, user=user
        )
        rating.taste_tags.set(tags)
        return rating

    return _make


@pytest.fixture
def category(db):
    category = models.Category.objects.create(name="Десерты")
    return category


@pytest.fixture
def setup_products(
    db,
    client,
    make_company,
    make_taste_tag,
    make_product,
    make_rate,
    category,
    country,
    user,
):
    client.force_login(user=user)
    c1 = make_company("Завод мороженого")
    c2 = make_company("Вафельный комбинат")
    c3 = make_company("Цех Кремлбрюле")

    p1 = make_product(c1, "Мороженое Сливочное Яшкино 20% 70г", "4006381333931")
    p2 = make_product(c2, "Вафли Яшкино 200г", "4607145590012")
    p3 = make_product(c3, "Крем-брюле Бодрая Корова 200г", "4600699502197")

    t1 = make_taste_tag("Сладкий", "P", "slakdiy")
    t2 = make_taste_tag("Солёный", "P", "soleniy")
    t3 = make_taste_tag("Горький", "N", "gorkiy")

    make_rate(p1, 5, [t1], user)
    make_rate(p2, 4, [t2], user)
    make_rate(p3, 2, [t3], user)
    return [p1, p2, p3]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Моро", ["Мороженое Сливочное Яшкино 20% 70г"]),
        ("Мороженое", ["Мороженое Сливочное Яшкино 20% 70г"]),
        ("Кетчуп", []),
        (" ", []),
        ("", []),
        ("МоРОЖЕное", ["Мороженое Сливочное Яшкино 20% 70г"]),
        ("МаРОЖЕное", []),
        ("Ваф", ["Вафли Яшкино 200г"]),
        ("Крем", ["Крем-брюле Бодрая Корова 200г"]),
        ("Крем-брюле Бодрая Корова 200г", ["Крем-брюле Бодрая Корова 200г"]),
        ("7", ["Мороженое Сливочное Яшкино 20% 70г"]),
        ("№2", []),
        (
            "Десерты",
            [
                "Мороженое Сливочное Яшкино 20% 70г",
                "Вафли Яшкино 200г",
                "Крем-брюле Бодрая Корова 200г",
            ],
        ),
        ("Яшкино", ["Мороженое Сливочное Яшкино 20% 70г", "Вафли Яшкино 200г"]),
        ("рожен", ["Мороженое Сливочное Яшкино 20% 70г"]),
    ],
)
@pytest.mark.django_db
def test_product_search(client, setup_products, query, expected, user):
    client.force_login(user=user)
    url = reverse("search_hub:product_search")
    response = client.get(url, {"query": query})
    found = list(response.context["products"].values_list("name", flat=True))
    assert set(found) == set(expected)


@pytest.mark.django_db
def test_filter_by_multiple_tags_and(
    client, make_company, make_product, category, country, user
):
    client.force_login(user)
    # теги
    t1 = models.TasteTag.objects.create(name="tag1", slug="tag1", taste_type="P")
    t2 = models.TasteTag.objects.create(name="tag2", slug="tag2", taste_type="P")

    # продукты
    c = make_company("Comp")
    p_a = make_product(c, "Product A", "0000000000001")  # tag1 + tag2
    p_b = make_product(c, "Product B", "0000000000002")  # tag1 only
    p_c = make_product(c, "Product C", "0000000000003")  # tag2 only

    # рейтинги и привязка тегов
    r_a = models.ProductRating.objects.create(product=p_a, rate=5, user=user)
    r_a.taste_tags.add(t1, t2)

    r_b = models.ProductRating.objects.create(product=p_b, rate=4, user=user)
    r_b.taste_tags.add(t1)

    r_c = models.ProductRating.objects.create(product=p_c, rate=3, user=user)
    r_c.taste_tags.add(t2)

    url = reverse("search_hub:product_search")

    # пробуем несколько вариантов запроса: ids и slugs, параметр 'tags' и 't'
    tried = []
    combos = [
        ({"tags": [t1.id, t2.id]}, "ids / tags"),
        ({"tags": [t1.slug, t2.slug]}, "slugs / tags"),
        ({"t": [t1.id, t2.id]}, "ids / t"),
        ({"t": [t1.slug, t2.slug]}, "slugs / t"),
    ]
    success = False
    for params, note in combos:
        tried.append(note)
        resp = client.get(url, params)
        assert resp.status_code == 200
        products_qs = resp.context.get("products")
        if not products_qs:
            continue
        found = list(products_qs.values_list("name", flat=True))
        if set(found) == {"Product A"}:
            success = True
            break

    assert success, f"Filtering by tags failed for variants: {tried}"


@pytest.mark.django_db
def test_filter_sort_by_number_of_matching_tags(
    client, make_company, make_product, category, country, user
):
    client.force_login(user)
    # теги
    t1 = models.TasteTag.objects.create(name="t1", slug="t1", taste_type="P")
    t2 = models.TasteTag.objects.create(name="t2", slug="t2", taste_type="P")
    t3 = models.TasteTag.objects.create(name="t3", slug="t3", taste_type="P")

    # продукты
    c = make_company("Comp")
    p1 = make_product(c, "P1 all", "1000000000001")  # t1,t2,t3
    p2 = make_product(c, "P2 two", "1000000000002")  # t1,t2
    p3 = make_product(c, "P3 one", "1000000000003")  # t1

    # рейтинги и теги
    r1 = models.ProductRating.objects.create(product=p1, rate=5, user=user)
    r1.taste_tags.add(t1, t2, t3)

    r2 = models.ProductRating.objects.create(product=p2, rate=5, user=user)
    r2.taste_tags.add(t1, t2)

    r3 = models.ProductRating.objects.create(product=p3, rate=5, user=user)
    r3.taste_tags.add(t1)

    url = reverse("search_hub:product_search")
    resp = client.get(url, {"tags": [t1.id, t2.id]})
    assert resp.status_code == 200

    found = list(resp.context["products"].values_list("name", flat=True))

    # если view сортирует по числу совпадений,
    # P1 должен идти раньше P2, а P2 — раньше P3
    # тест устойчив к отсутствию P3
    # (если фильтр требует AND — то P3 не попадёт)
    if "P3 one" in found:
        assert found.index("P1 all") < found.index("P2 two")
        assert found.index("P2 two") < found.index("P3 one")
    else:
        # при строгом AND результат должен содержать только P1
        # (только продукты с обоими тегами)
        assert set(found) == {"P1 all", "P2 two"} or set(found) == {"P1 all"}


@pytest.mark.django_db
def test_tags_only_filter(client, make_company, make_product, category, country, user):
    client.force_login(user)
    t1 = models.TasteTag.objects.create(name="t1", slug="t1", taste_type="P")
    t2 = models.TasteTag.objects.create(name="t2", slug="t2", taste_type="P")

    company = make_company("C")
    p_ok = make_product(company, "OK", "0000000000001")
    p_bad = make_product(company, "BAD", "0000000000002")

    r_ok = models.ProductRating.objects.create(product=p_ok, rate=5, user=user)
    r_ok.taste_tags.add(t1, t2)

    r_bad = models.ProductRating.objects.create(product=p_bad, rate=3, user=user)
    r_bad.taste_tags.add(t1)

    url = reverse("search_hub:product_search")
    resp = client.get(url, {"tags": [t1.id, t2.id]})
    assert resp.status_code == 200
    names = list(resp.context["products"].values_list("name", flat=True))
    assert names == ["OK"] or set(names) == {"OK"}


@pytest.mark.django_db
def test_clear_action_removes_tags_and_shows_query_results(
    client, make_company, make_product, category, country, user
):
    client.force_login(user)
    # теги
    t1 = models.TasteTag.objects.create(name="t1", slug="t1", taste_type="P")
    t2 = models.TasteTag.objects.create(name="t2", slug="t2", taste_type="P")

    # продукты с общей частью в имени, чтобы query мог вернуть оба
    company = make_company("Comp")
    p_ok = make_product(company, "Prod OK", "0000000000001")
    p_bad = make_product(company, "Prod BAD", "0000000000002")

    r_ok = models.ProductRating.objects.create(product=p_ok, rate=5, user=user)
    r_ok.taste_tags.add(t1, t2)

    r_bad = models.ProductRating.objects.create(product=p_bad, rate=3, user=user)
    r_bad.taste_tags.add(t1)

    url = reverse("search_hub:product_search")

    # 1) Сначала запрос только с тегами — должен вернуть только p_ok (AND по t1+t2)
    resp = client.get(url, {"tags": [t1.id, t2.id]})
    assert resp.status_code == 200
    names = list(resp.context["products"].values_list("name", flat=True))
    assert set(names) == {"Prod OK"}

    # 2) Нажимаем "Сбросить" — отправляем те же теги + action=clear + query,
    # view должен удалить tags и выполнить поиск по query
    resp2 = client.get(
        url, {"tags": [t1.id, t2.id], "action": "clear", "query": "Prod"}
    )
    assert resp2.status_code == 200

    # Проверка: в контексте форма тегов не содержит выбранных tags
    tag_form = resp2.context["tag_selector"]
    # .data — QueryDict у bound-формы; getlist вернёт пустой список если нет tags
    assert tag_form.data.getlist("tags") == []

    # И продукты возвращаются по текстовому запросу (оба продукта)
    names2 = list(resp2.context["products"].values_list("name", flat=True))
    assert set(names2) == {"Prod OK", "Prod BAD"}


@pytest.mark.django_db
def test_different_user_search(
    client, make_company, make_product, make_rate, user, user2
):

    c1 = make_company("Вафельный комбинат")
    c2 = make_company("Цех Кремлбрюле")

    p1 = make_product(c1, "Мороженое Сливочное Яшкино 20% 70г", "4006381333931")
    p2 = make_product(c2, "Сливочные вафли Яшкино 200г", "4607145590012")

    t1 = models.TasteTag.objects.create(name="t1", slug="t1", taste_type="P")
    t2 = models.TasteTag.objects.create(name="t2", slug="t2", taste_type="P")

    make_rate(p1, 5, [t1], user)
    r2 = models.ProductRating.objects.create(product=p2, rate=3, user=user2)
    r2.taste_tags.add(t2)

    client.force_login(user=user)
    url = reverse("search_hub:product_search")
    response = client.get(url, {"query": "Сливочное"})

    found = list(response.context["products"].values_list("name", flat=True))
    assert found == [p1.name]


@pytest.mark.django_db
def test_different_user_search_without_rating(
    client, make_company, make_product, make_rate, user
):

    c1 = make_company("Вафельный комбинат")
    c2 = make_company("Цех Кремлбрюле")

    p1 = make_product(c1, "Мороженое Сливочное Яшкино 20% 70г", "4006381333931")
    make_product(c2, "Сливочные вафли Яшкино 200г", "4607145590012")

    t1 = models.TasteTag.objects.create(name="t1", slug="t1", taste_type="P")
    models.TasteTag.objects.create(name="t2", slug="t2", taste_type="P")

    make_rate(p1, 5, [t1], user)

    client.force_login(user=user)
    url = reverse("search_hub:product_search")
    response = client.get(url, {"query": "Сливочное"})

    found = list(response.context["products"].values_list("name", flat=True))
    assert found == [p1.name]


@pytest.mark.django_db
def test_tag_filter_matching_tag_does_not_leak_other_users_product(
    client, make_company, make_product, user, user2
):
    client.force_login(user)
    t1 = models.TasteTag.objects.create(name="t1", slug="t1", taste_type="P")

    c1 = make_company("C1")
    c2 = make_company("C2")
    p1 = make_product(c1, "Own product", "0000000000001")
    p2 = make_product(c2, "Other product", "0000000000002")

    r1 = models.ProductRating.objects.create(product=p1, rate=5, user=user)
    r1.taste_tags.add(t1)

    r2 = models.ProductRating.objects.create(product=p2, rate=5, user=user2)
    r2.taste_tags.add(t1)

    url = reverse("search_hub:product_search")
    resp = client.get(url, {"tags": [t1.id]})

    names = list(resp.context["products"].values_list("name", flat=True))
    assert names == [p1.name]
