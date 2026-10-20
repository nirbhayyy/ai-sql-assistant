from django.urls import path
from .views import (query_api,home,history_query,dashboard_view,
                    dash_board,dashboard_api,registraton_Api,csrf_token_view,
                    login_api,logout_api,login_page,register_page,getUser,
                    test_databse_conn)

urlpatterns = [
    path('',home,name='home'),
    path('query/',query_api,name='query'),
    path('history/',history_query),
    path('dash-data/',dashboard_api),
    path('dash/',dash_board),
    path('reg-api/',registraton_Api),
    path('csrf/',csrf_token_view),
    path('login/',login_api),
    path('logout/',logout_api),
    path('login-page/',login_page),
    path('reg-page/',register_page),
    path('me/',getUser),
    path('test-db-conn/',test_databse_conn),
]
