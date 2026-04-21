from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from stdnum import ean
from django.contrib.postgres.indexes import GinIndex

from food_hub.utils.validators import (
    ean13_validator,
    field_name_product,
    fields_name_validator,
    slug_validator,
)


def valid_ean13(value):
    ean13_validator(value)
    try:
        ean.validate(value)
    except Exception:
        raise ValidationError("Некорректный EAN-13 код")


class PositiveTagsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(taste_type=TasteTag.TypeTag.POSITIVE)


class NegativeTagsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(taste_type=TasteTag.TypeTag.NEGATIVE)


class TasteTag(models.Model):
    class TypeTag(models.TextChoices):
        NEGATIVE = "N", "Negative"
        POSITIVE = "P", "Positive"

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Название тега вкуса",
        validators=[fields_name_validator],
    )
    taste_type = models.CharField(
        max_length=1,
        choices=TypeTag.choices,
        null=False,
        blank=False,
        help_text="Тип тега вкуса (положительный или отрицательный)",
    )
    slug = models.SlugField(max_length=50, unique=True, validators=[slug_validator])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    positive = PositiveTagsManager()
    negative = NegativeTagsManager()

    class Meta:
        verbose_name = "Тег вкуса"
        verbose_name_plural = "Теги вкуса"
        indexes = [
            models.Index(fields=["taste_type"]),
        ]

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("taste_tag_sort", kwargs={"slug": self.slug})


class Category(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Название категории",
        validators=[fields_name_validator],
    )
    taste_tags = models.ManyToManyField(TasteTag, related_name="categories")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        indexes = [
            GinIndex(
                name="category_name_trgm_gin",
                fields=["name"],
                opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(
        max_length=30,
        unique=True,
        help_text="Название страны",
        validators=[fields_name_validator],
    )

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"

    def __str__(self):
        return self.name


class Company(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Название компании",
        validators=[fields_name_validator],
    )
    country = models.ForeignKey(Country, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
        indexes = [
            GinIndex(
                name="company_name_trgm_gin",
                fields=["name"],
                opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=100,
        help_text="Название продукта",
        validators=[field_name_product],
    )
    ean_code = models.CharField(
        max_length=13,
        validators=[valid_ean13],
        unique=True,
        help_text="13-значный EAN код продукта",
    )
    img_field = models.ImageField(upload_to="products/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        indexes = [
            GinIndex(
                name="product_name_trgm_gin",
                fields=["name"], 
                opclasses=["gin_trgm_ops"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"], name="unique_product_per_company"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class ProductRating(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="ratings"
    )
    rate = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Комментарий",
        help_text="Комментарий к рейтингу продукта",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    taste_tags = models.ManyToManyField(TasteTag, related_name="ratings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Рейтинг продукта"
        verbose_name_plural = "Рейтинги продуктов"
        indexes = [
            models.Index(fields=["rate", "updated_at", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_rating"
            )
        ]

    def __str__(self):
        return f"Rating {self.rate} for {self.product.name}"
