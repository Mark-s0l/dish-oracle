from django.contrib import admin
from food_hub.models import TasteTag, Category, Country, Company, Product, ProductRating

@admin.register(TasteTag)
class TasteTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'taste_type')
    list_filter = ('taste_type',)
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('taste_tags',)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    list_filter = ('country',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'category', 'created_at')
    list_filter = ('company', 'category', 'created_at')
    search_fields = ('name', 'ean_code')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProductRating)
class ProductRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'rate', 'created_at')
    list_filter = ('rate', 'created_at')
    search_fields = ('product__name', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('taste_tags',)

