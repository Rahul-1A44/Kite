from django.urls import path
from . import views, ai_views

urlpatterns = [
    # ====================================================
    # 0. AI INTERVIEW SYSTEM
    # ====================================================
    path('interview-ai/start/<uuid:application_id>/', ai_views.start_ai_interview, name='start_ai_interview'),
    path('api/interview-ai/<uuid:application_id>/chat/', ai_views.ai_chat_api, name='ai_chat_api'),
    path('interview-ai/end/<uuid:application_id>/', ai_views.end_ai_interview, name='end_ai_interview'),
    path('interview/task/<uuid:application_id>/', ai_views.user_task_view, name='user_task_view'),

    # ====================================================
    # 1. SPECIFIC STATIC PAGES (MUST BE AT THE TOP)
    # ====================================================
    # If these are below <str:advert_id>, Django will think "sources" is an ID and crash.
    
    # Sources & Learning
    path('sources/', views.sources_page, name='sources_page'),
    path('api/get-sources/', views.get_sources_api, name='get_sources_api'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),

    # Dashboard & Profile
    path("dashboard/", views.dashboard, name="dashboard"),
    
    # ✅ NEW PATH: The "No Organization" Landing Page
    path('organization/setup/', views.org_setup_prompt, name='org_setup_prompt'),

    path("dashboard/profile/", views.profile_view, name="user_profile"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path("my-jobs/", views.my_jobs, name="my_jobs"),
    path('my-interviews/', views.user_interviews, name='user_interviews'),

    # Job Creation & Search
    path("create/", views.create_advert, name="create_advert"),
    path("search/", views.search, name="search"),
    path('apply/', views.jobs_apply, name='jobs_apply'),

    # ====================================================
    # 2. INTEGER ID PATHS (New System)
    # ====================================================
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'), 

    # ====================================================
    # 3. UUID SPECIFIC PATHS
    # ====================================================
    path('interview-room/<uuid:application_id>/', views.user_interview_room, name='user_interview_room'),
    path("<uuid:job_application_id>/decide/", views.decide, name="decide"),
   
    path("<str:advert_id>/", views.get_advert, name="job_advert"),
    path("<str:advert_id>/apply/", views.apply, name="apply_for_job"),
    path("<str:advert_id>/analyze/", views.analyze_resume, name="analyze_resume"),
    
    path("<str:advert_id>/applications/", views.advert_applications, name="advert_applications"),
    path("<str:advert_id>/update/", views.update_advert, name="update_advert"),
    path("<str:advert_id>/delete/", views.delete_advert, name="delete_advert"),
]