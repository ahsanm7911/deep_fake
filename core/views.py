from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from .models import History, Profile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        return redirect("dashboard")
    return JsonResponse({"status" : "OK", "message": "Welcome home."})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password")
    return render(request, 'core/login.html')

def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        msg = None
        if not name or not email or not password:
            msg = "Error: All fields are required."
            print(msg)
            messages.error(request, msg)
        elif password != confirm_password:
            msg = "Error: Passwords donot match."
            print(msg)
            messages.error(request, msg)
        elif User.objects.filter(username=email).exists():
            msg = "Error: Another user with this email is already registered."
            print(msg)
            messages.error(request, msg)
        else:
            try:
                user = User.objects.create_user(username=email, email=email, password=password)
                Profile.objects.create(user=user, name=name)
                msg = "Success: Account created successfully. Please log in."
                print(msg)
                messages.success(request, msg)
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
    return render(request, 'core/signup.html')

def dashboard_view(request):
    return render(request, 'core/dashboard.html')

def history_view(request):
    history = History.objects.filter(user=request.user)
    return render(request, 'core/history.html', {'history': history})

def settings_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = request.user
        profile = user.profile 
        if name: 
            profile.name = name 
            profile.save()
        if email and email != user.email:
            if not User.objects.filter(username=email).exists():
                user.username = email 
                user.email = email 
                user.save()
            else:
                messages.error(request, "Please choose another email because this one is registered by another user.")
                return render(request, "core/user_settings.html", {'user': user})
        if password:
            user.set_password(password)
            user.save()
            login(request, user) 
        messages.success(request, "Profile updated successfully.")
    return render(request, 'core/user_settings.html', {'user': request.user})

def logout_view(request):
    logout(request)
    return redirect('login')

def detect_api(request):
    if request.method == 'POST':
        image = request.FILES['image']
        # Process image with model (placeholder)
        result = {"result": "Real", "confidence": 0.95}
        # Save to History
        history_record = History.objects.create(
            user=request.user,
            image_name=image.name,
            image=image,
            result=f"{result['result']} (Confidence: {(result['confidence'] * 100):.2f}%)"
        )
        return JsonResponse(result)
    return JsonResponse({"error": "Invalid request"}, status=400)

def generate_pdf_api(request):
    if request.method == 'POST':
        pdf_buffer = None
        # Generate PDF with ReportLab
        return FileResponse(pdf_buffer, as_attachment=True, filename='deepfake_report.pdf')
    return JsonResponse({"error": "Invalid request"}, status=400)