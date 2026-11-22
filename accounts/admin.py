from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin panel me User ko dikhane ka tarika.
    Role ko list me add kiya taaki filter karna easy ho.
    """

    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')

    # Existing fieldsets me role add karo
    fieldsets = UserAdmin.fieldsets + (
        ('PPC Role', {'fields': ('role',)}),
    )

    # Naya user banate waqt bhi role pooche
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('PPC Role', {'fields': ('role',)}),
    )