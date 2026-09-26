from django.shortcuts import render
from .serializers import Queriserializer
from RAG.genrator import genrate_sql
from RAG.executor import execuute_sql,save_history
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def query_api(request):
    serializer=Queriserializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    question=serializer._validated_data['Question']
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
