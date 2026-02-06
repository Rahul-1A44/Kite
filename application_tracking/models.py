from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from accounts.models import User
from common.models import BaseModel
# ✅ Import Job from Organization app (Crucial for linking)
from organization.models import Job

from .enums import (ApplicationStatus, EmploymentType, ExperienceLevel,
                    LocationTypeChoice)


class JobAdvertQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_published=True, deadline__gte=timezone.now().date())

    def search(self, keyword, location):
        query = Q()

        if keyword:
            query &= (
                Q(title__icontains=keyword)
                | Q(company_name__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(skills__icontains=keyword)
            )

        if location:
            query &= Q(location__icontains=location)

        return self.active().filter(query)


class JobAdvert(BaseModel):
    title = models.CharField(max_length=150)
    company_name =  models.CharField(max_length=150)
    employment_type = models.CharField(max_length=50, choices=EmploymentType)
    experience_level = models.CharField(max_length=50, choices=ExperienceLevel)
    description = models.TextField()
    job_type =  models.CharField(max_length=50, choices=LocationTypeChoice)
    location =  models.CharField(max_length=255, null=True, blank=True)
    is_published = models.BooleanField(default=True)
    deadline = models.DateField()
    skills = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = JobAdvertQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)

    def publish_advert(self) -> None:
        self.is_published = True
        self.save(update_fields=["is_published"])

    @property
    def total_applicants(self):
        return self.applications.count()
    
    def get_absolute_url(self):
        return reverse("job_advert", kwargs={"advert_id": self.id})
    

class JobApplication(BaseModel):
    # ✅ 1. User Link (Required for Chat & Interviews)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications", null=True, blank=True)
    
    name = models.CharField(max_length=50)
    email = models.EmailField()
    portfolio_url = models.URLField()
    cv = models.FileField()
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, 
                              default=ApplicationStatus.APPLIED)
    
    # ✅ 2. Allow Linking to Old 'JobAdvert' OR New 'Job'
    job_advert = models.ForeignKey(JobAdvert, related_name="applications", on_delete=models.CASCADE, null=True, blank=True)
    job = models.ForeignKey(Job, related_name="applications", on_delete=models.CASCADE, null=True, blank=True)

    # ✅ 3. Interview Stages
    INTERVIEW_STAGES = [
        ('PENDING', 'Pending Review'),
        ('HR_ROUND', 'HR Round'),
        ('TECH_ROUND', 'Technical Round'),
        ('FINAL_ROUND', 'Final Round'),
        ('HIRED', 'Hired'),
    ]
    interview_stage = models.CharField(max_length=20, choices=INTERVIEW_STAGES, default='PENDING')

    # ✅ 4. Task Submission (New Feature)
    task_submission = models.FileField(upload_to='candidate_tasks/', null=True, blank=True)
    task_submitted_at = models.DateTimeField(null=True, blank=True)

    # ✅ 5. AI Score (For Dashboard)
    ai_score = models.IntegerField(default=0, help_text="Overall AI Score")

    def get_user_account(self):
        """Helper to get the User object for chat"""
        if self.user:
            return self.user
        # Fallback: try to find user by email
        return User.objects.filter(email=self.email).first()
    
    def get_active_interview_session(self):
        return self.ai_sessions.filter(status='ACTIVE').first()


class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    headline = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. 'Software Engineer at Google'")
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"Profile of {self.user.email}"


class Experience(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiences')
    job_title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"


class Education(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=100)
    degree = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.degree} at {self.institution}"


class Skill(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_skills')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"


class ActivityLog(models.Model):
    ACTION_TYPES = (
        ('LOGIN', 'Login'),
        ('REGISTER', 'User Registration'),
        ('JOB_CREATE', 'Job Created'),
        ('JOB_UPDATE', 'Job Updated'),
        ('APPLIED', 'Job Applied'),
        ('STATUS_CHANGE', 'Application Status Changed'),
        ('PROFILE_UPDATE', 'Profile Updated'),
    )

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    target_object = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.actor} - {self.action_type} - {self.timestamp}"


# ==========================================================
#  ✅ AI INTERVIEW SYSTEM MODELS
# ==========================================================

class AIInterviewSession(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABANDONED', 'Abandoned'),
    )

    DECISION_CHOICES = (
        ('PENDING', 'Pending Decision'),
        ('HIRE', 'Recommended for Hire'),
        ('REJECT', 'Rejected by AI'),
        ('MANUAL_REVIEW', 'Needs Manual Review'),
    )

    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='ai_sessions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Results
    final_score = models.IntegerField(default=0, help_text="AI Score 0-100")
    ai_decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='PENDING')
    ai_feedback = models.TextField(blank=True, null=True, help_text="Evaluator feedback")
    
    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"AI Interview for {self.application.name} ({self.status})"


class AIInterviewLog(models.Model):
    ROLE_CHOICES = (
        ('AI', 'AI Interviewer'),
        ('USER', 'Candidate'),
        ('SYSTEM', 'System Event'),
    )

    session = models.ForeignKey(AIInterviewSession, on_delete=models.CASCADE, related_name='logs')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class CandidateTask(models.Model):
    STAGES = (
        ('HR', 'HR Round (Form)'),
        ('TECH', 'Technical Round (Code/Task)'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUBMITTED', 'Submitted'),
        ('GRADED', 'Graded'),
    )

    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='tasks')
    stage = models.CharField(max_length=10, choices=STAGES)
    
    # Task Content (The Question)
    task_content = models.TextField(help_text="The question or instruction for the candidate")
    
    # Candidate Response
    response_text = models.TextField(blank=True, null=True)
    response_file = models.FileField(upload_to='task_responses/', blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # AI Evaluation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    score = models.IntegerField(default=0)
    ai_feedback = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.stage} Task for {self.application.name}"