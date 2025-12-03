from __future__ import annotations
import pendulum
import datetime
import logging

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Get the logger for this DAG file
log = logging.getLogger(__name__)

# Define the default arguments for the DAG
with DAG(
    dag_id="test_dag",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    schedule=None,
    tags=["test", "getting_started"],
    catchup=False,
) as dag:
    # Task 1: A simple BashOperator to print a message
    hello_task = BashOperator(
        task_id="hello_task",
        bash_command="echo 'Hello from Airflow!'",
    )

    # Task 2: A PythonOperator that uses the pendulum library
    def get_current_time():
        current_time = pendulum.now()
        log.info(f"The current time is: {current_time.to_iso8601_string()}")
        return str(current_time)

    time_task = PythonOperator(
        task_id="time_task",
        python_callable=get_current_time,
    )

    # Task 3: Another BashOperator to show a task dependency
    goodbye_task = BashOperator(
        task_id="goodbye_task",
        bash_command="echo 'Goodbye from Airflow!'",
    )

    # Define the task dependencies
    # This means hello_task will run first, then time_task, and finally goodbye_task
    hello_task >> time_task >> goodbye_task