from django.urls import path
from . import views

urlpatterns = [
    # --- Registration Flow ---
    path('register/', views.org_register, name='org_register'),
    path('status/<uuid:org_id>/', views.org_status, name='org_status'), 
    
    # --- Dashboard & Security ---
    path('dashboard/', views.org_dashboard, name='org_dashboard'),
    path('setup/password/', views.org_change_password, name='org_change_password'),

    # --- Messaging System ---
    path('inbox/', views.org_inbox, name='org_inbox'),
    # ✅ FIX: Supports User UUIDs
    path('chat/<uuid:applicant_id>/', views.org_chat, name='org_chat'),

    # --- Job Management ---
    path('job/create/', views.org_post_job, name='org_post_job'),
    path('my-jobs/', views.org_my_jobs, name='org_my_jobs'),
    path('job/edit/<int:job_id>/', views.org_edit_job, name='org_edit_job'),
    path('job/delete/<int:job_id>/', views.org_delete_job, name='org_delete_job'),
    
    # --- Candidates Management ---
    path('candidates/', views.org_candidates, name='org_candidates'),
    path('candidates/export/', views.org_export_candidates, name='org_export_candidates'),
    path('candidates/add/', views.org_add_candidate, name='org_add_candidate'),
    
    # --- Interview & Decision Management ---
    path('interviews/', views.org_interviews, name='org_interviews'),
    path('interviews/trigger/<uuid:application_id>/<str:round_name>/', views.org_trigger_interview, name='org_trigger_interview'),
    
    # ✅ NEW: Hire/Reject Decision URL
    path('decision/<uuid:application_id>/<str:decision>/', views.org_make_decision, name='org_make_decision'),

    # --- Payment Flow ---
    path('payment/initiate/<uuid:org_id>/', views.init_payment, name='init_khalti'),
    path('payment/verify/', views.verify_payment, name='verify_khalti'),
]