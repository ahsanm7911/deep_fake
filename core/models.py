from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name 
    
class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    image_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='history/', blank=True, null=True)
    result = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.username} - {self.image_name} - {self.result}"
    
