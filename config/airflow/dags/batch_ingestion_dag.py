from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime
import os

# Directory where scripts are stored inside the Airflow container
SCRIPTS_DIR = "/opt/airflow/scripts/ingestion/batch"

# Dynamically find all .sh scripts
script_files = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".sh")]

with DAG(
    dag_id="batch_ingestion_dag",
    description="Batch ingestion via Sqoop and Hive using SSH to dx-master",
    schedule=None,  # Trigger manually or add cron
    start_date=datetime(2025, 10, 1),
    catchup=False,
    tags=["batch", "sqoop", "hive", "ssh"],
) as dag:

    tasks = []

    for script in script_files:
        script_path = os.path.join(SCRIPTS_DIR, script)
        task_id = f"run_{os.path.splitext(script)[0]}"

        # Read the script content to send over SSH
        with open(script_path, "r") as f:
            script_content = f.read()

        # Create SSHOperator task
        task = SSHOperator(
            task_id=task_id,
            ssh_conn_id="hadoop_ssh",
            command=f""" {script_content}""",
            conn_timeout=60,   # seconds to wait for connection
            cmd_timeout=1800,  # seconds to wait for command completion
        )

        tasks.append(task)

    # Run scripts sequentially (if order matters)
    for i in range(1, len(tasks)):
        tasks[i - 1] >> tasks[i]
