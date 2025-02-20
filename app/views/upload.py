# app/views/s3_upload.py

import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import HttpRequest

from app.utils.s3 import upload_file_to_s3

@swagger_auto_schema(
    method="post",
    tags=["upload"],
    operation_description="Upload a file to S3 and return its public URL",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["file"],
        properties={
            "file": openapi.Schema(
                type=openapi.TYPE_FILE, 
                description="The file to upload"
            ),
        },
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "url": openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="The S3 URL of the uploaded file"
                ),
            },
        ),
        400: "No file was provided or invalid request."
    },
)
@api_view(["POST"])
def upload_file_view(request: HttpRequest):
    """
    Upload a file to S3 using the provided 'file' form field.
    Returns the S3 URL if successful.
    """
    # Check if file is provided
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file was provided."}, status=400)

    # Generate a unique file name (e.g., <UUID>-<original_name>)
    unique_name = f"{uuid.uuid4()}-{file_obj.name}"

    # Use your S3 utility function
    s3_url = upload_file_to_s3(file_obj, unique_name)

    if s3_url is None:
        return Response({"error": "Failed to upload file to S3."}, status=500)

    return Response({"url": s3_url}, status=200)
