from pyspark.sql import SparkSession

spark = (
    SparkSession.builder \
    .appName("CreateStarSchema") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("spark.sql.warehouse.dir", "hdfs://dx-master:8020/user/hive/warehouse") \
    .config("spark.sql.hive.metastore.uris", "thrift://dx-master:9083") \
    .config("spark.sql.catalog.spark_catalog.type", "hive") \
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.local.type", "hadoop") \
    .config("spark.sql.catalog.local.warehouse", "hdfs://dx-master:8020/user/hive/warehouse") \
    .enableHiveSupport() \
    .getOrCreate()
)

# spark.conf.set("spark.sql.catalog.datawarehouse", "org.apache.iceberg.spark.SparkCatalog")
# spark.conf.set("spark.sql.catalog.datawarehouse.catalog-impl", "org.apache.iceberg.hive.HiveCatalog")
# spark.conf.set("spark.sql.catalog.datawarehouse.uri", "thrift://dx-master:9083")
# spark.conf.set("spark.sql.catalog.datawarehouse.io-impl", "org.apache.iceberg.hadoop.HadoopFileIO")
# spark.conf.set("spark.sql.catalog.datawarehouse.warehouse", "hdfs://dx-master:8020/warehouse")

# spark.conf.set("spark.sql.catalog.delivery", "org.apache.iceberg.spark.SparkCatalog")
# spark.conf.set("spark.sql.catalog.delivery.catalog-impl", "org.apache.iceberg.hive.HiveCatalog")
# spark.conf.set("spark.sql.catalog.delivery.uri", "thrift://dx-master:9083")
# spark.conf.set("spark.sql.catalog.delivery.io-impl", "org.apache.iceberg.hadoop.HadoopFileIO")
# spark.conf.set("spark.sql.catalog.delivery.warehouse", "hdfs://dx-master:8020/warehouse")

# spark.conf.set("spark.sql.catalog.sandbox", "org.apache.iceberg.spark.SparkCatalog")
# spark.conf.set("spark.sql.catalog.sandbox.catalog-impl", "org.apache.iceberg.hive.HiveCatalog")
# spark.conf.set("spark.sql.catalog.sandbox.uri", "thrift://dx-master:9083")
# spark.conf.set("spark.sql.catalog.sandbox.io-impl", "org.apache.iceberg.hadoop.HadoopFileIO")
# spark.conf.set("spark.sql.catalog.sandbox.warehouse", "hdfs://dx-master:8020/warehouse")


databases = [
    "datawarehouse",
    "delivery",
    "sandbox"
]

for db in databases:
    spark.sql(f"DROP DATABASE IF EXISTS {db} CASCADE")

for db in databases:
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {db}")

# Fact Table
spark.sql("""
CREATE TABLE IF NOT EXISTS datawarehouse.fact_sales (
    orderkey BIGINT,
    partkey BIGINT,
    suppkey BIGINT,
    custkey BIGINT,
    extendedprice DOUBLE,
    discount DOUBLE,
    tax DOUBLE,
    quantity DOUBLE,
    orderdate DATE,
    year INT,
    month INT,
    day INT
)
USING ICEBERG
PARTITIONED BY (year, month, day)
""")

# Dimension Tables
spark.sql("""
CREATE TABLE IF NOT EXISTS datawarehouse.dim_customer (
    custkey BIGINT,
    name STRING,
    address STRING,
    phone STRING,
    acctbal DOUBLE,
    mktsegment STRING,
    nationkey BIGINT
)
USING ICEBERG
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS datawarehouse.dim_supplier (
    suppkey BIGINT,
    name STRING,
    address STRING,
    phone STRING,
    acctbal DOUBLE,
    nationkey BIGINT
)
USING ICEBERG
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS datawarehouse.dim_part (
    partkey BIGINT,
    name STRING,
    mfgr STRING,
    brand STRING,
    type STRING,
    size INT,
    container STRING,
    retailprice DOUBLE
)
USING ICEBERG
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS datawarehouse.dim_order (
    orderkey BIGINT,
    orderstatus STRING,
    totalprice DOUBLE,
    orderdate DATE,
    priority STRING,
    custkey BIGINT
)
USING ICEBERG
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS datawarehouse.dim_geography (
    regionkey BIGINT,
    regionname STRING,
    nationkey BIGINT,
    nationname STRING
)
USING ICEBERG
""")

spark.sql("""
CREATE TABLE IF NOT EXISTS datawarehouse.dim_time (
    datekey DATE,
    year INT,
    quarter INT,
    month INT,
    day INT
)
USING ICEBERG
""")

spark.stop()
