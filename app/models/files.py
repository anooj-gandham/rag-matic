import uuid

from django.db import models


class File(models.Model):
    """
    Model to store uploaded documents and their metadata.
    """

    FILE_FORMATS = [
        ("pdf", "PDF"),
        ("docx", "DOCX"),
        ("json", "JSON"),
        ("txt", "TXT"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    url = models.CharField(blank=False, max_length=500)
    file_type = models.CharField(max_length=10, choices=FILE_FORMATS)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)  # Flag to track processing status
    weaviate_ids = models.JSONField(default=dict)  # Store Weaviate IDs for the file
    sample_questions = models.JSONField(default=list, blank=True, null=True) # Store sample questions to be displayed in UI

    def __str__(self):
        return self.name
