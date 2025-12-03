from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import logging

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'test_connections_simple_spark',
    default_args=default_args,
    description='Test connections with simple Spark built-in example',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['test', 'connections', 'simple'],
)

def test_hdfs_connection():
    """Test HDFS connection using python hdfs library"""
    try:
        from hdfs import InsecureClient
        
        # Connect to HDFS
        client = InsecureClient('http://dx-master:9870')  # WebHDFS port
        
        # List root directory
        files = client.list('/')
        print(f"HDFS Root directory contents: {files}")
        
        # Try to get status
        status = client.status('/')
        print(f"HDFS Root status: {status}")
        
        return "HDFS connection successful!"
        
    except Exception as e:
        print(f"HDFS connection failed: {str(e)}")
        raise

def test_hive_connection():
    """Test Hive connection using hook"""
    try:
        from airflow.providers.apache.hive.hooks.hive import HiveServer2Hook
        
        # Test connection
        hook = HiveServer2Hook(hiveserver2_conn_id='hive')
        
        # Try to get records (simple test)
        records = hook.get_records("SHOW DATABASES", schema='default')
        print(f"Hive databases: {records}")
        
        return "Hive connection successful!"
        
    except Exception as e:
        print(f"Hive connection failed: {str(e)}")
        # Try alternative connection method
        try:
            from pyhive import hive
            conn = hive.Connection(host='dx-master', port=10000)
            cursor = conn.cursor()
            cursor.execute('SHOW DATABASES')
            results = cursor.fetchall()
            print(f"Hive databases (direct): {results}")
            return "Hive connection successful (direct method)!"
        except Exception as e2:
            print(f"Direct Hive connection also failed: {str(e2)}")
            raise

# Test basic network connectivity
test_network_task = BashOperator(
    task_id='test_network_connectivity',
    bash_command="""
        echo "Testing network connectivity..."
        
        echo "Ping dx-master:"
        ping -c 3 dx-master || echo "Ping failed"
        
        echo "Test HDFS NameNode port:"
        nc -zv dx-master 8020 || echo "HDFS port 8020 not accessible"
        
        echo "Test HDFS WebHDFS port:"
        nc -zv dx-master 9870 || echo "WebHDFS port 9870 not accessible"
        
        echo "Test Hive port:"
        nc -zv dx-master 10000 || echo "Hive port 10000 not accessible"
        
        echo "Test Spark port:"
        nc -zv dx-master 7077 || echo "Spark port 7077 not accessible"
        
        echo "Network connectivity test completed"
    """,
    dag=dag,
)

# Test HDFS
test_hdfs_task = PythonOperator(
    task_id='test_hdfs_connection',
    python_callable=test_hdfs_connection,
    dag=dag,
)

# Test Spark using built-in Pi example (simplest approach)
test_spark_simple = SparkSubmitOperator(
    task_id='test_spark_pi_example',
    application='/opt/airflow/scripts/test/pi.py',
    conn_id='spark',
    conf={
        'spark.pyspark.python': 'python3.11',
        'spark.driver.port': '7001',
        'spark.blockManager.port': '7002',
    },
    name='spark-pi-test',
    application_args=['5'],
    verbose=True,
    dag=dag,
)

# Test Hive
test_hive_task = PythonOperator(
    task_id='test_hive_connection',
    python_callable=test_hive_connection,
    dag=dag,
)

# Set task dependencies - keeping your original pattern
test_network_task >> [test_hdfs_task, test_spark_simple, test_hive_task]