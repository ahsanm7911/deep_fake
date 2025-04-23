from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from .models import History, Profile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
import re

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/index.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            token = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
            print("Token: ", token)
            # Pass token to template for JavaScript to store
            return render(request, 'core/login.html', {
                'token': token,
                'success': True,
            })
        else:
            messages.error(request, 'Invalid email or password.')
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

def analytics_view(request):
    return render(request, 'core/analytics.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_api(request):
    history = History.objects.filter(user=request.user)
    total_scans = history.count()
    
    fake_count = history.filter(result__contains='Fake').count()
    real_count = total_scans - fake_count
    fake_percentage = (fake_count / total_scans * 100) if total_scans > 0 else 0
    real_percentage = (real_count / total_scans * 100) if total_scans > 0 else 0

    # Trend data (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    trend_data = []
    trend_labels = []
    for i in range(30):
        day = start_date + timedelta(days=i)
        count = history.filter(date__date=day.date()).count()
        trend_data.append(count)
        trend_labels.append(day.strftime('%Y-%m-%d'))

    # Confidence score distribution
    confidence_bins = [f"{i}-{i+10}" for i in range(0, 100, 10)]
    real_confidence = [0] * 10
    fake_confidence = [0] * 10
    for record in history:
        match = re.search(r'Confidence: (\d+\.\d{2})', record.result)
        if match:
            confidence = float(match.group(1))
            bin_index = min(int(confidence // 10), 9)
            if 'Real' in record.result:
                real_confidence[bin_index] += 1
            else:
                fake_confidence[bin_index] += 1

    return JsonResponse({
        'total_scans': total_scans,
        'fake_percentage': round(fake_percentage, 2),
        'real_percentage': round(real_percentage, 2),
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'confidence_bins': confidence_bins,
        'real_confidence': real_confidence,
        'fake_confidence': fake_confidence
    })

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_api(request):
    if request.method == 'POST':
        image = request.FILES['image']
        # Process image with model (placeholder)
        result = {"result": "Real", "confidence": 0.95}
        # Save to History
        History.objects.create(
            user=request.user,
            image_name=image.name,
            image=image,
            result=f"{result['result']} (Confidence: {(result['confidence'] * 100):.2f}%)"
        )
        return JsonResponse(result)
    return JsonResponse({"error": "Invalid request"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_pdf_api(request):
    if request.method == 'POST':
        pdf_buffer = None
        # Generate PDF with ReportLab (placeholder)
        return FileResponse(pdf_buffer, as_attachment=True, filename='deepfake_report.pdf')
    return JsonResponse({"error": "Invalid request"}, status=400)