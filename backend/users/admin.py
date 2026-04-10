from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Role access", {"fields": ("role",)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Role access", {"fields": ("role",)}),
    )
