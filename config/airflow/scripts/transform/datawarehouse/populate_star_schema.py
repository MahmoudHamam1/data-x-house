from pyspark.sql import SparkSession
from pyspark.sql.functions import year, month, dayofmonth,to_date

spark = (
    SparkSession.builder
    .appName("PopulateStarSchema")
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog")
    .config("spark.sql.catalog.spark_catalog.type", "hive")
    .config("spark.sql.catalog.spark_catalog.uri", "thrift://dx-master:9083")
    .enableHiveSupport()
    .getOrCreate()
)

# Load raw tables
customer = spark.table("raw.customer")
supplier = spark.table("raw.supplier")
part = spark.table("raw.part")
orders = spark.table("raw.orders")
nation = spark.table("raw.nation")
region = spark.table("raw.region")
lineitem = spark.table("raw.lineitem")

# ---- DIMENSIONS ---- #
from pyspark.sql.types import DoubleType
from pyspark.sql.functions import col, year, month, dayofmonth

# --- DIMENSIONS ---
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, dayofmonth
from pyspark.sql.types import DoubleType

# ----------------------------
# Initialize Spark with Iceberg + Hive Metastore
# ----------------------------
spark = (
    SparkSession.builder
    .appName("Create Star Schema")
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog")
    .config("spark.sql.catalog.spark_catalog.type", "hive")
    .config("spark.sql.catalog.spark_catalog.uri", "thrift://dx-master:9083")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .enableHiveSupport()
    .getOrCreate()
)

# ----------------------------
# Create Databases (if not exists)
# ----------------------------
for db in ["datawarehouse", "delivery", "sandbox"]:
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {db}")

# ----------------------------
# Load Raw TPCH Tables
# ----------------------------
customer = spark.table("raw.customer")
orders = spark.table("raw.orders")
supplier = spark.table("raw.supplier")
part = spark.table("raw.part")
nation = spark.table("raw.nation")
region = spark.table("raw.region")
lineitem = spark.table("raw.lineitem")

# ----------------------------
# Create Dimension Tables
# ----------------------------
customer_dim = (
    customer.selectExpr(
        "c_custkey as custkey",
        "c_name as name",
        "c_address as address",
        "c_phone as phone",
        "c_mktsegment as mktsegment",
        "c_nationkey as nationkey",
        "c_acctbal as acctbal"
    )
    .withColumn("acctbal", col("acctbal").cast(DoubleType()))
)

supplier_dim = (
    supplier.selectExpr(
        "s_suppkey as suppkey",
        "s_name as name",
        "s_address as address",
        "s_phone as phone",
        "s_nationkey as nationkey",
        "s_acctbal as acctbal"
    )
    .withColumn("acctbal", col("acctbal").cast(DoubleType()))
)

part_dim = (
    part.selectExpr(
        "p_partkey as partkey",
        "p_name as name",
        "p_mfgr as mfgr",
        "p_brand as brand",
        "p_type as type",
        "p_size as size",
        "p_container as container",
        "p_retailprice as retailprice"
    )
    .withColumn("retailprice", col("retailprice").cast(DoubleType()))
)

order_dim = orders.selectExpr(
    "o_orderkey as orderkey",
    "o_orderstatus as orderstatus",
    "o_totalprice as totalprice",
    "o_orderdate as orderdate",
    "o_orderpriority as priority",
    "o_custkey as custkey"
).withColumn("totalprice", col("totalprice").cast(DoubleType()))\
 .withColumn("orderdate", to_date(col("orderdate"), "yyyy-MM-dd"))

geo_dim = (
    nation.join(region, nation.n_regionkey == region.r_regionkey)
    .selectExpr(
        "r_regionkey as regionkey",
        "r_name as regionname",
        "n_nationkey as nationkey",
        "n_name as nationname"
    )
)

time_dim = (
    orders.select("o_orderdate")
    .distinct()
    .withColumn("o_orderdate", to_date(col("o_orderdate"), "yyyy-MM-dd"))
    .withColumnRenamed("o_orderdate", "datekey")
    .withColumn("year", year("datekey"))
    .withColumn("month", month("datekey"))
    .withColumn("day", dayofmonth("datekey"))
)
time_dim = time_dim.withColumn("quarter", ((time_dim.month-1)/3 + 1).cast("int"))

# Write dimensions to Iceberg
customer_dim.writeTo("datawarehouse.dim_customer").append()
supplier_dim.writeTo("datawarehouse.dim_supplier").append()
part_dim.writeTo("datawarehouse.dim_part").append()
order_dim.writeTo("datawarehouse.dim_order").append()
geo_dim.writeTo("datawarehouse.dim_geography").append()
time_dim.writeTo("datawarehouse.dim_time").append()

# ---- FACT ---- #
fact_sales = (
    lineitem.join(orders, lineitem.l_orderkey == orders.o_orderkey, "inner")
    .selectExpr(
        "l_orderkey as orderkey",
        "l_partkey as partkey",
        "l_suppkey as suppkey",
        "o_custkey as custkey",
        "l_extendedprice as extendedprice",
        "l_discount as discount",
        "l_tax as tax",
        "l_quantity as quantity",
        "o_orderdate as orderdate"
    )
    .withColumn("orderdate", to_date(col("orderdate"), "yyyy-MM-dd"))
    .withColumn("extendedprice", col("extendedprice").cast(DoubleType()))
    .withColumn("discount", col("discount").cast(DoubleType()))
    .withColumn("tax", col("tax").cast(DoubleType()))
    .withColumn("quantity", col("quantity").cast(DoubleType()))
    .withColumn("year", year(col("orderdate")))
    .withColumn("month", month(col("orderdate")))
    .withColumn("day", dayofmonth(col("orderdate")))
    .repartition("year", "month", "day")
)

# fact_sales.writeTo("datawarehouse.fact_sales").using("iceberg").partitionedBy("year", "month", "day").createOrReplace()
fact_sales.writeTo("datawarehouse.fact_sales").append()

spark.stop()
