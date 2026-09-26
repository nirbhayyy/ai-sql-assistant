from django.shortcuts import render
from .serializers import QuerySerializer
from RAG.genrator import genrate_sql
from RAG.executor import execuute_sql,save_history
from rest_framework.decorators import api_view
from rest_framework.response import Response
from RAG.executor import engine
from sqlalchemy import text
from .pagination import QueryPagination
from .util import detect_chart


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
    paginator=QueryPagination()
    page=paginator.paginate_queryset(rows,request)


    return paginator.get_paginated_response({
        'quesion':question,
        'sql':sql,
        'execution_time':time,
        'row_count':len(rows),
        'chart':chart,
        'data':page
    })

def home(request):
    return render(request, 'index.html')

@api_view(['POST'])
def history_query(request):
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
        rows=[dict(row.map) for row in result]

    return Response(rows)



