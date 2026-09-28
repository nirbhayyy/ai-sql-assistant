from django.shortcuts import render
from .serializers import QuerySerializer
from RAG.genrator import genrate_sql
from RAG.executor import execuute_sql,save_history
from rest_framework.decorators import api_view
from rest_framework.response import Response
from RAG.executor import engine
from sqlalchemy import text
from .pagination import QueryPagination
from .util import detect_chart,genrate_insides


@api_view(['POST'])
def query_api(request):
    serializer=QuerySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    question=serializer.validated_data['question']
    sql=genrate_sql(question)
    df,time=execuute_sql(sql)
    save_history(question,sql,time)
    rows=df.to_dict(orient='records')
    chart=detect_chart(df)
    insides=genrate_insides(df)
    paginator=QueryPagination()
    page=paginator.paginate_queryset(rows,request)


    return paginator.get_paginated_response({
        'quesion':question,
        'sql':sql,
        'execution_time':time,
        'row_count':len(rows),
        'chart':chart,
        "insight": insides,
        'data':page
    })

def home(request):
    return render(request, 'index.html')

@api_view(['GET','DELETE'])
def history_query(request):
    if request.method=='GET':
        query = text("""
        SELECT id,
               question,
               generated_sql,
               execution_time,
               created_at
        FROM query_history
        ORDER BY created_at DESC
        LIMIT 20
    """)

        with engine.connect() as conn:
            result=conn.execute(query)
            data = [
                {
                    "question": row.question,
                    "generated_sql": row.generated_sql,
                    "execution_time": float(row.execution_time),
                    "created_at": str(row.created_at)
                }for row  in result]
        

            return Response(data)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM query_history"))
    return Response({"message": "History cleared"})

@api_view(['GET'])
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

def dash_board(request):
    return render(request,'dashboard.html')