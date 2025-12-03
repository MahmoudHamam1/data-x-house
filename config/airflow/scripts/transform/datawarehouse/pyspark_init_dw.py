#!/usr/bin/env python3
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, dayofmonth, to_date

parser = argparse.ArgumentParser()
parser.add_argument('--raw_db', required=True)
parser.add_argument('--dw_db', required=True)
args = parser.parse_args()

# Spark session with Iceberg Hadoop catalog named 'dxhouse'
spark = SparkSession.builder \
    .appName('init_star_schema_dw') \
    .enableHiveSupport() \
    .getOrCreate()

RAW = args.raw_db
DW = args.dw_db
CAT = 'dxhouse'

# Read raw Hive tables
customer = spark.table(f"{RAW}.customer")
orders = spark.table(f"{RAW}.orders")
lineitem = spark.table(f"{RAW}.lineitem")
part = spark.table(f"{RAW}.part")
partsupp = spark.table(f"{RAW}.partsupp")
supplier = spark.table(f"{RAW}.supplier")
nation = spark.table(f"{RAW}.nation")
region = spark.table(f"{RAW}.region")

# -------- DIMENSIONS --------
# dim_customer
dim_customer = customer.select(
    col('c_custkey').alias('customer_key'),
    col('c_name').alias('customer_name'),
    col('c_address').alias('address'),
    col('c_phone').alias('phone'),
    col('c_acctbal').alias('acctbal'),
    col('c_mktsegment').alias('mktsegment'),
    col('c_nationkey').alias('nation_key')
)

dim_customer.writeTo(f"{CAT}.{DW}_dim_customer").using('iceberg').createOrReplace()

# dim_supplier
dim_supplier = supplier.select(
    col('s_suppkey').alias('supplier_key'),
    col('s_name').alias('supplier_name'),
    col('s_address').alias('address'),
    col('s_phone').alias('phone'),
    col('s_acctbal').alias('acctbal'),
    col('s_nationkey').alias('nation_key')
)

dim_supplier.writeTo(f"{CAT}.{DW}_dim_supplier").using('iceberg').createOrReplace()

# dim_part
dim_part = part.select(
    col('p_partkey').alias('part_key'),
    col('p_name').alias('part_name'),
    col('p_mfgr').alias('mfgr'),
    col('p_brand').alias('brand'),
    col('p_type').alias('type'),
    col('p_size').alias('size'),
    col('p_container').alias('container'),
    col('p_retailprice').alias('retail_price')
)

dim_part.writeTo(f"{CAT}.{DW}_dim_part").using('iceberg').createOrReplace()

# dim_geography (nation + region)
region_df = region.select(col('r_regionkey').alias('region_key'), col('r_name').alias('region_name'))

nation_df = nation.select(col('n_nationkey').alias('nation_key'), col('n_name').alias('nation_name'), col('n_regionkey').alias('region_key'))

dim_geography = nation_df.join(region_df, 'region_key', 'left')

dim_geography.writeTo(f"{CAT}.{DW}_dim_geography").using('iceberg').createOrReplace()

# dim_order
# Convert o_orderdate to date
orders_clean = orders.withColumn('order_date', to_date(col('o_orderdate')))

dim_order = orders_clean.select(
    col('o_orderkey').alias('order_key'),
    col('o_orderstatus').alias('order_status'),
    col('o_totalprice').alias('total_price'),
    col('order_date'),
    col('o_orderpriority').alias('order_priority'),
    col('o_custkey').alias('customer_key')
)

dim_order.writeTo(f"{CAT}.{DW}_dim_order").using('iceberg').createOrReplace()

# dim_time - from order_date (orders)
time_df = orders_clean.select(col('o_orderdate').alias('order_date')).dropna()
from pyspark.sql.functions import year, month, dayofmonth, weekofyear, date_format

time_dim = time_df.select(
    to_date(col('order_date')).alias('date')
).dropDuplicates().withColumn('year', year(col('date'))).withColumn('month', month(col('date'))).withColumn('day', dayofmonth(col('date'))).withColumn('quarter', date_format(col('date'), 'Q')).withColumn('week', weekofyear(col('date')))

time_dim.writeTo(f"{CAT}.{DW}_dim_time").using('iceberg').createOrReplace()

# -------- FACT (fact_sales) --------
# join lineitem -> orders to get order date and custkey, partkey, suppkey
lineitem_clean = lineitem.withColumn('l_shipdate', to_date(col('l_shipdate'))).withColumn('l_commitdate', to_date(col('l_commitdate'))).withColumn('l_receiptdate', to_date(col('l_receiptdate')))

fact = lineitem_clean.join(orders_clean, lineitem_clean.l_orderkey == orders_clean.o_orderkey, 'left') \
    .select(
        col('l_orderkey').alias('order_key'),
        col('l_partkey').alias('part_key'),
        col('l_suppkey').alias('supplier_key'),
        col('o_custkey').alias('customer_key'),
        col('l_extendedprice').alias('extended_price'),
        col('l_discount').alias('discount'),
        col('l_tax').alias('tax'),
        col('l_quantity').alias('quantity'),
        col('l_shipdate').alias('ship_date'),
        col('l_commitdate').alias('commit_date'),
        col('l_receiptdate').alias('receipt_date')
    )

# add partition columns
fact = fact.withColumn('order_year', year(col('ship_date'))).withColumn('order_month', month(col('ship_date'))).withColumn('order_day', dayofmonth(col('ship_date')))

# write partitioned by year/month/day
fact.writeTo(f"{CAT}.{DW}_fact_sales").using('iceberg').partitionedBy('order_year','order_month','order_day').createOrReplace()

spark.stop()
