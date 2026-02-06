from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Organization

@receiver(pre_save, sender=Organization)
def check_status_change(sender, instance, **kwargs):
    """
    Checks if the status is changing from 'PENDING' to 'VERIFIED'.
    This runs BEFORE the save to capture the old status.
    """
    if instance.pk:
        try:
            old_instance = Organization.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Organization.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Organization)
def send_verification_email(sender, instance, created, **kwargs):
    """
    Sends email if status changed to 'VERIFIED'.
    """
    # Check if the status has actually changed to VERIFIED
    if hasattr(instance, '_old_status') and instance._old_status != 'VERIFIED' and instance.status == 'VERIFIED':
        
        # ✅ FIX 1: Use contact_email instead of admin_user
        # The User account (admin_user) is usually created AFTER payment, so it might be None here.
        recipient_email = instance.contact_email 
        
        # ✅ FIX 2: Generate the link to the Status Page
        # This is where the user needs to go to click the "Pay" button.
        # Ensure SITE_URL is defined in settings.py, or default to localhost
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        payment_link = f"{base_url}/organization/status/{instance.id}/"

        subject = "Action Required: Your Organization is Verified!"
        message = f"""
        Hi,

        Great news! Your organization "{instance.name}" has been verified by our admin team.

        To activate your account and receive your login password, please complete the registration fee payment.

        Click the link below to proceed to payment:
        {payment_link}
        
        Regards,
        The Administration Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
                fail_silently=False,
            )
            print(f"✅ Verification email sent to {recipient_email}")
        except Exception as e:
            # Print error to terminal so you can debug if SMTP fails
            print(f"❌ Email failed to send: {e}")