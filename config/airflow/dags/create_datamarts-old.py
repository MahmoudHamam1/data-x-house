from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta

default_args = {
'owner': 'dx',
'depends_on_past': False,
'email_on_failure': False,
'retries': 0,
'retry_delay': timedelta(minutes=10),
}


with DAG(
dag_id='build_datamarts',
default_args=default_args,
start_date=datetime(2025,1,1),
# schedule='@daily',
schedule=None,
catchup=False,
tags=['tpch','datamarts']
) as dag:
    
    create_datamarts = SparkSubmitOperator(
        task_id='create_datamarts',
        application='/opt/airflow/scripts/transform/delivery/create_datamarts.py',
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

        # # MySQL metastore connection (critical)
        'spark.hadoop.javax.jdo.option.ConnectionDriverName': 'com.mysql.cj.jdbc.Driver',
        
        # CRITICAL: Force Thrift-only mode
        'spark.hadoop.hive.metastore.uris': 'thrift://dx-master:9083',
        'spark.hadoop.javax.jdo.option.ConnectionURL': '', 
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
        },
        jars="hdfs://dx-master:8020/shared/jars/hive/hive-spark-client-3.1.3.jar,/opt/airflow/scripts/jars/mysql-connector-j-8.0.33.jar,/opt/airflow/scripts/jars/iceberg-spark-runtime-3.4_2.12-1.3.1.jar,/opt/airflow/scripts/jars/iceberg-hive-runtime-1.3.1.jar"
    
    )


create_datamarts