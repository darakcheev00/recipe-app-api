"""Django admin customization"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core import models

class UserAdmin(BaseUserAdmin):
    """Define the amdin pages for users."""
    ordering = ['id']
    list_display = ['email', 'name']


# provide useradmin as second arg because we want our custom changes to be picked up
admin.site.register(models.User, UserAdmin)