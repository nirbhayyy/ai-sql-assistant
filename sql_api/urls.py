from django.urls import path
from .views import query_api,home,history_query

urlpatterns = [
    path('',home,name='home'),
    path('query/',query_api,name='query'),
    path('history/',history_query)
]
