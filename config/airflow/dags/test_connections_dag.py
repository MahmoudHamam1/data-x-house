from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
import logging


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'test_connections_dag',
    default_args=default_args,
    description='Test all connections to Hadoop ecosystem',
    schedule=None,  # Manual trigger only (Airflow 3.0 syntax)
    catchup=False,
    tags=['test', 'connections'],
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

def test_spark_connection():
    """Test Spark connection with proper session management"""
    
    try:
        from pyspark.sql import SparkSession
        from pyspark import SparkContext
        
        # Stop any existing SparkContext
        try:
            if SparkContext._active_spark_context:
                SparkContext._active_spark_context.stop()
                logging.info("Stopped existing SparkContext")
        except:
            pass
        
        # Create new SparkSession with proper configuration
        spark = SparkSession.builder \
            .appName("AirflowSparkTest") \
            .master("spark://dx-master:7077") \
            .config("spark.sql.warehouse.dir", "hdfs://dx-master:8020/user/hive/warehouse") \
            .config("spark.sql.catalogImplementation", "hive") \
            .config("spark.sql.hive.metastore.uris", "thrift://dx-master:9083") \
            .config("spark.serializer", "org.apache.spark.serializer.JavaSerializer") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .enableHiveSupport() \
            .getOrCreate()
        
        # Test basic Spark functionality
        df = spark.range(10).toDF("number")
        count = df.count()
        logging.info(f"Spark test successful. DataFrame count: {count}")
        
        # Test Hive integration
        try:
            spark.sql("SHOW DATABASES").show()
            logging.info("Hive integration test successful")
        except Exception as hive_error:
            logging.warning(f"Hive integration test failed: {str(hive_error)}")
        
        # Clean up
        spark.stop()
        logging.info("SparkSession stopped successfully")
        
        return "Spark connection: SUCCESS"
        
    except Exception as e:
        logging.error(f"Spark connection failed: {str(e)}")
        # Ensure cleanup even on failure
        try:
            if 'spark' in locals():
                spark.stop()
        except:
            pass
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

# Test HDFS
test_hdfs_task = PythonOperator(
    task_id='test_hdfs_connection',
    python_callable=test_hdfs_connection,
    dag=dag,
)

# Test Hive
test_hive_task = PythonOperator(
    task_id='test_hive_connection',
    python_callable=test_hive_connection,
    dag=dag,
)

# Test Spark
test_spark_task = PythonOperator(
    task_id='test_spark_connection',
    python_callable=test_spark_connection,
    dag=dag,
)

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

sqoop_connection = SSHOperator(
    task_id='test_sqoop_list_databases',
    ssh_conn_id='hadoop_ssh',
    command='''
        sqoop list-databases \
        --connect jdbc:mysql://dx-database:3306 \
        --username hive \
        --password <HIVE_PASSWORD>
    ''',
    dag=dag
)
# Set task dependencies
test_network_task >> [test_hdfs_task, test_hive_task, test_spark_task, sqoop_connection]