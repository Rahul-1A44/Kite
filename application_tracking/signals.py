import logging
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

# Import your models
from accounts.models import User
from .models import ActivityLog, JobAdvert, JobApplication, UserProfile

# --- Helper Function: Get IP Address ---
def get_client_ip(request):
    """
    Safely extract the IP address from the request.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# ==========================================
# 1. LOG USER LOGIN
# ==========================================
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        actor=user,
        action_type='LOGIN',
        description="User logged in successfully.",
        ip_address=get_client_ip(request),
        timestamp=timezone.now()
    )

# ==========================================
# 2. LOG USER LOGOUT
# ==========================================
@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        ActivityLog.objects.create(
            actor=user,
            action_type='LOGOUT',
            description="User logged out.",
            ip_address=get_client_ip(request),
            timestamp=timezone.now()
        )

# ==========================================
# 3. LOG USER REGISTRATION
# ==========================================
@receiver(post_save, sender=User)
def log_user_registration(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            actor=instance,
            action_type='USER_REGISTER',
            description=f"New account created: {instance.email}",
            timestamp=timezone.now()
        )

# ==========================================
# 4. LOG JOB CREATION & UPDATES
# ==========================================
@receiver(post_save, sender=JobAdvert)
def log_job_advert(sender, instance, created, **kwargs):
    if created:
        action = 'JOB_CREATE'
        desc = f"Job '{instance.title}' was created."
    else:
        action = 'JOB_UPDATE'
        desc = f"Job '{instance.title}' was updated."
    
    # Use the job creator as the actor
    actor = instance.created_by
    
    ActivityLog.objects.create(
        actor=actor,
        action_type=action,
        description=desc,
        target_object=f"Job ID: {instance.id}",
        timestamp=timezone.now()
    )

# ==========================================
# 5. LOG APPLICATIONS & STATUS CHANGES (✅ FIXED)
# ==========================================
@receiver(post_save, sender=JobApplication)
def log_application(sender, instance, created, **kwargs):
    # ✅ FIX: Handle New 'Job' (via Organization) vs Old 'JobAdvert'
    if instance.job:
        job_title = instance.job.title
        
        # 1. Try to get the Organization Admin (New System)
        if hasattr(instance.job, 'organization') and instance.job.organization:
            employer = instance.job.organization.admin_user
        # 2. Fallback: Try 'created_by' directly (in case model differs)
        elif hasattr(instance.job, 'created_by'):
            employer = instance.job.created_by
        else:
            employer = None
            
    elif instance.job_advert:
        # Legacy System
        job_title = instance.job_advert.title
        employer = instance.job_advert.created_by
    else:
        job_title = "Unknown Job"
        employer = None

    if created:
        # 1. New Application Log
        # If the user is logged in (linked), use that. Otherwise try email match.
        applicant_user = instance.user 
        if not applicant_user:
            applicant_user = User.objects.filter(email=instance.email).first()
        
        # Only log if we found a user to act as the 'actor'
        if applicant_user:
            ActivityLog.objects.create(
                actor=applicant_user, 
                action_type='JOB_APPLIED',
                description=f"{instance.name} applied for {job_title}",
                target_object=f"App ID: {instance.id}",
                timestamp=timezone.now()
            )
    else:
        # 2. Status Change Log (e.g., Pending -> Accepted)
        # We assume the employer is the one changing the status
        if employer:
            ActivityLog.objects.create(
                actor=employer,
                action_type='APP_STATUS',
                description=f"Updated application for {instance.name} to '{instance.status}'",
                target_object=f"Job: {job_title}",
                timestamp=timezone.now()
            )

# ==========================================
# 6. LOG PROFILE UPDATES
# ==========================================
@receiver(post_save, sender=UserProfile)
def log_profile_update(sender, instance, created, **kwargs):
    if not created: # Only log updates, creation happens automatically on register
        ActivityLog.objects.create(
            actor=instance.user,
            action_type='PROFILE_UPDATE',
            description="User updated their profile details.",
            timestamp=timezone.now()
        )