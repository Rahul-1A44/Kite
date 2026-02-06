import uuid
import json
import csv
import requests

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib import auth
from django.utils.crypto import get_random_string
from django.utils.html import format_html  # ✅ Added for Professional Alerts
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import HttpResponse

from .models import Organization, Payment, Message, Job 
from .forms import OrganizationRegistrationForm, ForcePasswordChangeForm, MessageForm, JobPostForm, ManualCandidateForm

from application_tracking.models import JobApplication, Notification

User = get_user_model()

# ---------------------------------------------------
# 1. REGISTRATION VIEW
# ---------------------------------------------------
def org_register(request):
    if request.method == 'POST':
        form = OrganizationRegistrationForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.status = 'PENDING'
            org.save()
            messages.success(request, "Registration successful! Verification Pending.")
            return redirect('org_status', org_id=org.id)
    else:
        form = OrganizationRegistrationForm()
    return render(request, 'organization/register.html', {'form': form})

# ---------------------------------------------------
# 2. STATUS PAGE
# ---------------------------------------------------
def org_status(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    return render(request, 'organization/status.html', {'org': org})

# ---------------------------------------------------
# 3. INITIATE PAYMENT
# ---------------------------------------------------
def init_payment(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    amount_rs = 100
    amount_paisa = amount_rs * 100 
    
    # ✅ FIX: Automatically get the current domain (e.g., http://127.0.0.1:8000)
    # This prevents errors if you switch ports or deploy to the web.
    base_url = request.build_absolute_uri('/')[:-1] 
    
    payload = {
        "return_url": settings.KHALTI_RETURN_URL,
        "website_url": base_url,
        "amount": amount_paisa,
        "purchase_order_id": str(org.id),
        "purchase_order_name": f"Registration Fee - {org.name}",
        "customer_info": {
            "name": org.name,
            "email": org.contact_email,
            "phone": org.phone_number
        }
    }
    
    headers = {
        "Authorization": settings.KHALTI_SECRET_KEY,
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(settings.KHALTI_INITIATE_URL, headers=headers, json=payload)
        data = response.json()
        
        if response.status_code == 200:
            Payment.objects.create(
                organization=org,
                transaction_id=data.get('pidx'),
                amount=amount_rs,
                status='INITIATED'
            )
            return redirect(data.get('payment_url'))
        else:
            messages.error(request, f"Khalti Error: {data.get('detail', 'Unknown error')}")
    except Exception as e:
        messages.error(request, f"Connection Error: {str(e)}")
        
    return redirect('org_status', org_id=org.id)

# ---------------------------------------------------
# 4. VERIFY PAYMENT (✅ INDUSTRIAL LEVEL UPDATE)
# ---------------------------------------------------
def verify_payment(request):
    pidx = request.GET.get('pidx')
    if not pidx:
        messages.error(request, "Payment failed or cancelled.")
        return redirect('home')

    headers = {
        "Authorization": settings.KHALTI_SECRET_KEY,
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(settings.KHALTI_LOOKUP_URL, headers=headers, json={'pidx': pidx})
        data = response.json()
        
        if data.get('status') == 'Completed':
            try:
                payment = Payment.objects.get(transaction_id=pidx)
                if payment.status == 'SUCCESS':
                    auth.logout(request)
                    messages.info(request, "Payment verified. Please login.")
                    return redirect('login')

                payment.status = 'SUCCESS'
                payment.verified_token = data.get('transaction_id')
                payment.save()
                
                org = payment.organization
                
                if not org.admin_user:
                    # 1. Generate Temp Password
                    temp_password = get_random_string(8)
                    
                    # 2. Check if user already exists
                    existing_user = User.objects.filter(email=org.contact_email).first()
                    
                    if existing_user:
                        # ✅ CRITICAL FIX: Reset password for existing user so you can see it
                        existing_user.set_password(temp_password)
                        existing_user.save()
                        org.admin_user = existing_user
                    else:
                        # Create new user
                        new_user = User.objects.create_user(email=org.contact_email, password=temp_password)
                        org.admin_user = new_user
                    
                    org.status = 'ACTIVE'
                    org.save()
                    
                    # 3. Send Email (Backend)
                    try:
                        send_mail(
                            subject="Welcome to Kite Organization",
                            message=f"Login: {org.contact_email}\nPassword: {temp_password}",
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[org.contact_email],
                            fail_silently=False,
                        )
                    except Exception:
                        pass # Ignore email errors, we show password on screen

                    # 4. ✅ INDUSTRIAL LEVEL HTML MESSAGE
                    formatted_message = format_html(
                        """
                        <div class="flex flex-col gap-1">
                            <strong class="text-base">Account Activated Successfully!</strong>
                            <div class="mt-2 flex items-center justify-between bg-white bg-opacity-60 border border-green-200 rounded-md p-3">
                                <span class="text-sm text-green-800 mr-2">Temp Password:</span>
                                <div class="flex items-center gap-2">
                                    <code class="font-mono font-bold text-lg text-green-900 tracking-wider select-all" id="pwd-box">{}</code>
                                    <button type="button" onclick="navigator.clipboard.writeText('{}').then(() => alert('Copied!'))" 
                                        class="text-xs bg-green-700 hover:bg-green-800 text-white px-3 py-1.5 rounded transition shadow-sm flex items-center gap-1">
                                        <i class="fa-regular fa-copy"></i> Copy
                                    </button>
                                </div>
                            </div>
                            <span class="text-xs mt-1 opacity-80">Please log in and change your password immediately.</span>
                        </div>
                        """,
                        temp_password, 
                        temp_password
                    )

                    messages.success(request, formatted_message)
                    
                    auth.logout(request)
                return redirect('login')
                
            except Payment.DoesNotExist:
                messages.error(request, "Payment record not found.")
        else:
            messages.error(request, f"Payment Status: {data.get('status')}")
            
    except Exception as e:
        messages.error(request, f"Verification Error: {str(e)}")
    
    return redirect('home')

# ---------------------------------------------------
# 5. DASHBOARD VIEW
# ---------------------------------------------------
@login_required
def org_dashboard(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        messages.error(request, "You do not have an Organization account.")
        return redirect('home')

    if org.must_change_password:
        return redirect('org_change_password')

    if org.status != 'ACTIVE':
        return redirect('org_status', org_id=org.id)

    jobs = Job.objects.filter(organization=org)
    active_jobs_count = jobs.filter(is_active=True).count()
    total_applicants = JobApplication.objects.filter(job__in=jobs).count()
    recent_jobs = jobs.order_by('-posted_at')[:3]

    context = {
        'org': org,
        'active_jobs_count': active_jobs_count,
        'total_applicants': total_applicants,
        'recent_jobs': recent_jobs
    }
    return render(request, 'organization/dashboard.html', context)

# ---------------------------------------------------
# 6. FORCE PASSWORD CHANGE VIEW
# ---------------------------------------------------
@login_required
def org_change_password(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')
    
    if not org.must_change_password:
        return redirect('org_dashboard')

    if request.method == 'POST':
        form = ForcePasswordChangeForm(request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)
            org.must_change_password = False
            org.save()
            messages.success(request, "Password updated successfully!")
            return redirect('org_dashboard')
    else:
        form = ForcePasswordChangeForm()

    return render(request, 'organization/force_password_change.html', {'form': form})

# ---------------------------------------------------
# 7. INBOX VIEW
# ---------------------------------------------------
@login_required
def org_inbox(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')

    messages_list = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver').order_by('-timestamp')

    conversations = {}
    for msg in messages_list:
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        if other_user not in conversations:
            conversations[other_user] = msg

    return render(request, 'organization/inbox.html', {'org': org, 'conversations': conversations})

# ---------------------------------------------------
# 8. CHAT DETAIL VIEW
# ---------------------------------------------------
@login_required
def org_chat(request, applicant_id):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')
    
    applicant_user = get_object_or_404(User, id=applicant_id)

    # Find active application
    active_application = JobApplication.objects.filter(
        user=applicant_user,
        job__organization=org
    ).order_by('-created_at').first()

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = applicant_user
            msg.save()
            return redirect('org_chat', applicant_id=applicant_id)
    else:
        form = MessageForm()

    chat_history = Message.objects.filter(
        Q(sender=request.user, receiver=applicant_user) | 
        Q(sender=applicant_user, receiver=request.user)
    ).order_by('timestamp')

    Message.objects.filter(sender=applicant_user, receiver=request.user, is_read=False).update(is_read=True)

    return render(request, 'organization/chat.html', {
        'org': org, 
        'applicant': applicant_user, 
        'chat_history': chat_history, 
        'form': form,
        'application_id': active_application.id if active_application else None,
        'application_status': active_application.status if active_application else None
    })

# ---------------------------------------------------
# 9. POST A JOB VIEW
# ---------------------------------------------------
@login_required
def org_post_job(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('org_register')
    
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.organization = org 
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect('org_dashboard')
    else:
        form = JobPostForm()

    return render(request, 'organization/post_job.html', {'form': form, 'org': org})

# ---------------------------------------------------
# 10. MY JOBS VIEW
# ---------------------------------------------------
@login_required
def org_my_jobs(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')

    all_jobs = Job.objects.filter(organization=org).annotate(
        applicant_count=Count('applications')
    ).order_by('-posted_at')

    active_jobs_count = all_jobs.filter(is_active=True).count()
    total_applicants = JobApplication.objects.filter(job__organization=org).count()
    
    paginator = Paginator(all_jobs, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'org': org,
        'jobs': page_obj, 
        'active_jobs_count': active_jobs_count,
        'total_applicants': total_applicants,
        'total_views': 0 
    }
    return render(request, 'organization/my_jobs.html', context)

# ---------------------------------------------------
# 11. EDIT JOB VIEW
# ---------------------------------------------------
@login_required
def org_edit_job(request, job_id):
    try:
        org = Organization.objects.get(admin_user=request.user)
        job = get_object_or_404(Job, id=job_id, organization=org)
    except Organization.DoesNotExist:
        return redirect('home')

    if request.method == 'POST':
        form = JobPostForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully!")
            return redirect('org_my_jobs')
    else:
        form = JobPostForm(instance=job)
    
    return render(request, 'organization/post_job.html', {
        'form': form, 
        'org': org,
        'is_edit': True 
    })

# ---------------------------------------------------
# 12. DELETE JOB VIEW
# ---------------------------------------------------
@login_required
def org_delete_job(request, job_id):
    try:
        org = Organization.objects.get(admin_user=request.user)
        job = get_object_or_404(Job, id=job_id, organization=org)
        job.delete()
        messages.success(request, "Job deleted successfully!")
    except (Organization.DoesNotExist, Job.DoesNotExist):
        messages.error(request, "Permission denied or job not found.")
        
    return redirect('org_my_jobs')

# ---------------------------------------------------
# 13. CANDIDATES VIEW
# ---------------------------------------------------
@login_required
def org_candidates(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')

    candidates = JobApplication.objects.filter(
        job__organization=org
    ).select_related('job').order_by('-created_at')

    jobs = Job.objects.filter(organization=org).order_by('-posted_at')

    job_id = request.GET.get('job_id')
    status = request.GET.get('status')
    search_query = request.GET.get('q')

    if job_id: candidates = candidates.filter(job_id=job_id)
    if status: candidates = candidates.filter(status=status)
    if search_query:
        candidates = candidates.filter(
            Q(name__icontains=search_query) | 
            Q(email__icontains=search_query)
        )

    context = {
        'org': org,
        'candidates': candidates,
        'jobs': jobs,
        'current_job': int(job_id) if job_id else None,
        'current_status': status,
        'search_query': search_query
    }
    return render(request, 'organization/candidates.html', context)

# ---------------------------------------------------
# 14. EXPORT CANDIDATES
# ---------------------------------------------------
@login_required
def org_export_candidates(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')

    candidates = JobApplication.objects.filter(job__organization=org).select_related('job')

    job_id = request.GET.get('job_id')
    status = request.GET.get('status')
    search_query = request.GET.get('q')

    if job_id: candidates = candidates.filter(job_id=job_id)
    if status: candidates = candidates.filter(status=status)
    if search_query:
        candidates = candidates.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="candidates_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Candidate Name', 'Email', 'Job Applied For', 'Applied Date', 'Status'])

    for app in candidates:
        job_title = app.job.title if app.job else "Unknown"
        writer.writerow([app.name, app.email, job_title, app.created_at.strftime('%Y-%m-%d'), app.status])

    return response

# ---------------------------------------------------
# 15. MANUALLY ADD CANDIDATE
# ---------------------------------------------------
@login_required
def org_add_candidate(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')

    if request.method == 'POST':
        form = ManualCandidateForm(request.POST, request.FILES, org=org)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['full_name']
            
            candidate_user, created = User.objects.get_or_create(
                email=email, defaults={'username': email, 'first_name': name}
            )
            if created:
                candidate_user.set_unusable_password()
                candidate_user.save()

            application = form.save(commit=False)
            application.user = candidate_user 
            if hasattr(application, 'name'): application.name = name
            if hasattr(application, 'email'): application.email = email
            
            application.save()
            messages.success(request, f"Candidate {name} added successfully!")
            return redirect('org_candidates')
    else:
        form = ManualCandidateForm(org=org)

    return render(request, 'organization/add_candidate.html', {'form': form, 'org': org})

# ---------------------------------------------------
# 16. INTERVIEWS DASHBOARD
# ---------------------------------------------------
@login_required
def org_interviews(request):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')

    applicants = JobApplication.objects.filter(
        job__organization=org
    ).exclude(status='REJECTED').order_by('-created_at')

    return render(request, 'organization/interviews.html', {'org': org, 'applicants': applicants})

# ---------------------------------------------------
# 17. TRIGGER INTERVIEW (MANUAL MODE)
# ---------------------------------------------------
@login_required
def org_trigger_interview(request, application_id, round_name):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')

    application = get_object_or_404(JobApplication, id=application_id)
    
    if round_name == 'HR': application.interview_stage = 'HR_ROUND'
    elif round_name == 'TECH': application.interview_stage = 'TECH_ROUND'
    elif round_name == 'FINAL': application.interview_stage = 'FINAL_ROUND'
    
    application.status = 'INTERVIEWING'
    application.save()

    candidate_user = application.get_user_account()
    
    if candidate_user:
        job_title = "the position"
        if application.job:
            job_title = application.job.title
        elif application.job_advert:
            job_title = application.job_advert.title

        formatted_message = (
            f"**[INTERVIEW UPDATE - {round_name} ROUND]**\n\n"
            f"Hello {application.name}, congratulations! You have been moved to the {round_name} Interview Round for {job_title}.\n\n"
            f"The hiring manager will be sending you the interview questions or tasks shortly via this chat.\n"
            f"Please stay online."
        )

        Message.objects.create(
            sender=request.user, 
            receiver=candidate_user, 
            content=formatted_message, 
            is_read=False
        )

        Notification.objects.create(
            user=candidate_user,
            title=f"Interview Update: {round_name}",
            message=f"You have moved to the {round_name} round. Check your messages.",
            link=reverse('user_interview_room', kwargs={'application_id': application.id})
        )

        messages.success(request, f"{round_name} Round started! Redirecting to chat...")
        return redirect('org_chat', applicant_id=candidate_user.id)

    else:
        messages.warning(request, "Stage updated, but candidate has no User account linked.")

    return redirect('org_interviews')

# ---------------------------------------------------
# 18. ✅ NEW: MAKE HIRING DECISION (HIRE / REJECT)
# ---------------------------------------------------
@login_required
def org_make_decision(request, application_id, decision):
    try:
        org = Organization.objects.get(admin_user=request.user)
    except Organization.DoesNotExist:
        return redirect('home')

    # Get the application and verify it belongs to this org
    application = get_object_or_404(JobApplication, id=application_id)
    
    if application.job.organization != org:
        messages.error(request, "Permission denied.")
        return redirect('org_dashboard')

    candidate_user = application.get_user_account()

    if decision == 'hire':
        application.status = 'ACCEPTED' 
        message_content = f"🎉 **CONGRATULATIONS!**\n\nWe are pleased to inform you that you have been selected for the **{application.job.title}** position.\n\nHR will contact you shortly with the offer letter details."
        notif_title = "You're Hired! 🎉"
        messages.success(request, f"Candidate {application.name} has been Hired!")
        
    elif decision == 'reject':
        application.status = 'REJECTED'
        message_content = f"Thank you for your time and interest in the **{application.job.title}** position.\n\nAfter careful consideration, we have decided to move forward with other candidates at this time. We wish you the best in your future endeavors."
        notif_title = "Application Update"
        messages.info(request, f"Candidate {application.name} has been rejected.")
        
    else:
        return redirect('org_chat', applicant_id=candidate_user.id)

    application.save()

    # 1. Send System Message in Chat
    if candidate_user:
        Message.objects.create(
            sender=request.user,
            receiver=candidate_user,
            content=message_content,
            is_read=False
        )

        # 2. Send Notification
        Notification.objects.create(
            user=candidate_user,
            title=notif_title,
            message=f"Status update for {application.job.title}: {application.status}",
            link=reverse('user_interview_room', kwargs={'application_id': application.id})
        )

    return redirect('org_chat', applicant_id=candidate_user.id)