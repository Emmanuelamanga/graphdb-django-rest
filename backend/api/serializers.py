from rest_framework import serializers
from .models import Repository
from .models import UploadedFile
from .models import BlazegraphConnection

# blazegraph serializer 
class BlazegraphConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlazegraphConnection
        fields = '__all__'
        
class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = '__all__'

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = '__all__'
