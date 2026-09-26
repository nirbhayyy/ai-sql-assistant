import os
from google import genai
from dotenv import load_dotenv
from .retriever import retrieve_schema
from openai import OpenAI
from groq import Groq
load_dotenv()


# client=genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
# client=OpenAI(api_key=os.getenv('OPEN_AI_API'))
client=Groq(api_key=os.getenv('GEOQ_API'))

def genrate_sql(question):
    docs=retrieve_schema(question)
    context='\n\n'.join(doc.page_content for doc in docs)

    prompt = f"""
You are an expert PostgreSQL SQL generator.

Your task is to convert a natural language question into a valid PostgreSQL query.

## Database Schema
{context}

## Rules
- Use ONLY tables and columns present in the schema.
- Do NOT invent tables, columns, or relationships.
- Generate syntactically correct PostgreSQL SQL.
- Use appropriate JOINs, GROUP BY, ORDER BY, LIMIT, and aggregate functions when needed.
- If the question asks for "top" or "highest", sort in DESC order.
- If the question asks for "latest", use the appropriate date column in DESC order.
- Return ONLY the SQL query.
- Do NOT include explanations, markdown, comments, or code fences.

## User Question
{question}

## SQL
"""
    # esponse = client.models.generate_content(
    #     model="gemini-2.5-flash",
    #     contents=prompt
    # )
    try:
        # responce=client.chat.completions.create(
        #     model="gpt-5-mini",
        #     messages=[
        #         {
        #             "role": "system",
        #             "content": "You generate PostgreSQL SQL only."
        #         },
        #         {
        #             "role": "user",
        #             "content": prompt
        #         }
        #     ],
        #     temperature=0
        # )

        responce=client.chat.completions.create(
            model='openai/gpt-oss-120b',
            messages=[{"role": "system", "content": "You are a PostgreSQL SQL generator."},
                      {"role": "user", "content": prompt}],
                      temperature=0

        )
# Show all customers from Pune
        return responce.choices[0].message.content.strip()
    except Exception as e:  
         return f"erorr {e} "

if __name__=="__main__":
    Q=input('ASK: ')

    sql=genrate_sql(Q)

    print("\nGenerated SQL:\n")
    print(sql)
    
