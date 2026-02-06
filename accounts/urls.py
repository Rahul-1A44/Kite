from django.urls import path
from . import views

urlpatterns = [
    # ✅ ADD THIS LINE (This is where regular users go)
    path('', views.home, name='home'), 

    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name="register"),
    path('verify-account/', views.verify_account, name="verify_account"),
    path('forgot-password/', views.send_password_reset_link, name="reset_password_via_email"),
    path('verify-password-reset-link/', views.verify_password_reset_link, name="verify_password_reset_link"),
    path('set-new-password/', views.set_new_password_using_reset_link, name="set_new_password"),
    
    # Traffic Cop
    path('login-success/', views.login_success, name='login_success'),
]