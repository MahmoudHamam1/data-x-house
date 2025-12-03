from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta


default_args = {
'owner': 'dx',
'depends_on_past': False,
'email_on_failure': False,
'retries': 0,
}


with DAG(
dag_id='sandbox_generate_comments',
default_args=default_args,
start_date=datetime(2025,1,1),
schedule=None,
catchup=False,
tags=['sandbox']
) as dag:
    
    # Generate comments file (Python script)
    gen_comments = BashOperator(
    task_id='gen_comments',
    bash_command='python3 /dxhouse/airflow/scripts/ingestion/batch/generate_comments.py --outdir /sandbox/comments --rows 10000'
    )

    # Optionally register the CSV into Hive raw schema as external table
    create_hive_table = BashOperator(
    task_id='create_hive_table',
    bash_command=(
    "beeline -u 'jdbc:hive2://localhost:10000' -n hive -p <HIVE_PASSWORD> -e "
    "\"CREATE EXTERNAL TABLE IF NOT EXISTS raw.social_comments("
    "comment_id STRING, customer_id STRING, product_id STRING, comment_text STRING, comment_date STRING) "
    "ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE LOCATION '/sandbox/comments' TBLPROPERTIES('skip.header.line.count'='1');\""
    )
)


gen_comments >> create_hive_table