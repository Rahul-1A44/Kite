from django import forms
from django.contrib.auth import get_user_model
from .models import Organization, Message, Job 

# ✅ Import these for the Manual Candidate Form
from application_tracking.models import JobApplication, JobAdvert

User = get_user_model()

# ---------------------------------------------------
# 1. ORGANIZATION REGISTRATION FORM
# ---------------------------------------------------
class OrganizationRegistrationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'contact_email', 'phone_number', 'registration_number', 'website']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all duration-200 outline-none', 
                'placeholder': 'e.g. Kite Technologies Pvt Ltd'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all duration-200 outline-none', 
                'placeholder': 'hr@company.com'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all duration-200 outline-none', 
                'placeholder': '+977 9800000000'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all duration-200 outline-none', 
                'placeholder': 'Govt. Reg No.'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all duration-200 outline-none', 
                'placeholder': 'https://www.company.com'
            }),
        }

# ---------------------------------------------------
# 2. FORCE PASSWORD CHANGE FORM
# ---------------------------------------------------
class ForcePasswordChangeForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition',
            'placeholder': 'New Password'
        }),
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition',
            'placeholder': 'Confirm New Password'
        }),
        label="Confirm Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

# ---------------------------------------------------
# 3. MESSAGE FORM (✅ UPDATED FOR ATTACHMENTS)
# ---------------------------------------------------
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'attachment'] # ✅ Added attachment
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none transition resize-none',
                'placeholder': 'Type your message here...',
                'rows': '3'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            })
        }

    def clean(self):
        """Ensure either text OR file is provided."""
        cleaned_data = super().clean()
        content = cleaned_data.get("content")
        attachment = cleaned_data.get("attachment")

        if not content and not attachment:
            raise forms.ValidationError("You must write a message or attach a file.")
        
        return cleaned_data

# ---------------------------------------------------
# 4. JOB POSTING FORM
# ---------------------------------------------------
class JobPostForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'location', 'job_type', 'salary_range', 'deadline', 'description', 'requirements']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none', 'placeholder': 'e.g. Senior Python Developer'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none', 'placeholder': 'e.g. Kathmandu / Remote'}),
            'job_type': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none'}),
            'salary_range': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none', 'placeholder': 'e.g. NRs. 50,000 - 80,000'}),
            'deadline': forms.DateInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none', 'rows': 4, 'placeholder': 'Job responsibilities...'}),
            'requirements': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none', 'rows': 4, 'placeholder': 'Skills required...'}),
        }

# ---------------------------------------------------
# 5. MANUAL CANDIDATE FORM
# ---------------------------------------------------
class ManualCandidateForm(forms.ModelForm):
    # Extra fields for manual entry (since User might not exist yet)
    full_name = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none', 'placeholder': 'Candidate Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none', 'placeholder': 'candidate@email.com'})
    )

    class Meta:
        model = JobApplication
        fields = ['job_advert', 'status', 'cv']
        widgets = {
            'job_advert': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none'}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none'}),
            'cv': forms.FileInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white focus:ring-2 focus:ring-blue-500 outline-none'}),
        }

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org', None)
        super().__init__(*args, **kwargs)
        if org:
            # Only show jobs created by the organization's admin
            self.fields['job_advert'].queryset = JobAdvert.objects.filter(created_by=org.admin_user)