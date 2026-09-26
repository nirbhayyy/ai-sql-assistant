from django.urls import path
from .views import query_api

urlpatterns = [
    path('query/',query_api),
]
