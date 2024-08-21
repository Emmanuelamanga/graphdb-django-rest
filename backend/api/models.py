from django.db import models

# Blazegraph connection strings 
class BlazegraphConnection(models.Model):
    name = models.CharField(max_length=100)
    endpoint_url = models.URLField(max_length=200)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UploadedFile(models.Model):
    name = models.CharField(max_length=255)
    size = models.IntegerField()
    file_path = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Repository(models.Model):
    name = models.CharField(max_length=100)
    endpoint_url = models.URLField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    