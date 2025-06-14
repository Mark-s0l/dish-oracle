from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

class PositiveTagsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(taste_type=TasteTag.TypeTag.POSITIVE)

class NegativeTagsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(taste_type=TasteTag.TypeTag.NEGATIVE)

class TasteTag(models.Model):
    class TypeTag(models.TextChoices):
        NEGATIVE = 'N', 'Negative'
        POSITIVE = 'P', 'Positive'

    name = models.CharField(max_length=50, unique=True)
    taste_type = models.CharField(max_length=1, choices=TypeTag.choices, null=False, blank=False)

    objects = models.Manager()
    positive = PositiveTagsManager()
    negative = NegativeTagsManager()
    
    class Meta:
        verbose_name = 'Тег вкуса'
        verbose_name_plural = 'Теги вкуса'
        indexes = [
            models.Index(fields=['taste_type']),
        ]

    def __str__(self):
        return f'{self.name} [{self.get_taste_type_display()}]'

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    taste_tags = models.ManyToManyField(TasteTag, related_name='categories')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=30, unique=True)
    
    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'
    
    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=50, unique=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'
    
    def __str__(self):
        return self.name

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    ean_code = models.CharField(max_length=13, validators=[RegexValidator(regex=r'^\d{13}$')], unique=True)
    img_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        indexes = [
                models.Index(fields=['name']),
            ]
        constraints = [
        models.UniqueConstraint(fields=['company', 'name'],
                                name='unique_product_per_company')
    ]
        
    def __str__(self):
        return f'{self.name} ({self.company.name})'
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})

class ProductRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    rate = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name='Комментарий'
    )
    #NOTE: This model is designed to link to a user model in future via FK.
    # The field will be added once `user_data` app is implemented.
    taste_tags = models.ManyToManyField(TasteTag, related_name='ratings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Рейтинг продукта'
        verbose_name_plural = 'Рейтинги продуктов'
        indexes = [
            models.Index(fields=['rate', 'updated_at', 'created_at']),
        ]
    
    def __str__(self):
        return f'Rating {self.rate} for {self.product.name}'