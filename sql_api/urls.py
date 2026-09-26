from django.urls import path
from .views import query_api,home

urlpatterns = [
    path('',home,name='home'),
    path('query/',query_api,name='query'),
]
