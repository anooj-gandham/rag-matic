from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from celery.result import AsyncResult


from app.models.files import File
from app.serializers.files import FileSerializer
from app.tasks.generate_embeddings import process_file_for_embeddings
from django.http import JsonResponse

class FileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling file uploads and metadata management.
    On create and update, triggers a Celery task to process file embeddings.
    """
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def create(self, request, *args, **kwargs):
        # Validate and save the new file instance
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_instance = serializer.save()
        
        # Trigger the Celery task to generate embeddings
        result = process_file_for_embeddings.apply_async(
            args=[file_instance.id],
            queue="embeddings",
            )
        
        return JsonResponse({"task_id": result.id}, status=202)

    def update(self, request, *args, **kwargs):
        # Get the existing file instance
        file_instance = get_object_or_404(File, pk=kwargs.get("pk"))
        
        # Store the old URL for comparison
        old_url = file_instance.url
        
        # Validate and update the file instance
        serializer = self.get_serializer(file_instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        # Check if the URL has changed
        if old_url != updated_instance.url:
            # Set processed = False before triggering the embedding process
            updated_instance.processed = False
            updated_instance.save(update_fields=["processed"])
            
            # Re-trigger the Celery task to process embeddings
            result = process_file_for_embeddings.apply_async(
                args=[updated_instance.id],
                queue="embeddings",
            )
            return JsonResponse({
                "task_id": result.id,
                "message": "Embeddings reprocessing triggered. Processed flag set to False."
            }, status=202)
        
        # Return a successful response if no reprocessing is required
        return Response(serializer.data, status=status.HTTP_200_OK)


    def destroy(self, request, *args, **kwargs):
        # Perform any custom cleanup if needed.
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="task-status/(?P<task_id>[^/.]+)")
    def task_status(self, request, task_id=None):
        """
        Retrieve the status of a Celery task.
        """
        result = AsyncResult(task_id)
        response = {
            "status": result.status,
            "result": result.result if result.ready() and result.status == "SUCCESS" else None,
        }
        return JsonResponse(response)
