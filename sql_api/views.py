from django.shortcuts import render
from .serializers import QuerySerializer,RegistrationSerializer
from RAG.genrator import genrate_sql
from RAG.executor import execuute_sql,save_history,engine
from rest_framework.decorators import api_view
from rest_framework.response import Response
from RAG.executor import engine
from sqlalchemy import text
from .pagination import QueryPagination
from .util import detect_chart,genrate_insides
from RAG.dashboard_genrator import genrate_dashboards
import logging
from sqlalchemy.exc import SQLAlchemyError

from rest_framework import status
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.contrib.auth import login,logout,authenticate
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.decorators import permission_classes
from django.contrib.auth.decorators import login_required

from RAG.user_databse import test_prostgres_connection,get_database_schema
logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def query_api(request):
    # 1. Validate request
    serializer = QuerySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    question = serializer.validated_data["question"]

    
    try:
        sql = genrate_sql(question, engine)

    except RuntimeError as exc:
        error_message = str(exc)
        logger.warning("SQL generation failed: %s", error_message)

        if "rate limit" in error_message.lower():
            return Response(
                {
                    "success": False,
                    "message": (
                        "The AI service is temporarily rate-limited. "
                        "Please wait a few seconds and try again."
                    ),
                    "sql": None,
                },
                status=429,
            )

        return Response(
            {
                "success": False,
                "message": (
                    "SQL generation is temporarily unavailable. "
                    "Please try again."
                ),
                "sql": None,
            },
            status=503,
        )

    except Exception:
        logger.exception("Unexpected SQL generation error")

        return Response(
            {
                "success": False,
                "message": "An unexpected error occurred while generating SQL.",
                "sql": None,
            },
            status=500,
        )

    
    if not isinstance(sql, str):
        return Response(
            {
                "success": False,
                "message": "The AI returned an invalid response.",
                "sql": None,
            },
            status=502,
        )

    sql = sql.strip()

    if sql == "UNSAFE_REQUEST":
        return Response(
            {
                "success": False,
                "message": (
                    "This request involves a database modification "
                    "and is not allowed. Only read-only queries are supported."
                ),
                "sql": None,
            },
            status=400,
        )

    
    try:
        df, execution_time = execuute_sql(sql)

    except ValueError:
        logger.warning("SQL rejected by safety validation")

        return Response(
            {
                "success": False,
                "message": (
                    "The generated query did not pass SQL safety validation."
                ),
                "sql": None,
            },
            status=400,
        )

    except SQLAlchemyError:
        logger.exception("SQL execution failed")

        return Response(
            {
                "success": False,
                "message": (
                    "The query could not be executed. "
                    "Please try a different question."
                ),
                "sql": None,
            },
            status=400,
        )

    except Exception:
        logger.exception("Unexpected SQL execution error")

        return Response(
            {
                "success": False,
                "message": "An unexpected error occurred while executing the query.",
                "sql": None,
            },
            status=500,
        )

    
    rows = df.to_dict(orient="records")

    
    try:
        save_history(request.user.id,question, sql, execution_time)
    except Exception:
        logger.exception("Failed to save query history")

    
    try:
        chart = detect_chart(df)
    except Exception:
        logger.exception("Chart generation failed")
        chart = None

    try:
        insights = genrate_insides(df)
    except Exception:
        logger.exception("Insight generation failed")
        insights = None

    
    paginator = QueryPagination()
    page = paginator.paginate_queryset(rows, request)

    return paginator.get_paginated_response(
        {
            "quesion": question,
            "sql": sql,
            "execution_time": execution_time,
            "row_count": len(rows),
            "chart": chart,
            "insight": insights,
            "data": page,
        }
    )

@api_view(['POST'])
def registraton_Api(request):
    serializer=RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    User=serializer.save()

    login(request,User)
    return Response({
        'success':True,
        'message':'registation_done',
        'user':{
            'id':User.id,
            'username':User.username,
            'email':User.email,}
    },status=status.HTTP_201_CREATED)




login_required
def home(request):
    return render(request, 'index.html')


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def history_query(request):
    if request.method == "GET":
        query = text("""
            SELECT id,
                   question,
                   generated_sql,
                   execution_time,
                   created_at
            FROM query_history
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 20
        """)

        with engine.connect() as conn:
            result = conn.execute(query, {
                "user_id": request.user.id
            })

            data = [
                {
                    "question": row.question,
                    "generated_sql": row.generated_sql,
                    "execution_time": float(row.execution_time),
                    "created_at": str(row.created_at)
                }
                for row in result
            ]

        return Response(data)

    with engine.begin() as conn:
        conn.execute(
            text("""
                DELETE FROM query_history
                WHERE user_id = :user_id
            """),
            {"user_id": request.user.id}
        )

    return Response({"message": "History cleared"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    with engine.connect() as conn:
        total=conn.execute(text("""SELECT COUNT(*) FROM customers""")).scalar()

        city=conn.execute(text("""SELECT city,
                   COUNT(*) AS total
            FROM customers
            GROUP BY city
            ORDER BY total DESC
        """)).fetchall()

        year=conn.execute(text("""SELECT EXTRACT(YEAR FROM join_date) AS year,
                   COUNT(*) AS total
            FROM customers
            GROUP BY year
            ORDER BY year""")).fetchall()

    return Response({
        "total_customers": total,

        "top_city": city[0].city,

        "city_distribution": {
            "labels": [r.city for r in city],
            "values": [r.total for r in city]
        },

        "yearly_growth": {
            "labels": [str(int(r.year)) for r in year],
            "values": [r.total for r in year]
        }
    })
@login_required
def dash_board(request):
    return render(request,'dashboard.html')

@api_view(['GET'])
def dashboard_api(request):
    try:
        data=genrate_dashboards()
        return Response(data)
    except Exception as e:
        return Response({
            'Erorr':str(e)
        },status=500
        )

@ensure_csrf_cookie
def csrf_token_view(request):
    return JsonResponse({
        'message':'csrf tokken set'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username=request.data.get('username','').strip()
    password=request.data.get('password','')

    if not username or not password:
        return Response({
            'success':False,
            'message':'the username or password is wrong'
        },status=400)
    user=authenticate(request,username=username,password=password)
    if user is None:
        return Response({
            "success": False,
            "message": "Invalid username or password."
        },status=400)
    login(request,user)
    return Response({
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_api(request):
    logout(request)

    return Response({
        "success": True,
        "message": "Logout successful."
    })


def login_page(request):
    return render(request,'login.html')

def register_page(request):
    return render(request,'register.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUser(request):
    return Response({
        'username':request.user.username,
        'email':request.user.email,
        'Is_Authenticated': True
    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_databse_conn(request):
    data=request.data

    required_fields = [
        "host",
        "port",
        "database",
        "username",
        "password"
    ]

    if any(not data.get(field) for field in required_fields):
        return Response(
            {"error": "All database fields are required"},
            status=status.HTTP_400_BAD_REQUEST
          )
    try:
        result = test_prostgres_connection(
            host=data["host"],
            port=data["port"],
            database=data["database"],
            username=data["username"],
            password=data["password"]
        )

        return Response(result)

    except Exception as e:
        import logging
        logging.exception("User database connection failed")

        return Response(
            {
            "success": False,
            "message": str(e)
            },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_user_database_schema(request):
    data=request.data

    required_fields = [
        "host",
        "port",
        "database",
        "username",
        "password"
    ]

    if any(not data.get(field) for field in required_fields):
        return Response(
            {"error": "All database fields are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        schema = get_database_schema(
            host=data["host"],
            port=data["port"],
            database=data["database"],
            username=data["username"],
            password=data["password"]
        )

        return Response({
            "success": True,
            "tables": schema
        })

    except Exception as e:
        import logging
        logging.exception("Schema retrieval failed")

        return Response(
        {
            "success": False,
            "message": str(e)
        },
        status=status.HTTP_400_BAD_REQUEST
    )