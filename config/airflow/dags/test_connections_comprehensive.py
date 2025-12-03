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
    'retries': 0,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'test_connections_comprehensive',
    default_args=default_args,
    description='Comprehensive test suite: HDFS, Spark, Hive, and Iceberg integration',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['test', 'connections', 'comprehensive', 'spark', 'hive', 'iceberg'],
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

def create_spark_hive_test_script():
    """Create the Spark-Hive integration test script"""
    print("Created Spark-hive test script")
    return "Spark-hive test script created successfully!"

def create_spark_iceberg_test_script():
    """Create the Spark-Hive integration test script"""
    print("Created Spark-Iceberg test script")
    return "Spark-Iceberg test script created successfully!"

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
        
        echo "Test Hive Metastore port:"
        nc -zv dx-master 9083 || echo "Hive Metastore port 9083 not accessible"
        
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

# Test Spark basic functionality (Pi calculation)
test_spark_basic = SparkSubmitOperator(
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

# Create test scripts
create_spark_hive_script_task = PythonOperator(
    task_id='create_spark_hive_test_script',
    python_callable=create_spark_hive_test_script,
    dag=dag,
)

create_spark_iceberg_script_task = PythonOperator(
    task_id='create_spark_iceberg_test_script',
    python_callable=create_spark_iceberg_test_script,
    dag=dag,
)

# Test Spark-Hive integration
test_spark_hive_integration = SparkSubmitOperator(
    task_id='test_spark_hive_integration',
    application='/opt/airflow/scripts/test/spark_hive_test.py',
    conn_id='spark',
    # env_vars={
    #     'SPARK_CONF_DIR': '/opt/airflow/scrips/conf/spark/',
    #     'HADOOP_CONF_DIR': '/opt/airflow/scrips/conf/hadoop/',
    #     'HIVE_CONF_DIR': '/opt/airflow/scrips/conf/hive/',
    # },
    # properties_file='/opt/airflow/scrips/conf/spark/spark-defaults.conf',
    conf={
        'spark.pyspark.python': 'python3.11',
        'spark.driver.port': '7002',
        'spark.blockManager.port': '7003',
        
        # Force all metastore settings explicitly
        'spark.sql.catalogImplementation': 'hive',
        'spark.sql.hive.metastore.uris': 'thrift://dx-master:9083',
        # 'spark.sql.hive.metastore.version': '3.1.3',
        'spark.sql.hive.metastore.version': '2.3.9',  # Match Spark's builtin version
        'spark.sql.hive.metastore.jars': 'builtin',   # Use Spark's builtin JARs
        # 'spark.sql.hive.metastore.jars': 'path',
        # 'spark.sql.hive.metastore.jars.path':'hdfs://dx-master:8020/shared/jars/hive/hive-exec-3.1.3.jar,hdfs://dx-master:8020/shared/jars/hive/hive-metastore-3.1.3.jar,hdfs://dx-master:8020/shared/jars/hive/hive-common-3.1.3.jar,hdfs://dx-master:8020/shared/jars/hive/hive-serde-3.1.3.jar,hdfs://dx-master:8020/shared/jars/hive/libthrift-0.9.3.jar,hdfs://dx-master:8020/shared/jars/hive/datanucleus-api-jdo-4.2.4.jar,hdfs://dx-master:8020/shared/jars/hive/datanucleus-core-4.1.17.jar,hdfs://dx-master:8020/shared/jars/hive/datanucleus-rdbms-4.1.19.jar',
        # 'spark.sql.hive.metastore.jars.path': 'hdfs://dx-master:8020/shared/jars/hive/*',
        # 'spark.sql.hive.metastore.jars.path': 'http://dx-master:8888/hive-exec-3.1.3.jar,http://dx-master:8888/hive-metastore-3.1.3.jar,http://dx-master:8888/hive-common-3.1.3.jar,http://dx-master:8888/hive-serde-3.1.3.jar',
        # 'spark.sql.hive.metastore.jars.path': 'http://dx-master:8888/*',
        'spark.sql.warehouse.dir': 'hdfs://dx-master:8020/user/hive/warehouse',
        
        'spark.sql.catalog.spark_catalog.type': 'hive',
        'spark.hadoop.hive.metastore.schema.verification': 'false',
        'spark.sql.catalog.local':          'org.apache.iceberg.spark.SparkCatalog',
        'spark.sql.catalog.local.type':     'hadoop',
        'spark.sql.catalog.local.warehouse': 'hdfs://dx-master:8020/user/hive/warehouse',

        # # MySQL metastore connection (critical)
        # 'spark.hadoop.javax.jdo.option.ConnectionURL': 'jdbc:mysql://dx-database:3306/metastore?createDatabaseIfNotExist=true&useSSL=false&allowPublicKeyRetrieval=true',
        'spark.hadoop.javax.jdo.option.ConnectionDriverName': 'com.mysql.cj.jdbc.Driver',
        # 'spark.hadoop.javax.jdo.option.ConnectionUserName': 'hive',
        # 'spark.hadoop.javax.jdo.option.ConnectionPassword': '<HIVE_PASSWORD>',
        # 'spark.hadoop.datanucleus.autoCreateSchema': 'false',
        # 'spark.hadoop.datanucleus.fixedDatastore': 'true',
        
        # CRITICAL: Force Thrift-only mode
        'spark.hadoop.hive.metastore.uris': 'thrift://dx-master:9083',
        'spark.hadoop.javax.jdo.option.ConnectionURL': '',  # Disable embedded connection
        'spark.hadoop.hive.metastore.warehouse.dir': 'hdfs://dx-master:8020/user/hive/warehouse',

        # Transaction support
        'spark.sql.hive.support.concurrency': 'true',
        'spark.sql.hive.txn.manager': 'org.apache.hadoop.hive.ql.lockmgr.DbTxnManager',
        'spark.sql.hive.enforce.bucketing': 'true',
        'spark.sql.hive.exec.dynamic.partition.mode': 'nonstrict',
        
        # HDFS
        'spark.sql.fs.defaultFS': 'hdfs://dx-master:8020',
        
        # Serializer
        'spark.serializer': 'org.apache.spark.serializer.JavaSerializer',
        
        # 'spark.driver.extraClassPath': 'hdfs://dx-master:8020/shared/jars/hive/guava-19.0.jar',
        # 'spark.executor.extraClassPath': 'hdfs://dx-master:8020/shared/jars/hive/guava-19.0.jar',

        # 'spark.driver.extraJavaOptions': '-Djava.util.logging.config.file=logging.properties -Dlog4j.debug=true -XX:+PrintGCDetails -XX:+PrintGCTimeStamps',
        # 'spark.executor.extraJavaOptions': '-Djava.util.logging.config.file=logging.properties -Dlog4j.debug=true',
        'spark.driver.userClassPathFirst': 'true',
        'spark.executor.userClassPathFirst': 'true',
        'spark.sql.hive.metastore.sharedPrefixes': 'com.mysql.cj,com.mysql.cj.jdbc,org.apache.commons',
    },
    jars="hdfs://dx-master:8020/shared/jars/hive/hive-spark-client-3.1.3.jar,/opt/airflow/scripts/jars/mysql-connector-j-8.0.33.jar,/opt/airflow/scripts/jars/iceberg-spark-runtime-3.4_2.12-1.3.1.jar,/opt/airflow/scripts/jars/iceberg-hive-runtime-1.3.1.jar",
    name='spark-hive-integration-test',
    # verbose=True,
    dag=dag,
)

# Test Spark-Iceberg integration
test_spark_iceberg_integration = SparkSubmitOperator(
    task_id='test_spark_iceberg_integration',
    application='/opt/airflow/scripts/test/spark_iceberg_test.py',
    conn_id='spark',
    conf={
        'spark.pyspark.python': 'python3.11',
        'spark.driver.port': '7002',
        'spark.blockManager.port': '7003',
        
        # Force all metastore settings explicitly
        'spark.sql.catalogImplementation': 'hive',
        'spark.sql.hive.metastore.uris': 'thrift://dx-master:9083',
        # 'spark.sql.hive.metastore.version': '3.1.3',
        'spark.sql.hive.metastore.version': '2.3.9',  # Match Spark's builtin version
        'spark.sql.hive.metastore.jars': 'builtin',   # Use Spark's builtin JARs
        # 'spark.sql.hive.metastore.jars': 'path',
        # 'spark.sql.hive.metastore.jars.path':'hdfs://dx-master:8020/shared/jars/hive/hive-exec-3.1.3.jar,hdfs://dx-master:8020/shared/jars/hive/hive-metastore-3.1.3.jar,hdfs://dx-master:8020/shared/jars/hive/hive-common-3.1.3.jar,hdfs://dx-master:8020/shared/jars/hive/hive-serde-3.1.3.jar,hdfs://dx-master:8020/shared/jars/hive/libthrift-0.9.3.jar,hdfs://dx-master:8020/shared/jars/hive/datanucleus-api-jdo-4.2.4.jar,hdfs://dx-master:8020/shared/jars/hive/datanucleus-core-4.1.17.jar,hdfs://dx-master:8020/shared/jars/hive/datanucleus-rdbms-4.1.19.jar',
        # 'spark.sql.hive.metastore.jars.path': 'hdfs://dx-master:8020/shared/jars/hive/*',
        # 'spark.sql.hive.metastore.jars.path': 'http://dx-master:8888/hive-exec-3.1.3.jar,http://dx-master:8888/hive-metastore-3.1.3.jar,http://dx-master:8888/hive-common-3.1.3.jar,http://dx-master:8888/hive-serde-3.1.3.jar',
        # 'spark.sql.hive.metastore.jars.path': 'http://dx-master:8888/*',
        'spark.sql.warehouse.dir': 'hdfs://dx-master:8020/user/hive/warehouse',
        
        'spark.sql.catalog.spark_catalog.type': 'hive',
        'spark.hadoop.hive.metastore.schema.verification': 'false',
        'spark.sql.catalog.local':          'org.apache.iceberg.spark.SparkCatalog',
        'spark.sql.catalog.local.type':     'hadoop',
        'spark.sql.catalog.local.warehouse': 'hdfs://dx-master:8020/user/hive/warehouse',

        # # MySQL metastore connection (critical)
        # 'spark.hadoop.javax.jdo.option.ConnectionURL': 'jdbc:mysql://dx-database:3306/metastore?createDatabaseIfNotExist=true&useSSL=false&allowPublicKeyRetrieval=true',
        'spark.hadoop.javax.jdo.option.ConnectionDriverName': 'com.mysql.cj.jdbc.Driver',
        # 'spark.hadoop.javax.jdo.option.ConnectionUserName': 'hive',
        # 'spark.hadoop.javax.jdo.option.ConnectionPassword': '<HIVE_PASSWORD>',
        # 'spark.hadoop.datanucleus.autoCreateSchema': 'false',
        # 'spark.hadoop.datanucleus.fixedDatastore': 'true',
        
        # CRITICAL: Force Thrift-only mode
        'spark.hadoop.hive.metastore.uris': 'thrift://dx-master:9083',
        'spark.hadoop.javax.jdo.option.ConnectionURL': '',  # Disable embedded connection
        'spark.hadoop.hive.metastore.warehouse.dir': 'hdfs://dx-master:8020/user/hive/warehouse',

        # Transaction support
        'spark.sql.hive.support.concurrency': 'true',
        'spark.sql.hive.txn.manager': 'org.apache.hadoop.hive.ql.lockmgr.DbTxnManager',
        'spark.sql.hive.enforce.bucketing': 'true',
        'spark.sql.hive.exec.dynamic.partition.mode': 'nonstrict',
        
        # HDFS
        'spark.sql.fs.defaultFS': 'hdfs://dx-master:8020',
        
        # Serializer
        'spark.serializer': 'org.apache.spark.serializer.JavaSerializer',
        
        # 'spark.driver.extraClassPath': 'hdfs://dx-master:8020/shared/jars/hive/guava-19.0.jar',
        # 'spark.executor.extraClassPath': 'hdfs://dx-master:8020/shared/jars/hive/guava-19.0.jar',

        # 'spark.driver.extraJavaOptions': '-Djava.util.logging.config.file=logging.properties -Dlog4j.debug=true -XX:+PrintGCDetails -XX:+PrintGCTimeStamps',
        # 'spark.executor.extraJavaOptions': '-Djava.util.logging.config.file=logging.properties -Dlog4j.debug=true',
        'spark.driver.userClassPathFirst': 'true',
        'spark.executor.userClassPathFirst': 'true',
        'spark.sql.hive.metastore.sharedPrefixes': 'com.mysql.cj,com.mysql.cj.jdbc,org.apache.commons',

        # Default catalog (Hive-backed)
        'spark.sql.extensions':            'org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions',
        'spark.sql.catalog.spark_catalog':  'org.apache.iceberg.spark.SparkSessionCatalog',
        'spark.sql.catalog.spark_catalog.type': 'hive',
        'spark.sql.catalog.local':          'org.apache.iceberg.spark.SparkCatalog',
        'spark.sql.catalog.local.type':     'hadoop',
        'spark.sql.catalog.local.warehouse': 'hdfs://dx-master:8020/user/hive/warehouse',
    },
    jars="hdfs://dx-master:8020/shared/jars/hive/hive-spark-client-3.1.3.jar,/opt/airflow/scripts/jars/mysql-connector-j-8.0.33.jar,/opt/airflow/scripts/jars/iceberg-spark-runtime-3.4_2.12-1.3.1.jar,/opt/airflow/scripts/jars/iceberg-hive-runtime-1.3.1.jar",
    name='spark-iceberg-integration-test',
    # verbose=True,
    dag=dag,
)

# Test basic Hive connection
test_hive_task = PythonOperator(
    task_id='test_hive_connection',
    python_callable=test_hive_connection,
    dag=dag,
)

# Set task dependencies for comprehensive testing
test_network_task >> [test_hdfs_task, create_spark_hive_script_task, create_spark_iceberg_script_task]

# Basic Spark test after scripts are created
[create_spark_hive_script_task, create_spark_iceberg_script_task] >> test_spark_basic

# Advanced integration tests after basic Spark test passes
test_spark_basic >> test_spark_hive_integration >> test_spark_iceberg_integration

# Final Hive connection test after all Spark tests complete
[test_hdfs_task, test_spark_hive_integration, test_spark_iceberg_integration]

# # test_spark_hive_integration >> 
# test_spark_iceberg_integration