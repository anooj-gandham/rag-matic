from rest_framework import serializers
from app.models.files import File

class FileSerializer(serializers.ModelSerializer):
    # Mark weaviate_ids as read_only so it's excluded from input data.
    weaviate_ids = serializers.JSONField(read_only=True)
    
    class Meta:
        model = File
        fields = "__all__"
        read_only_fields = ("weaviate_ids", "uploaded_at")