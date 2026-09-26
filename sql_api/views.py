from django.shortcuts import render
from .serializers import QuerySerializer
from RAG.genrator import genrate_sql
from RAG.executor import execuute_sql,save_history
from rest_framework.decorators import api_view
from rest_framework.response import Response
from RAG.executor import engine
from sqlalchemy import text


@api_view(['POST'])
def query_api(request):
    serializer=QuerySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    question=serializer.validated_data['question']
    sql=genrate_sql(question)
    df,time=execuute_sql(sql)
    save_history(question,sql,time)

    return Response({
        'quesion':question,
        'sql':sql,
        'execution_time':time,
        'row_count':len(df),
        'data':df.to_dict(orient='records')
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



