from django.contrib import admin
from .models import (
    JobAdvert, 
    JobApplication, 
    UserProfile, 
    Experience, 
    Education, 
    Skill, 
    Notification,
    ActivityLog
)

# 1. Register simple models
admin.site.register(JobAdvert)
admin.site.register(JobApplication)
admin.site.register(UserProfile)
admin.site.register(Experience)
admin.site.register(Education)
admin.site.register(Skill)
admin.site.register(Notification)

# 2. Register ActivityLog with a nice list view (Read-Only recommended)
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action_type', 'description', 'ip_address')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('actor__email', 'description')
    readonly_fields = ('timestamp', 'actor', 'action_type', 'description', 'ip_address', 'target_object')
    
    # Prevent adding/changing logs manually (logs should be automatic)
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False