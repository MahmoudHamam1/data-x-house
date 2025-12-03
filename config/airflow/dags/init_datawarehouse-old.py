from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


# Default args
default_args = {
'owner': 'Data Team',
'depends_on_past': False,
'email_on_failure': False,
'email_on_retry': False,
'retries': 0,
'retry_delay': timedelta(minutes=5),
}


with DAG(
dag_id='init_datawarehouse',
default_args=default_args,
start_date=datetime(2025, 1, 1),
schedule=None,
catchup=False,
tags=['dw','iceberg']
) as dag:
    
    create_star_schema = SparkSubmitOperator(
        task_id='create_star_schema',
        application='/opt/airflow/scripts/transform/datawarehouse/create_star_schema.py',
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
        name='create_star_schema',
        # verbose=True,
        dag=dag,
    )

    populate_star_schema = SparkSubmitOperator(
        task_id='populate_star_schema',
        application='/opt/airflow/scripts/transform/datawarehouse/populate_star_schema.py',
        conn_id='spark',
        name='populate_star_schema',
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

    create_star_schema 
    # >> populate_star_schema
    