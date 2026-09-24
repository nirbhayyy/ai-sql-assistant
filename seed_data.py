from faker import Faker
from dotenv import load_dotenv
import pandas as pd
import os 
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import random
load_dotenv()



DB_URL = URL.create(
    "postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

fake=Faker('en-IN')
print("USER:", os.getenv("DB_USER"))
print("HOST:", os.getenv("DB_HOST"))
print("PASSWORD:", os.getenv("DB_PASSWORD"))
print("DB_URL:", DB_URL)
engine=create_engine(DB_URL)

customers=[]
cities = ["Mumbai", "Pune", "Delhi", "Bangalore", "Hyderabad", "Nagpur"]

for _ in range(10000):
    customers.append({
        'name': fake.name(),
        'email':fake.unique.email(),
        'city':random.choice(cities),
        'join_date':fake.date_between(start_date='-3y',end_date='today')
})

customer_df=pd.DataFrame(customers)
customer_df.to_sql('customers',engine,if_exists='append',index=False)

# --- products ----

categories = {
    "Laptop": ["MacBook Air", "Dell XPS", "HP Pavilion", "Lenovo Legion"],
    "Phone": ["iPhone 15", "Samsung S24", "OnePlus 13", "Pixel 9"],
    "Accessories": ["Keyboard", "Mouse", "Headphones", "Monitor"],
    "Tablet": ["iPad Air", "Galaxy Tab", "Xiaomi Pad"]
}

products=[]

for category,items in categories.items():
    for i in items:
        products.append({
            'p_name':i,
            'category':category,
            'price':random.randint(500,120000)
})

products_df=pd.DataFrame(products)
products_df.to_sql('products',engine,if_exists='append',index=False)

# ----orders-----

orders=[]
for _ in range(10000):
    orders.append({
        'c_id':random.randint(1,1000),
        'p_id':random.randint(1,len(products)),
        'quantity':random.randint(1,5),
        'order_date':fake.date_between(start_date='-2y',end_date='today')

    })

orderd_df=pd.DataFrame(orders)
orderd_df.to_sql('orders',engine,if_exists='append',index=False)

print('database seede susesfully')




