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
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from rest_framework.response import Response
from django.conf import settings
from datetime import timedelta
import re
import tensorflow as tf 
import numpy as np 
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
import io 
import os 
from django.core.files import File

physical_devices = tf.config.list_physical_devices('GPU')
if physical_devices:
    try:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
    except:
        print("Failed to set memory growth.")

MODEL_PATH = os.path.join('model', 'deepfake_model_final.h5')
if not os.path.exists(MODEL_PATH):
    print("Model path doesnot exists.")

try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print(f"Model: {model}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

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

@login_required
def analytics_page(request):
    user = request.user
    detections = History.objects.filter(user=user)
    
    # Real/Fake distribution
    result_counts = detections.values('result').annotate(count=Count('id'))
    real_count = next((item['count'] for item in result_counts if item['result'] == 'Real'), 0)
    fake_count = next((item['count'] for item in result_counts if item['result'] == 'Fake'), 0)
    
    # Average confidence
    avg_confidence = detections.aggregate(Avg('confidence'))['confidence__avg'] or 0
    
    # Image size stats
    avg_image_width = detections.aggregate(Avg('image_width'))['image_width__avg'] or 0
    avg_image_height = detections.aggregate(Avg('image_height'))['image_height__avg'] or 0
    
    # Time-series data (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_detections = detections.filter(timestamp__gte=thirty_days_ago).order_by('timestamp')
    
    # Confidence trends
    confidence_data = [
        {'timestamp': d.timestamp.strftime('%Y-%m-%d'), 'confidence': d.confidence}
        for d in recent_detections
    ]
    
    # Detections per day
    detections_by_day = (
        detections.filter(timestamp__gte=thirty_days_ago)
        .extra({'day': "date(timestamp)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    detections_per_day = [
        {'date': item['day'], 'count': item['count']}
        for item in detections_by_day
    ]
    
    # Recent detections for table
    recent_detections_table = detections[:5]
    
    context = {
        'real_count': real_count,
        'fake_count': fake_count,
        'total_detections': real_count + fake_count,
        'avg_confidence': round(avg_confidence * 100, 2),
        'avg_image_width': round(avg_image_width, 0),
        'avg_image_height': round(avg_image_height, 0),
        'confidence_data': confidence_data,
        'detections_per_day': detections_per_day,
        'recent_detections': recent_detections_table,
    }
    return render(request, 'core/analytics.html', context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_api(request):
    user = request.user
    detections = History.objects.filter(user=user)
    
    result_counts = detections.values('result').annotate(count=Count('id'))
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_detections = detections.filter(timestamp__gte=thirty_days_ago).order_by('timestamp')
    
    detections_by_day = (
        detections.filter(timestamp__gte=thirty_days_ago)
        .extra({'day': "date(timestamp)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    
    return Response({
        'result_counts': list(result_counts),
        'confidence_data': [
            {'timestamp': d.timestamp.strftime('%Y-%m-%d'), 'confidence': d.confidence}
            for d in recent_detections
        ],
        'detections_per_day': [
            {'date': item['day'], 'count': item['count']}
            for item in detections_by_day
        ],
        'avg_confidence': detections.aggregate(Avg('confidence'))['confidence__avg'] or 0,
        'avg_image_width': detections.aggregate(Avg('image_width'))['image_width__avg'] or 0,
        'avg_image_height': detections.aggregate(Avg('image_height'))['image_height__avg'] or 0,
    })

def dashboard_view(request):
    return render(request, 'core/dashboard.html')


# @api_view(['GET'])
# # @permission_classes([IsAuthenticated])
def history_view(request):
    
    history_records = History.objects.filter(user=request.user).order_by('-timestamp')
    history_data = [{
        'id': record.id,
        'image_url': record.image.url if record.image else None,
        'result': record.result,
        'confidence': float(record.confidence),
        'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'image_name': record.image_name,
        'image_width': record.image_width,
        'image_height': record.image_height,
        'pdf_report_url': record.pdf_report.url if record.pdf_report else None
    } for record in history_records]
    context = {
        'history': history_data
    }
    return render(request, 'core/history.html', context)
    
    
    

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
    print("Detect_api called.")
    if request.method == 'POST':
        try:
            model = tf.keras.models.load_model(MODEL_PATH)
        except Exception as e:
            print(f"Model loading failed: {e}")
            return JsonResponse({'error': f'Model loading failed: {str(e)}'}, status=500)

        try:
            print("Inside detect_api try block.")
            image = request.FILES['image']
            print(f"Image: {image}")
            img = Image.open(image).resize((128, 128)).convert('RGB')
            img_array = np.array(img) / 127.5 - 1.0
            img_array = np.expand_dims(img_array, axis=0)
            prediction = model.predict(img_array)[0][0]
            result = 'Real' if prediction < 0.5 else 'Fake'
            confidence = 1 - prediction if prediction < 0.5 else prediction

            # Save image to media/images/
            image_name = image.name
            image_path = f'images/{datetime.now().strftime("%Y%m%d_%H%M%S")}_{image_name}'
            image_full_path = os.path.join(settings.MEDIA_ROOT, image_path)
            os.makedirs(os.path.dirname(image_full_path), exist_ok=True)
            with open(image_full_path, 'wb') as f:
                for chunk in image.chunks():
                    f.write(chunk)

            # Create History record
            history = History.objects.create(
                user=request.user,
                image=image_path,
                result=result,
                confidence=confidence,
                image_name=image_name,
                image_width=img.width,
                image_height=img.height
            )

            # Generate PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Heading
            c.setFont("Helvetica-Bold", 20)
            c.drawString(1 * inch, height - 1 * inch, "DeepFake Detection Report")

            # User Information
            c.setFont("Helvetica", 12)
            c.drawString(1 * inch, height - 1.5 * inch, f"User: {request.user.profile.name}")
            c.drawString(1 * inch, height - 1.75 * inch, f"Email: {request.user.email}")
            c.drawString(1 * inch, height - 2 * inch, f"Date: {history.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            

            # Image
            if os.path.exists(image_full_path):
                img_reader = ImageReader(image_full_path)
                img_width, img_height = 200, 200
                c.drawImage(img_reader, 1 * inch, height - 5.5 * inch, width=img_width, height=img_height)
            else:
                c.drawString(1 * inch, height - 4.5 * inch, "Image not found")

            # Image Information
            c.drawString(1 * inch, height - 6.5 * inch, f"Image Name: {image_name}")
            c.drawString(1 * inch, height - 6.75 * inch, f"Dimensions: {img.width} x {img.height} pixels")

            # Detection Results
            c.drawString(1 * inch, height - 7 * inch, f"Result: {result}")
            c.drawString(1 * inch, height - 7.25 * inch, f"Confidence: {float(confidence):.2%}")

            # Finalize PDF
            c.showPage()
            c.save()
            buffer.seek(0)

            # Save PDF to History
            pdf_filename = f'pdfs/report_{history.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            history.pdf_report.save(pdf_filename, File(buffer))
            history.save()

            print(f"History record created: ID {history.id}, PDF saved: {pdf_filename}")
            return JsonResponse({
                'result': result,
                'confidence': float(confidence),
                'history_id': history.id,
                'image_name': image_name,
                'image_width': img.width,
                'image_height': img.height,
                'pdf_report_url': f"{settings.MEDIA_URL}{pdf_filename}"
            })
        except Exception as e:
            print(f"Detection failed: {e}")
            return JsonResponse({'error': f'Detection failed: {str(e)}'}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_pdf(request):
    try:
        # Extract data from request
        history_id = request.data.get('history_id')
        result = request.data.get('result')
        confidence = request.data.get('confidence')
        image_name = request.data.get('image_name')
        image_width = request.data.get('image_width')
        image_height = request.data.get('image_height')

        if not all([history_id, result, confidence, image_name, image_width, image_height]):
            return JsonResponse({'error': 'Missing required data'}, status=400)

        # Get History record
        try:
            history = History.objects.get(id=history_id, user=request.user)
        except History.DoesNotExist:
            return JsonResponse({'error': 'History record not found'}, status=404)

        # Create PDF in memory
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Heading
        c.setFont("Helvetica-Bold", 20)
        c.drawString(1 * inch, height - 1 * inch, "DeepFake Detection Report")

        # User Information
        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, height - 1.5 * inch, f"User: {request.user.username}")
        c.drawString(1 * inch, height - 1.75 * inch, f"Email: {request.user.email}<br/>")
        c.drawString(1 * inch, height - 4 * inch, f"Date: {history.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br/><br/>")

        # Image
        image_path = os.path.join(settings.MEDIA_ROOT, history.image.name)
        if os.path.exists(image_path):
            img = ImageReader(image_path)
            img_width, img_height = 200, 200
            c.drawImage(img, 1 * inch, height - 4.5 * inch, width=img_width, height=img_height)
        else:
            c.drawString(1 * inch, height - 4.5 * inch, "Image not found")

        # Image Information
        c.drawString(1 * inch, height - 5 * inch, f"Image Name: {image_name}")
        c.drawString(1 * inch, height - 5.25 * inch, f"Dimensions: {image_width} x {image_height} pixels")

        # Detection Results
        c.drawString(1 * inch, height - 5.75 * inch, f"Result: {result}")
        c.drawString(1 * inch, height - 6 * inch, f"Confidence: {float(confidence):.2%}")

        # Finalize PDF
        c.showPage()
        c.save()
        buffer.seek(0)

        # Save PDF to History
        pdf_filename = f'pdfs/report_{history_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        history.pdf_report.save(pdf_filename, File(buffer))
        history.save()

        # Return PDF as downloadable file
        buffer.seek(0)
        response = FileResponse(buffer, as_attachment=True, filename=f"deepfake_report_{history_id}.pdf")
        return response
    except Exception as e:
        print(f"PDF generation error: {e}")
        return JsonResponse({'error': str(e)}, status=500)