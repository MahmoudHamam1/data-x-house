from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum, countDistinct

spark = (
    SparkSession.builder
    .appName("CreateDataMarts")
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog")
    .config("spark.sql.catalog.spark_catalog.type", "hive")
    .config("spark.sql.catalog.spark_catalog.uri", "thrift://dx-master:9083")
    .enableHiveSupport()
    .getOrCreate()
)

fact = spark.table("datawarehouse.fact_sales")
cust = spark.table("datawarehouse.dim_customer")
geo = spark.table("datawarehouse.dim_geography")

# ---- Sales by Customer ---- #
sales_by_customer = (
    fact.join(cust, "custkey")
    .groupBy("custkey", "name")
    .agg(
        _sum(fact.extendedprice * (1 - fact.discount)).alias("total_revenue"),
        countDistinct("orderkey").alias("total_orders")
    )
)

sales_by_customer.writeTo("delivery.sales_by_customer").using("iceberg").createOrReplace()

# ---- Sales by Region ---- #
sales_by_region = (
    fact.join(cust, "custkey")
        .join(geo, cust.nationkey == geo.nationkey)
        .groupBy("regionname")
        .agg(
            _sum(fact.extendedprice * (1 - fact.discount)).alias("total_revenue"),
            countDistinct("orderkey").alias("total_orders")
        )
)

sales_by_region.writeTo("delivery.sales_by_region").using("iceberg").createOrReplace()

# ---- Sales Summery ---- #
sales_summary = (
    fact.groupBy("year", "month")
    .agg(
        {"extendedprice": "sum", "discount": "avg", "tax": "avg", "quantity": "sum"}
    )
    .withColumnRenamed("sum(extendedprice)", "total_revenue")
    .withColumnRenamed("avg(discount)", "avg_discount")
    .withColumnRenamed("avg(tax)", "avg_tax")
    .withColumnRenamed("sum(quantity)", "total_quantity")
)

sales_summary.writeTo("delivery.sales_summary").using("iceberg").createOrReplace()

spark.stop()
