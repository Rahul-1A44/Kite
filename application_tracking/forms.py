from django import forms
from django.forms import ModelForm
from .models import JobAdvert, JobApplication, UserProfile, Experience, Education, Skill
# ✅ Import Message from Organization app for the chat form
from organization.models import Message

# ===========================
# 1. JOB ADVERT FORM
# ===========================
class JobAdvertForm(ModelForm):
    class Meta:
        model = JobAdvert
        fields = [
            "title", "company_name", "employment_type", "experience_level", 
            "job_type", "location", "description", "skills", 
            "is_published", "deadline"
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder":"Job title", "class":"form-control"}),
            "description": forms.Textarea(attrs={"placeholder":"Description", "class":"form-control"}),
            "company_name": forms.TextInput(attrs={"placeholder":"Company name", "class":"form-control"}),
            "employment_type": forms.Select(attrs={"class":"form-control"}),
            "experience_level": forms.Select(attrs={"class":"form-control"}),
            "job_type": forms.Select(attrs={"class":"form-control"}),
            "location": forms.TextInput(attrs={"placeholder":"Optional", "class":"form-control"}),
            "deadline": forms.DateInput(attrs={"placeholder":"Date", "class":"form-control", "type":"date"}),
            "skills": forms.TextInput(attrs={"placeholder":"Comma separated skills", "class":"form-control"}),
        }

# ===========================
# 2. JOB APPLICATION FORM
# ===========================
class JobApplicationForm(ModelForm):
    class Meta:
        model = JobApplication
        fields = ["name", "email", "portfolio_url", "cv"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "class":"form-control"}),
            "email": forms.EmailInput(attrs={"placeholder": "Your email", "class":"form-control"}),
            "portfolio_url": forms.URLInput(attrs={"placeholder": "Portfolio link", "class":"form-control"}),
            "cv": forms.FileInput(attrs={"placeholder": "Select your cv", "class":"form-control", "accept":".pdf, .docx, .doc"}),
        }

# ===========================
# 3. PROFILE PAGE FORMS
# ===========================
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'headline', 'bio', 'location', 'phone', 'portfolio_url']
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Software Engineer...'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Tell us about yourself...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Country'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+977-...'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['job_title', 'company_name', 'start_date', 'end_date', 'description', 'is_current']
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['institution', 'degree', 'start_date', 'end_date']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, etc.'}),
        }

# ===========================
# 4. INTERVIEW & CHAT FORMS
# ===========================
class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['task_submission']
        widgets = {
            'task_submission': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            })
        }

class CandidateMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'attachment']  # ✅ Added attachment
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none transition',
                'placeholder': 'Type your answer or message here...',
                'rows': '3'
            }),
            'attachment': forms.FileInput(attrs={  # ✅ Added widget
                'class': 'mt-2 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            })
        }