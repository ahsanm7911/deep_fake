from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name 
    


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detection_history')
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    result = models.CharField(max_length=10, choices=[('Real', 'Real'), ('Fake', 'Fake')])
    confidence = models.FloatField(default=0.00)
    timestamp = models.DateTimeField(auto_now_add=True)
    pdf_report = models.FileField(upload_to='pdfs/', null=True, blank=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'History'
        verbose_name_plural = 'Histories'

    def __str__(self):
        return f"{self.user.username} - {self.result} ({self.timestamp})"
