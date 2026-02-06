import json
import uuid  
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.urls import reverse

from accounts.models import User
from application_tracking.enums import ApplicationStatus
from common.tasks import send_email

# Import Job & Organization Models
# ✅ Added Organization to imports for Dashboard check
from organization.models import Job, Message, Organization 
from organization.forms import JobPostForm 

from .forms import (
    JobAdvertForm, 
    JobApplicationForm, 
    UserProfileForm, 
    ExperienceForm, 
    EducationForm, 
    SkillForm,
    TaskSubmissionForm,
    CandidateMessageForm
)

from .models import (
    JobAdvert, 
    JobApplication, 
    UserProfile, 
    Experience, 
    Education, 
    Skill,
    Notification
)

from .utils import (
    extract_text_from_file, 
    get_match_score, 
    extract_missing_skills, 
    get_learning_resources
)

# --- HELPER: NOTIFICATIONS ---
def notify_relevant_users(job_instance):
    # Safe check for skills attribute
    if not hasattr(job_instance, 'skills') or not job_instance.skills:
        return

    job_skills = [s.strip() for s in job_instance.skills.split(',') if s.strip()]
    if not job_skills: return

    if hasattr(job_instance, 'organization'):
        creator_id = job_instance.organization.admin_user.id
    elif hasattr(job_instance, 'created_by'):
        creator_id = job_instance.created_by.id
    else:
        creator_id = None

    matched_candidates = User.objects.filter(
        user_skills__name__in=job_skills
    ).exclude(id=creator_id).distinct()

    notifications_to_create = []
    for user in matched_candidates:
        notifications_to_create.append(
            Notification(
                user=user,
                title=f"New Job Match: {job_instance.title}",
                message=f"A new opening matches your skill set.",
                link=f"/job/{job_instance.id}/"
            )
        )
    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create)


# ---------------------------------------------------
# 1. HOME PAGE
# ---------------------------------------------------
def home(request: HttpRequest):
    active_jobs = Job.objects.filter(is_active=True).order_by('-posted_at')[:6]
    return render(request, "home.html", {"jobs": active_jobs})


# ---------------------------------------------------
# 2. JOB DETAIL & APPLICATION
# ---------------------------------------------------
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    return render(request, 'job_detail.html', {'job': job})

def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data["email"]
            if job.applications.filter(email__iexact=email).exists():
                messages.error(request, "You have already applied for this position.")
                return redirect("job_detail", job_id=job.id)

            application = form.save(commit=False)
            application.job = job 
            if request.user.is_authenticated:
                application.user = request.user
            application.save()

            if request.user.is_authenticated:
                Notification.objects.create(
                    user=request.user,
                    title=f"Applied: {job.title}",
                    message=f"Success! You applied to {job.organization.name}.",
                    link=reverse('my_applications')
                )

            messages.success(request, "Application submitted successfully!")
            return redirect("job_detail", job_id=job.id)
    
    return redirect("job_detail", job_id=job.id)


# ---------------------------------------------------
# 3. INTERVIEW MANAGEMENT
# ---------------------------------------------------
@login_required
def user_interviews(request):
    interviews = JobApplication.objects.filter(
        user=request.user,
        status='INTERVIEWING'
    ).order_by('-updated_at')
    return render(request, 'user_interview_list.html', {'interviews': interviews})

@login_required
def user_interview_room(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id, user=request.user)
    task_form = TaskSubmissionForm(instance=application)
    chat_form = CandidateMessageForm()

    if application.job:
        org_user = application.job.organization.admin_user
    elif application.job_advert:
        org_user = application.job_advert.created_by
    else:
        org_user = None

    if request.method == 'POST':
        if 'submit_task' in request.POST:
            task_form = TaskSubmissionForm(request.POST, request.FILES, instance=application)
            if task_form.is_valid():
                app = task_form.save(commit=False)
                app.task_submitted_at = timezone.now()
                app.save()
                
                if org_user:
                    Message.objects.create(
                        sender=request.user,
                        receiver=org_user,
                        content="[SYSTEM]: I have submitted the required task file.",
                        attachment=app.task_submission,
                        is_read=False
                    )
                messages.success(request, "Task submitted successfully!")
                return redirect('user_interview_room', application_id=application.id)

        elif 'send_message' in request.POST:
            chat_form = CandidateMessageForm(request.POST, request.FILES)
            if chat_form.is_valid():
                msg = chat_form.save(commit=False)
                msg.sender = request.user
                msg.receiver = org_user
                msg.save()
                return redirect('user_interview_room', application_id=application.id)

    if org_user:
        chat_history = Message.objects.filter(
            Q(sender=request.user, receiver=org_user) | 
            Q(sender=org_user, receiver=request.user)
        ).order_by('timestamp')
        Message.objects.filter(sender=org_user, receiver=request.user, is_read=False).update(is_read=True)
    else:
        chat_history = []

    context = {
        'application': application,
        'chat_history': chat_history,
        'task_form': task_form,
        'chat_form': chat_form
    }
    return render(request, 'user_interview_room.html', context)


# ---------------------------------------------------
# 4. ORGANIZATION DASHBOARD VIEWS
# ---------------------------------------------------
@login_required
def my_jobs(request: HttpRequest):
    jobs = Job.objects.filter(organization__admin_user=request.user).order_by('-posted_at')
    paginator = Paginator(jobs, 10)
    return render(request, "my_jobs.html", {
        "my_jobs": paginator.get_page(request.GET.get("page")), 
        "current_date": timezone.now().date()
    })

# ---------------------------------------------------
# 5. LEGACY / UPDATED VIEWS
# ---------------------------------------------------

@login_required
def advert_applications(request: HttpRequest, advert_id):
    # Try New System First
    try:
        if str(advert_id).isdigit():
            job = Job.objects.get(pk=advert_id)
            if job.organization.admin_user != request.user:
                return HttpResponseForbidden("Permission denied.")
            applications = job.applications.all().order_by('-created_at')
            paginator = Paginator(applications, 10)
            return render(request, "advert_applications.html", {
                "applications": paginator.get_page(request.GET.get("page")), 
                "advert": job 
            })
    except Job.DoesNotExist:
        pass

    # Try Legacy System
    try:
        uuid_obj = uuid.UUID(str(advert_id))
        advert = get_object_or_404(JobAdvert, pk=uuid_obj)
        if request.user != advert.created_by: 
            return HttpResponseForbidden()
        applications = advert.applications.all()
        paginator = Paginator(applications, 10)
        return render(request, "advert_applications.html", {
            "applications": paginator.get_page(request.GET.get("page")), 
            "advert": advert
        })
    except ValueError:
        return HttpResponseForbidden("Invalid Job ID")

@login_required
def update_advert(request: HttpRequest, advert_id):
    # Try New System
    if str(advert_id).isdigit():
        try:
            job = Job.objects.get(pk=advert_id)
            if job.organization.admin_user != request.user:
                return HttpResponseForbidden()
            
            form = JobPostForm(request.POST or None, instance=job)
            if form.is_valid():
                form.save()
                messages.success(request, "Job updated successfully!")
                return redirect("my_jobs")
            
            return render(request, "create_advert.html", {
                "job_advert_form": form, 
                "title": "Edit Job", 
                "btn_text": "Update Job"
            })
        except Job.DoesNotExist:
            pass

    # Try Legacy System
    try:
        uuid_obj = uuid.UUID(str(advert_id))
        advert = get_object_or_404(JobAdvert, pk=uuid_obj)
        if request.user != advert.created_by: 
            return HttpResponseForbidden()
        
        form = JobAdvertForm(request.POST or None, instance=advert)
        if form.is_valid():
            form.save()
            return redirect(advert.get_absolute_url())
        return render(request, "create_advert.html", {"job_advert_form": form, "btn_text": "Update advert"})
    except ValueError:
        return redirect("my_jobs")

@login_required
def delete_advert(request: HttpRequest, advert_id):
    # New System
    if str(advert_id).isdigit():
        try:
            job = Job.objects.get(pk=advert_id)
            if job.organization.admin_user != request.user:
                return HttpResponseForbidden()
            job.delete()
            messages.success(request, "Job deleted.")
            return redirect("my_jobs")
        except Job.DoesNotExist:
            pass

    # Legacy System
    try:
        uuid_obj = uuid.UUID(str(advert_id))
        advert = get_object_or_404(JobAdvert, pk=uuid_obj)
        if request.user != advert.created_by: 
            return HttpResponseForbidden()
        advert.delete()
        return redirect("my_jobs")
    except ValueError:
        return redirect("my_jobs")

@login_required
def job_applications(request, job_id):
    return advert_applications(request, job_id)

@login_required
def decide(request: HttpRequest, job_application_id):
    job_application = get_object_or_404(JobApplication, pk=job_application_id)
    
    if job_application.job:
        owner = job_application.job.organization.admin_user
    elif job_application.job_advert:
        owner = job_application.job_advert.created_by
    else:
        owner = None
    
    if request.user != owner:
        return HttpResponseForbidden("Permission denied.")
    
    if request.method == "POST":
        status = request.POST.get("status")
        job_application.status = status
        job_application.save(update_fields=["status"])
        
        applicant_user = User.objects.filter(email=job_application.email).first()
        title = job_application.job.title if job_application.job else job_application.job_advert.title
        
        if applicant_user:
            msg = f"Your application for {title} was updated to: {status}."
            if status == ApplicationStatus.ACCEPTED:
                msg = f"Congratulations! You were ACCEPTED for {title}!"
            elif status == ApplicationStatus.REJECTED:
                msg = f"Update: Your application for {title} was not successful."

            Notification.objects.create(
                user=applicant_user,
                title="Application Status Update",
                message=msg,
                link=reverse('my_applications')
            )

        messages.success(request, f"Application status updated to {status}")

        if status == ApplicationStatus.REJECTED:
            job_title = job_application.job.title if job_application.job else job_application.job_advert.title
            company = job_application.job.organization.name if job_application.job else job_application.job_advert.company_name
            
            context = {
                "applicant_name": job_application.name,
                "job_title": job_title,
                "company_name": company,
            }
            send_email.delay(
                f"Application Outcome for {job_title}",
                [job_application.email],
                "emails/job_application_update.html",
                context
            )
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def create_advert(request: HttpRequest):
    form = JobAdvertForm(request.POST or None)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.created_by = request.user
        instance.save()
        notify_relevant_users(instance)
        messages.success(request, "Advert created.")
        return redirect(instance.get_absolute_url())

    context = {"job_advert_form": form, "title": "Create a new advert", "btn_text": "Create advert"}
    return render(request, "create_advert.html", context)

# ---------------------------------------------------
# ✅ APPLY PAGE
# ---------------------------------------------------
def jobs_apply(request: HttpRequest):
    jobs = Job.objects.filter(is_active=True).order_by('-posted_at')
    
    keyword = request.GET.get("keyword")
    location = request.GET.get("location")
    
    if keyword:
        jobs = jobs.filter(
            Q(title__icontains=keyword) | 
            Q(organization__name__icontains=keyword)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
        
    paginator = Paginator(jobs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    
    return render(request, "jobs_apply.html", {
        "job_adverts": page_obj, 
        "keyword": keyword,
        "location": location
    })

def search(request: HttpRequest):
    return jobs_apply(request)

def get_advert(request: HttpRequest, advert_id):
    # Handle both ID types for Viewing
    if str(advert_id).isdigit():
        return job_detail(request, int(advert_id))
    
    try:
        uuid_obj = uuid.UUID(str(advert_id))
        job_advert = get_object_or_404(JobAdvert, pk=uuid_obj)
        has_applied = False
        if request.user.is_authenticated:
            has_applied = job_advert.applications.filter(email=request.user.email).exists()
        form = JobApplicationForm()
        if request.user.is_authenticated:
            form.fields['name'].initial = f"{request.user.first_name} {request.user.last_name}"
            form.fields['email'].initial = request.user.email
        return render(request, "advert.html", {"job_advert": job_advert, "application_form": form, "has_applied": has_applied})
    except ValueError:
        return redirect('jobs_apply')

# ---------------------------------------------------
# ✅ UPDATED: ANALYZE RESUME (SAFE & CRASH-PROOF)
# ---------------------------------------------------
def analyze_resume(request, advert_id):
    if request.method == "POST" and request.FILES.get('resume'):
        job = None # Initialize job variable safely
        try:
            full_text = ""
            
            # 1. SMART ID RESOLUTION & SAFE TEXT EXTRACTION
            if str(advert_id).isdigit():
                # NEW SYSTEM (Integer ID)
                try:
                    job = Job.objects.get(pk=advert_id)
                except Job.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Job ID not found.'})
            else:
                # LEGACY SYSTEM (UUID)
                try:
                    uuid_obj = uuid.UUID(str(advert_id))
                    job = get_object_or_404(JobAdvert, pk=uuid_obj)
                except (ValueError, JobAdvert.DoesNotExist):
                    return JsonResponse({'status': 'error', 'message': 'Invalid Job Reference.'})

            # ✅ CRITICAL FIX: SAFELY GET SKILLS (Prevents "no attribute 'skills'" error)
            skills_text = ""
            if hasattr(job, 'skills'):
                # Check if it is a Many-to-Many relationship manager or a simple string
                if hasattr(job.skills, 'all'):
                    skills_text = ", ".join([str(s) for s in job.skills.all()])
                else:
                    skills_text = str(job.skills)
            elif hasattr(job, 'required_skills'): # Try alternative name
                skills_text = str(job.required_skills)
            else:
                # If no specific skills field, defaults to empty.
                # AI will infer skills from description.
                skills_text = "Refer to job description"
            
            # Construct the prompt text safely
            full_text = f"Job Title: {job.title}\n\nDescription: {job.description}\n\nRequired Skills: {skills_text}"

            # 2. Extract Resume Text
            uploaded_file = request.FILES['resume']
            resume_text = extract_text_from_file(uploaded_file)
            
            if not resume_text or len(resume_text) < 50: 
                return JsonResponse({'status': 'error', 'message': 'Could not extract text. Please upload a clear PDF or DOCX.'})
            
            # 3. AI Analysis
            analysis_result = get_match_score(resume_text, full_text)
            
            score = analysis_result.get('score', 0)
            missing = analysis_result.get('missing_skills', [])
            reason = analysis_result.get('reason', 'Analysis Complete')
            redirect_url = None

            # 4. Response Logic
            if score >= 70:
                status = 'success'
                msg = f"Great Match! Score: {score}%. {reason}"
                
                if isinstance(job, Job):
                    redirect_url = reverse('job_detail', kwargs={'job_id': advert_id})
                else:
                    redirect_url = reverse('job_advert', kwargs={'advert_id': advert_id})
            else:
                status = 'fail'
                msg = f"Low Match ({score}%). {reason}"

            # ✅ UPDATED: Sending job_title so frontend can create the Learning Sources link
            return JsonResponse({
                'status': status,
                'message': msg,
                'missing_skills': missing,
                'job_title': job.title, 
                'redirect_url': redirect_url
            })

        except Exception as e:
            # Log exact error to console for debugging
            print(f"❌ Analysis Error: {e}")
            # ✅ FALLBACK: Return error BUT include job_title if we found it
            # This ensures the button links to "Python Developer" instead of "AI Service Unavailable"
            return JsonResponse({
                'status': 'error', 
                'message': f"AI Service Unavailable (Check API Key)", 
                'score': 0,
                'missing_skills': [],
                'job_title': job.title if job else "General Career Skills", 
                'redirect_url': None
            })
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def notifications_view(request):
    all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(all_notifications, 10)
    return render(request, "notifications.html", {"notifications": paginator.get_page(request.GET.get('page'))})

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)

@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications')

def sources_page(request): return render(request, 'sources.html')

def get_sources_api(request):
    if request.method == "GET":
        topic = request.GET.get('topic', '').strip()
        data = get_learning_resources(topic) if topic else None
        return JsonResponse({'status': 'success', 'data': data}) if data else JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

def apply(request: HttpRequest, advert_id): 
    return redirect("job_advert", advert_id=advert_id)

@login_required
def my_applications(request: HttpRequest):
    applications = JobApplication.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(applications, 10)
    return render(request, "my_applications.html", {"my_applications": paginator.get_page(request.GET.get("page"))})


# ---------------------------------------------------
# ✅ UPDATED: DASHBOARD (GATEKEEPER)
# ---------------------------------------------------
@login_required
def dashboard(request: HttpRequest):
    """
    Organization Dashboard.
    Gatekeeper: Checks if the user actually has an Organization profile.
    """
    # 1. Check if the logged-in user is an Admin of any Organization
    has_org = Organization.objects.filter(admin_user=request.user).exists()

    # 2. If NO Organization found, redirect to the prompt page
    if not has_org:
        messages.warning(request, "You need an Organization profile to access the dashboard.")
        return redirect('org_setup_prompt') 

    # 3. If YES, render the dashboard normally
    return render(request, "dashboard.html")

# --- NEW VIEW: The "Stop & Suggest" Page ---
@login_required
def org_setup_prompt(request):
    """
    Landing page for users who try to access Dashboard without an Org profile.
    """
    return render(request, "org_setup_prompt.html")

@login_required
def profile_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        if 'edit_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid(): profile_form.save()
        elif 'add_experience' in request.POST:
            exp_form = ExperienceForm(request.POST)
            if exp_form.is_valid():
                exp = exp_form.save(commit=False)
                exp.user = user
                exp.save()
        elif 'add_education' in request.POST:
            edu_form = EducationForm(request.POST)
            if edu_form.is_valid():
                edu = edu_form.save(commit=False)
                edu.user = user
                edu.save()
        elif 'add_skill' in request.POST:
            skill_form = SkillForm(request.POST)
            if skill_form.is_valid():
                skill = skill_form.save(commit=False)
                skill.user = user
                skill.save()
        return redirect('user_profile')

    context = {
        'user': user,
        'profile': profile,
        'experiences': Experience.objects.filter(user=user).order_by('-start_date'),
        'education': Education.objects.filter(user=user).order_by('-start_date'),
        'skills': Skill.objects.filter(user=user),
        'profile_form': UserProfileForm(instance=profile),
        'exp_form': ExperienceForm(),
        'edu_form': EducationForm(),
        'skill_form': SkillForm(),
    }
    return render(request, "profile.html", context)