from datetime import datetime, timezone

from django.contrib import auth, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string

# Ensure this task exists in common/tasks.py
from common.tasks import send_email

# NOTE: Make sure the decorator name matches your file
from .decorators import redirect_autheticated_user
from .models import PendingUser, Token, TokenType, User


def home(request: HttpRequest):
    # This renders the Candidate Homepage
    return render(request, "home.html")


@redirect_autheticated_user
def login(request: HttpRequest):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = auth.authenticate(request, email=email, password=password)

        if user is not None:
            auth.login(request, user)
            # ✅ CORRECT: Redirect to the Traffic Cop view
            return redirect("login_success")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    else:
        return render(request, "login.html")


def logout(request: HttpRequest):
    auth.logout(request)
    messages.success(request, "You are now logged out.")
    return redirect("login")


@redirect_autheticated_user
def register(request: HttpRequest):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Email and password are required")
            return redirect("register")

        cleaned_email = email.lower()

        if User.objects.filter(email=cleaned_email).exists():
            messages.error(request, "Email exists on the platform")
            return redirect("register")

        else:
            verification_code = get_random_string(10)
            
            PendingUser.objects.update_or_create(
                email=cleaned_email,
                defaults={
                    "password": make_password(password),
                    "verification_code": verification_code,
                    "created_at": datetime.now(timezone.utc),
                },
            )
            
            # Send Email
            send_email.delay(
                "Verify Your Account",
                [cleaned_email],
                "emails/email_verification_template.html",
                context={"code": verification_code},
            )
            
            messages.success(request, f"Verification code sent to {cleaned_email}")
            return render(
                request, "verify_account.html", context={"email": cleaned_email}
            )

    else:
        return render(request, "register.html")


def verify_account(request: HttpRequest):
    if request.method == "POST":
        code = request.POST.get("code")
        email = request.POST.get("email")
        
        pending_user = PendingUser.objects.filter(
            verification_code=code, email=email
        ).first()
        
        if pending_user and pending_user.is_valid():
            # Create the actual user
            User.objects.create(
                email=pending_user.email, 
                password=pending_user.password
            )
            
            # Clean up
            pending_user.delete()
            
            # Note: We do NOT log them in automatically.
            messages.success(request, "Account verified! Please login with your credentials.")
            return redirect("login")

        else:
            messages.error(request, "Invalid or expired verification code")
            return render(request, "verify_account.html", {"email": email}, status=400)


def send_password_reset_link(request: HttpRequest):
    if request.method == "POST":
        email = request.POST.get("email", "")
        user = get_user_model().objects.filter(email=email.lower()).first()

        if user:
            token, _ = Token.objects.update_or_create(
                user=user,
                token_type=TokenType.PASSWORD_RESET,
                defaults={
                    "token": get_random_string(20),
                    "created_at": datetime.now(timezone.utc),
                },
            )

            email_data = {"email": email.lower(), "token": token.token}
            send_email.delay(
                "Your Password Reset Link",
                [email],
                "emails/password_reset_template.html",
                email_data,
            )
            messages.success(request, "Reset link sent to your email")
            return redirect("reset_password_via_email")

        else:
            messages.error(request, "Email not found")
            return redirect("reset_password_via_email")

    else:
        return render(request, "forgot_password.html")


def verify_password_reset_link(request: HttpRequest):
    email = request.GET.get("email")
    reset_token = request.GET.get("token")

    token = Token.objects.filter(
        user__email=email, token=reset_token, token_type=TokenType.PASSWORD_RESET
    ).first()

    if not token or not token.is_valid():
        messages.error(request, "Invalid or expired reset link.")
        return redirect("reset_password_via_email")

    return render(
        request,
        "set_new_password_using_reset_token.html",
        context={"email": email, "token": reset_token},
    )


def set_new_password_using_reset_link(request: HttpRequest):
    if request.method == "POST":
        password1_input = request.POST.get("password1")
        password2_input = request.POST.get("password2")
        email = request.POST.get("email")
        reset_token = request.POST.get("token")

        if password1_input != password2_input:
            messages.error(request, "Passwords do not match")
            return render(
                request,
                "set_new_password_using_reset_token.html",
                {"email": email, "token": reset_token},
            )

        token = Token.objects.filter(
            token=reset_token, token_type=TokenType.PASSWORD_RESET, user__email=email
        ).first()

        if not token or not token.is_valid():
            messages.error(request, "Expired or Invalid reset link")
            return redirect("reset_password_via_email")

        token.reset_user_password(password1_input)
        token.delete()
        messages.success(request, "Password changed. Please login.")
        return redirect("login")


# ✅ NEW VIEW: The "Traffic Cop"
@login_required
def login_success(request):
    """
    Redirects users based on their role:
    - Organization Admins -> Organization Dashboard
    - Regular Users -> Candidate Home
    """
    # Lazy import to avoid circular dependency issues
    from organization.models import Organization
    
    # Check if this user manages any organization
    if Organization.objects.filter(admin_user=request.user).exists():
        return redirect('org_dashboard')
        
    # Otherwise, they are a regular candidate -> Go to HOME
    return redirect('home')  # ✅ FIXED: Points to 'home' instead of 'user_profile'