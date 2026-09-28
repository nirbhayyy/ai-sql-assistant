from django.urls import path
from .views import query_api,home,history_query,dashboard_view,dash_board

urlpatterns = [
    path('',home,name='home'),
    path('query/',query_api,name='query'),
    path('history/',history_query),
    path('dash-data/',dashboard_view),
    path('dash/',dash_board),
]
