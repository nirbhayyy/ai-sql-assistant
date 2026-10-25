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

from sql_api.models import DatabaseConnection
from sql_api.serializers import DatabaseConnectionSerializer 
from RAG.credential_encryption import encrypt_password,decrypt_password
from sqlalchemy import inspect

from RAG.user_databse import test_postgres_connection,get_saved_connection_engine
logger = logging.getLogger(__name__)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def query_api(request):
    serializer = QuerySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    connection_id = serializer.validated_data["connection_id"]
    question = serializer.validated_data["question"]

    # 1. Get the selected connection belonging to this user.
    try:
        connection = DatabaseConnection.objects.get(
            id=connection_id,
            user=request.user,
        )
    except DatabaseConnection.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Database connection not found.",
                "sql": None,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    engine = None

    try:
        # 2. Create an engine using the saved, encrypted credentials.
        try:
            engine = get_saved_connection_engine(connection)

            # Verify the selected database is reachable.
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        except Exception:
            logger.exception("Failed to connect to saved database")
            return Response(
                {
                    "success": False,
                    "message": "Could not connect to the selected database.",
                    "sql": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Generate SQL using the selected database's schema.
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
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
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
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except Exception:
            logger.exception("Unexpected SQL generation error")
            return Response(
                {
                    "success": False,
                    "message": (
                        "An unexpected error occurred while generating SQL."
                    ),
                    "sql": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 4. Validate the AI response.
        if not isinstance(sql, str):
            return Response(
                {
                    "success": False,
                    "message": "The AI returned an invalid response.",
                    "sql": None,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        sql = sql.strip()

        if sql == "UNSAFE_REQUEST":
            return Response(
                {
                    "success": False,
                    "message": (
                        "Database modifications are not allowed. "
                        "Only read-only queries are supported."
                    ),
                    "sql": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not sql:
            return Response(
                {
                    "success": False,
                    "message": "The AI returned an empty SQL query.",
                    "sql": None,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 5. Execute SQL against the SAME selected database.
        try:
            df, execution_time = execuute_sql(sql, engine=engine)

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
                status=status.HTTP_400_BAD_REQUEST,
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
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception("Unexpected SQL execution error")
            return Response(
                {
                    "success": False,
                    "message": (
                        "An unexpected error occurred while executing the query."
                    ),
                    "sql": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 6. Convert results to records.
        rows = df.to_dict(orient="records")

        # 7. Save query history.
        try:
            save_history(
                request.user.id,
                question,
                sql,
                execution_time,
            )
        except Exception:
            logger.exception("Failed to save query history")

        # 8. Generate chart data.
        try:
            chart = detect_chart(df)
        except Exception:
            logger.exception("Chart generation failed")
            chart = None

        # 9. Generate insights.
        try:
            insights = genrate_insides(df)
        except Exception:
            logger.exception("Insight generation failed")
            insights = None

        # 10. Paginate the results.
        paginator = QueryPagination()
        page = paginator.paginate_queryset(rows, request)

        return paginator.get_paginated_response(
            {
                "question": question,
                "sql": sql,
                "execution_time": execution_time,
                "row_count": len(rows),
                "chart": chart,
                "insight": insights,
                "data": page,
            }
        )

    finally:
       
        if engine is not None:
            engine.dispose()


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
        result = test_postgres_connection(
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




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_saved_db_schema(request):
    connection_id = request.data.get("connection_id")

    if not connection_id:
        return Response(
            {"success": False, "message": "connection_id is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        connection = DatabaseConnection.objects.get(
            id=connection_id,
            user=request.user
        )
    except (DatabaseConnection.DoesNotExist, ValueError, TypeError):
        return Response(
            {"success": False, "message": "Database connection not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    engine = None

    try:
        engine = get_saved_connection_engine(connection)
        inspector = inspect(engine)

        tables = inspector.get_table_names(schema="public")
        schema = {}

        for table in tables:
            columns = inspector.get_columns(table, schema="public")
            foreign_keys = inspector.get_foreign_keys(table, schema="public")

            schema[table] = {
                "columns": [
                    {
                        "name": column["name"],
                        "type": str(column["type"]),
                        "nullable": column["nullable"]
                    }
                    for column in columns
                ],
                "foreign_keys": [
                    {
                        "columns": fk["constrained_columns"],
                        "referenced_table": fk["referred_table"],
                        "referenced_columns": fk["referred_columns"]
                    }
                    for fk in foreign_keys
                ]
            }

        return Response({
            "success": True,
            "connection_id": connection.id,
            "connection_name": connection.name,
            "tables": schema
        })

    except Exception:
        logger.exception("Saved database schema retrieval failed")
        return Response(
            {
                "success": False,
                "message": "Could not retrieve the saved database schema."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    finally:
        if engine is not None:
            engine.dispose()



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_db_connection(request):
    serializer=DatabaseConnectionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data=serializer.validated_data

    try:
        result = test_postgres_connection(
            host=data["host"],
            port=data["port"],
            database=data["database"],
            username=data["username"],
            password=data["password"],
        )
        if not result.get("success"):
            return Response(
                {
                    "success": False,
                    "message": "Could not connect to the database.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    except (SQLAlchemyError, ValueError):
        return Response(
            {
                "success": False,
                "message": (
                    "Database connection failed. "
                    "Check the host, port, database, username, and password."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception:
        logger.exception("Unexpected database connection error")
        return Response(
            {
                "success": False,
                "message": "An unexpected error occurred while testing the connection.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    try:
        encrypted_password = encrypt_password(data["password"])

        connection = DatabaseConnection.objects.create(
            user=request.user,
            name=data["name"],
            db_type="postgresql",
            host=data["host"],
            port=data["port"],
            database=data["database"],
            username=data["username"],
            encrypt_password=encrypted_password,
        )
    except Exception:
        logger.exception("Failed to save database connection")
        return Response(
            {
                "success": False,
                "message": "The connection was tested, but could not be saved.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response(
        {
            "success": True,
            "message": "Database connection saved successfully.",
            "connection": {
                "id": connection.id,
                "name": connection.name,
                "db_type": connection.db_type,
                "host": connection.host,
                "port": connection.port,
                "database": connection.database,
                "username": connection.username,
                "created_at": connection.create_at,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_db_connections(request):
    connections = DatabaseConnection.objects.filter(
        user=request.user
    ).order_by("-create_at")
    print("Authenticated:", request.user.is_authenticated)
    print("User ID:", request.user.id)
    print("Username:", request.user)
    results = [
        {
            "id": connection.id,
            "name": connection.name,
            "db_type": connection.db_type,
            "host": connection.host,
            "port": connection.port,
            "database": connection.database,
            "username": connection.username,
            "created_at": connection.create_at,
        }
        for connection in connections
    ]

    return Response({
        "success": True,
        "count": len(results),
        "connections": results,
    })

    

@login_required
def Connect_database_ui(request):
    return render(request,'connect_database.html')