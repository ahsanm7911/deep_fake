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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history_view(request):
    try:
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
        return JsonResponse({'history': history_data})
    except Exception as e:
        print(f"History view error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

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
                c.drawImage(img_reader, 1 * inch, height - 4.5 * inch, width=img_width, height=img_height)
            else:
                c.drawString(1 * inch, height - 4.5 * inch, "Image not found")

            # Image Information
            c.drawString(1 * inch, height - 5 * inch, f"Image Name: {image_name}")
            c.drawString(1 * inch, height - 5.25 * inch, f"Dimensions: {img.width} x {img.height} pixels")

            # Detection Results
            c.drawString(1 * inch, height - 5.75 * inch, f"Result: {result}")
            c.drawString(1 * inch, height - 6 * inch, f"Confidence: {float(confidence):.2%}")

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
        c.drawString(1 * inch, height - 1.75 * inch, f"Email: {request.user.email}")
        c.drawString(1 * inch, height - 2 * inch, f"Date: {history.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

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