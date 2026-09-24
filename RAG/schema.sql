TABLE customers
- c_id INT PRIMARY KEY
- name varchar
- email varchar
- city varchar
- join_date Date

TABLE products
- p_id INT PRIMARY KEY
- p_name varchar
- category varchar
- price NUMERIC

TABLE orders
- o_id INT PRIMARY KEY
- c_id INT
- p_id INT
- quantity INT
- order_date DATE


TABLE query_history
- id INTEGER PRIMARY KEY
- question TEXT
- generated_sql TEXT
- execution_time FLOAT
- created_at TIMESTAMP
