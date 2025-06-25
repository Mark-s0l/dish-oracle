from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from stdnum import ean

from food_hub.validators import ean13_validator, fields_name_validator, slug_validator


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
    # Используется для CSS-селекторов на фронте, не для URL
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
        return f"{self.name} [{self.get_taste_type_display()}]"


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

    def __str__(self):
        return self.name


class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=100,
        help_text="Название продукта",
        validators=[fields_name_validator],
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
            models.Index(fields=["name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"], name="unique_product_per_company"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.pk})


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

    # NOTE: This model is designed to link to a user model in future via FK.
    # The field will be added once `user_data` app is implemented.
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

    def __str__(self):
        return f"Rating {self.rate} for {self.product.name}"
