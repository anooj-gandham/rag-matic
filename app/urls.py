# app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from app.views.query import generate_response_view, poll_query_status_view
from app.views.files import FileViewSet
from app.views.upload import upload_file_view  

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'files', FileViewSet, basename='file')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path("query-generate/", generate_response_view, name="query"),
    path("query-status/", poll_query_status_view, name="query"),
    path("upload-file/", upload_file_view, name="upload-file"),


]
