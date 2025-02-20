from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import JsonResponse
import json
from celery.result import AsyncResult

@swagger_auto_schema(
    method="post",
    tags=["query"],
    operation_id="query_create",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["query", "file_id"],
        properties={
            "query": openapi.Schema(type=openapi.TYPE_STRING, description="The query text"),
            "file_id": openapi.Schema(type=openapi.TYPE_STRING, description="The file UUID as a string"),
        },
    ),
    responses={
        202: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "task_id": openapi.Schema(type=openapi.TYPE_STRING, description="Celery task ID"),
            },
        )
    }
)
@api_view(["POST"])
def generate_response_view(request):
    """
    Endpoint to trigger the generate_response Celery task and return its task ID.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    query = data.get("query")
    file_id = data.get("file_id")
    if not query or not file_id:
        return JsonResponse({"error": "Both 'query' and 'file_id' are required."}, status=400)

    from app.tasks.query import generate_response  # Import here to avoid circular imports.
    task_result = generate_response.apply_async(args=[query, file_id], queue="queries")
    return JsonResponse({"task_id": task_result.id}, status=202)


@swagger_auto_schema(
    method="get",
    tags=["query"],  # <--- Same tag name to group with the other endpoint
    operation_id="query_status",
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_QUERY,  # or IN_PATH if you're passing it in the URL
            description="Celery task ID to poll",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "status": openapi.Schema(type=openapi.TYPE_STRING, description="Task status"),
                "result": openapi.Schema(type=openapi.TYPE_STRING, description="Task result (if available)")
            }
        )
    }
)
@api_view(["GET"])
def poll_query_status_view(request):
    """
    Poll the status of the generate_response Celery task using the task_id.
    """
    task_id = request.GET.get("task_id")  # or from the URL path if desired
    if not task_id:
        return JsonResponse({"error": "'task_id' is required as a query parameter."}, status=400)
    
    result = AsyncResult(task_id)
    if not result.ready():
        return JsonResponse({"status": result.status, "result": None})
    elif result.status == "SUCCESS":
        return JsonResponse({"status": result.status, "result": result.result})
    else:
        return JsonResponse({"status": result.status, "result": None})
