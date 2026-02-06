from django.contrib import admin
from .models import Organization, Payment

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'subdomain', 'status', 'contact_email', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'subdomain', 'registration_number')
    readonly_fields = ('subdomain',) # Prevent accidental changes after creation

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('organization', 'amount', 'status', 'transaction_id', 'created_at')
    list_filter = ('status',)