from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import logging

default_args = {
    'owner': 'hadoop',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    'sandbox_sentiment_dag',
    default_args=default_args,
    description='Init Transformation and Delivery Databases in addition to the star schema',
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['spark', 'sentiment', 'sandbox'],
)


generate_comments = SparkSubmitOperator(
    task_id='generate_comments',
    application='/opt/airflow/scripts/ingestion/batch/generate_comments.py',
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
        'spark.sql.warehouse.dir': 'hdfs://dx-master:8020/user/hive/warehouse',
        
        'spark.sql.catalog.spark_catalog.type': 'hive',
        'spark.hadoop.hive.metastore.schema.verification': 'false',
        'spark.sql.catalog.local':          'org.apache.iceberg.spark.SparkCatalog',
        'spark.sql.catalog.local.type':     'hadoop',
        'spark.sql.catalog.local.warehouse': 'hdfs://dx-master:8020/user/hive/warehouse',

        'spark.hadoop.javax.jdo.option.ConnectionDriverName': 'com.mysql.cj.jdbc.Driver',
        
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
    name='generate_comments',
    # verbose=True,
    dag=dag,
)

sentiment_analysis = SparkSubmitOperator(
    task_id='sentiment_analysis',
    application='/opt/airflow/scripts/transform/sandbox/sentiment_analysis_spark.py',
    conn_id='spark',
    conf={
        'spark.pyspark.python': 'python3.11',
        'spark.driver.port': '7004',
        'spark.blockManager.port': '7005',
        
        # Force all metastore settings explicitly
        'spark.sql.catalogImplementation': 'hive',
        'spark.sql.hive.metastore.uris': 'thrift://dx-master:9083',
        # 'spark.sql.hive.metastore.version': '3.1.3',
        'spark.sql.hive.metastore.version': '2.3.9',  # Match Spark's builtin version
        'spark.sql.hive.metastore.jars': 'builtin',   # Use Spark's builtin JARs
        'spark.sql.warehouse.dir': 'hdfs://dx-master:8020/user/hive/warehouse',
        
        'spark.sql.catalog.spark_catalog.type': 'hive',
        'spark.hadoop.hive.metastore.schema.verification': 'false',
        'spark.sql.catalog.local':          'org.apache.iceberg.spark.SparkCatalog',
        'spark.sql.catalog.local.type':     'hadoop',
        'spark.sql.catalog.local.warehouse': 'hdfs://dx-master:8020/user/hive/warehouse',

        'spark.hadoop.javax.jdo.option.ConnectionDriverName': 'com.mysql.cj.jdbc.Driver',
        
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
    name='sentiment_analysis',
    application_args=[
        "--raw_db", "raw",
        "--raw_table", "customer_comments",
        "--dim_db", "datawarehouse",
        "--dim_table", "dim_customer",
        "--sandbox_db", "sandbox",
        "--sandbox_table", "sentiment_analysis_results"
    ],
    # verbose=True,
    dag=dag,
)


generate_comments >> sentiment_analysis
