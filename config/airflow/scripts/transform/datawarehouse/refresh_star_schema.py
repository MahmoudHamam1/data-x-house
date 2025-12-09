from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, dayofmonth, to_date
from pyspark.sql.types import DoubleType

# Initialize Spark + Iceberg
spark = (
    SparkSession.builder
    .appName("Incremental_Orders_Merge_And_Fact_Refresh")
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog")
    .config("spark.sql.catalog.spark_catalog.type", "hive")
    .config("spark.sql.catalog.spark_catalog.uri", "thrift://dx-master:9083")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .enableHiveSupport()
    .getOrCreate()
)

# Load raw tables
orders_raw = spark.table("raw.orders")
lineitem = spark.table("raw.lineitem")

# -----------------------------
# MERGE INTO dim_order (incremental)
# -----------------------------
orders_raw_clean = (
    orders_raw.selectExpr(
        "o_orderkey as orderkey",
        "o_orderstatus as orderstatus",
        "o_totalprice as totalprice",
        "o_orderdate as orderdate",
        "o_orderpriority as priority",
        "o_custkey as custkey"
    )
    .withColumn("totalprice", col("totalprice").cast(DoubleType()))
    .withColumn("orderdate", to_date(col("orderdate"), "yyyy-MM-dd"))
    .distinct()
)

orders_raw_clean.createOrReplaceTempView("staging_orders")
print("✅  Temp Orders View updated successfully !!!")

# spark.sql("""
# MERGE INTO datawarehouse.dim_order AS target
# USING staging_orders AS source
# ON target.orderkey = source.orderkey
# WHEN MATCHED THEN UPDATE SET *
# WHEN NOT MATCHED THEN INSERT *
# """)

print("✅  Orders tables updated successfully !!!")
# -----------------------------
# FULL REFRESH fact_sales
# -----------------------------

fact_sales_clean = (
    lineitem.join(orders_raw_clean, lineitem.l_orderkey == orders_raw_clean.orderkey, "inner")
    .selectExpr(
        "l_orderkey AS orderkey",
        "l_partkey AS partkey",
        "l_suppkey AS suppkey",
        "custkey",
        "l_extendedprice AS extendedprice",
        "l_discount AS discount",
        "l_tax AS tax",
        "l_quantity AS quantity",
        "orderdate"
    )
    .withColumn("extendedprice", col("extendedprice").cast(DoubleType()))
    .withColumn("discount", col("discount").cast(DoubleType()))
    .withColumn("tax", col("tax").cast(DoubleType()))
    .withColumn("quantity", col("quantity").cast(DoubleType()))
    .withColumn("year", year(col("orderdate")))
    .withColumn("month", month(col("orderdate")))
    .withColumn("day", dayofmonth(col("orderdate")))
    .repartition("year", "month", "day")
    .distinct()
)

fact_sales_clean.createOrReplaceTempView("staging_sales")

print("✅  Temp Sales View updated successfully !!!")

spark.sql("""
MERGE INTO datawarehouse.fact_sales AS target
USING staging_sales AS source
ON target.orderkey = source.orderkey and target.partkey = source.partkey  and target.suppkey = source.suppkey and target.custkey = source.custkey and target.orderdate = source.orderdate 
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

print("✅  Sales table updated successfully !!!")

spark.stop()
