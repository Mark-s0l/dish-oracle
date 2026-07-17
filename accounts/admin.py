from django.contrib import admin
from accounts.models import CustomUser
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html


@admin.register(CustomUser)
class MyUserAdmin(UserAdmin):
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return '—'
    avatar_preview.short_description = 'Аватар'

    list_display = ['avatar_preview', 'username', 'email', 'first_name', 'last_name', 'is_staff']
    list_display_links = ['username']

    fieldsets = (
        ('Фото профиля', {'fields': ('avatar', 'avatar_preview')}),
    ) + UserAdmin.fieldsets

    readonly_fields = ['avatar_preview']

    add_fieldsets = (
        ('Фото профиля', {'fields': ('avatar',)}),
    ) + UserAdmin.add_fieldsets