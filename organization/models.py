from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid

# ---------------------------------------------------
# 1. ORGANIZATION MODEL
# ---------------------------------------------------
class Organization(models.Model):
    # Workflow Stages
    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'), # 1. Registered, waiting for Admin
        ('VERIFIED', 'Verified'),            # 2. Approved, waiting for Payment
        ('ACTIVE', 'Active'),                # 3. Paid & Live
        ('SUSPENDED', 'Suspended'),          # 4. Blocked
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, verbose_name="Organization Name")
    
    # ✅ Subdomain: e.g., if name is "Kite Tech", subdomain is "kite-tech"
    subdomain = models.SlugField(max_length=100, unique=True, help_text="Unique subdomain identifier")

    # Legal / Contact Info
    registration_number = models.CharField(max_length=100, unique=True)
    tax_id = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='org_logos/', null=True, blank=True)

    # Linked User: This user is created ONLY after payment success
    admin_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='organization_owned'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # ✅ Force Password Change
    must_change_password = models.BooleanField(default=True, help_text="If True, admin must change password on next login.")

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate subdomain from name if not provided
        if not self.subdomain:
            self.subdomain = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.status})"

# ---------------------------------------------------
# 2. PAYMENT MODEL
# ---------------------------------------------------
class Payment(models.Model):
    PAYMENT_GATEWAY_CHOICES = [('KHALTI', 'Khalti')]
    STATUS_CHOICES = [('INITIATED', 'Initiated'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payments')
    
    # Khalti Transaction Data
    transaction_id = models.CharField(max_length=100, unique=True) # pidx
    amount = models.DecimalField(max_digits=10, decimal_places=2) # e.g. 5000.00
    gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAY_CHOICES, default='KHALTI')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    
    verified_token = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization.name} - {self.status}"

# ---------------------------------------------------
# 3. MESSAGE MODEL
# ---------------------------------------------------
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    
    # ✅ FIX: Content is optional if a file is attached
    content = models.TextField(blank=True, null=True)
    
    # ✅ NEW: Attachment Field for PDF/Word Docs
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp'] # Oldest messages first (Chat log style)

    def __str__(self):
        return f"Msg from {self.sender} to {self.receiver}"

# ---------------------------------------------------
# 4. JOB MODEL (✅ New Addition for Job Posting)
# ---------------------------------------------------
class Job(models.Model):
    JOB_TYPES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERNSHIP', 'Internship'),
        ('FREELANCE', 'Freelance'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=100, default="Remote")
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='FULL_TIME')
    salary_range = models.CharField(max_length=100, blank=True)
    
    description = models.TextField()
    requirements = models.TextField(help_text="List key requirements")
    
    posted_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} at {self.organization.name}"

    class Meta:
        ordering = ['-posted_at']