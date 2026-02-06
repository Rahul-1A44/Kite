from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # 1. The fields to display in the user list (removed 'username', 'first_name', 'last_name')
    list_display = ('email', 'is_staff', 'is_active', 'is_superuser')
    
    # 2. The field to use for ordering (removed 'username')
    ordering = ('email',)
    
    # 3. The fields to search for
    search_fields = ('email',)
    
    # 4. The form layout for the "Edit User" page
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # 5. The form layout for the "Add User" page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password'), # removed 'username'
        }),
    )

# Register your custom user with the custom admin class
admin.site.register(User, CustomUserAdmin)