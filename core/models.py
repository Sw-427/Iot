

from email.policy import default
from django.db import models
from datetime import datetime
from django.db.models.functions import Now
  
# Create your models here.
  
  
class React(models.Model):
    name = models.CharField(max_length=30)
    detail = models.CharField(max_length=500)

class iot(models.Model):
    uid = models.CharField(max_length=30)
    indate = models.DateTimeField(default=Now(), blank=True)
    outdate = models.DateTimeField(default=Now(), blank=True)      
    
