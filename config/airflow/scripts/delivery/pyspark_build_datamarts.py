#!/usr/bin/env python3
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, avg, count, expr, year, month, dayofmonth

parser = argparse.ArgumentParser()
parser.add_argument('--dw_db', required=True)
parser.add_argument('--mart_db', required=True)
parser.add_argument('--iceberg_warehouse', required=True)
args = parser.parse_args()

spark = SparkSession.builder \
    .appName('build_datamarts') \
    .config('spark.sql.catalog.dxhouse', 'org.apache.iceberg.spark.SparkCatalog') \
    .config('spark.sql.catalog.dxhouse.type', 'hadoop') \
    .config('spark.sql.catalog.dxhouse.warehouse', args.iceberg_warehouse) \
    .config('spark.sql.extensions', 'org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions') \
    .enableHiveSupport() \
    .getOrCreate()

CAT = 'dxhouse'
DW = args.dw_db
MART = args.mart_db

fact = spark.table(f"{CAT}.{DW}_fact_sales")
dim_customer = spark.table(f"{CAT}.{DW}_dim_customer")
dim_part = spark.table(f"{CAT}.{DW}_dim_part")
dim_supplier = spark.table(f"{CAT}.{DW}_dim_supplier")
dim_order = spark.table(f"{CAT}.{DW}_dim_order")

def write_mart(df, name, partition_cols=None):
    if partition_cols:
        df.writeTo(f"{CAT}.{MART}_{name}").using('iceberg').partitionedBy(*partition_cols).createOrReplace()
    else:
        df.writeTo(f"{CAT}.{MART}_{name}").using('iceberg').createOrReplace()

# 1. dm_revenue_by_customer_region: revenue per customer and region and time
sales_enriched = fact.join(dim_customer, 'customer_key', 'left').join(dim_part, 'part_key', 'left')

rev = sales_enriched.withColumn('net_revenue', expr('extended_price * (1 - discount)'))

rev_by_customer = rev.groupBy('customer_key').agg(_sum('net_revenue').alias('total_revenue'), _sum('quantity').alias('total_units'))
write_mart(rev_by_customer, 'revenue_by_customer', partition_cols=['customer_key'])

# 2. dm_supplier_performance: supplier volume, revenue
supp = fact.join(dim_supplier, 'supplier_key', 'left').withColumn('net_revenue', expr('extended_price * (1 - discount)'))
supp_perf = supp.groupBy('supplier_key').agg(_sum('net_revenue').alias('total_revenue'), _sum('quantity').alias('total_units'), count('*').alias('transactions'))
write_mart(supp_perf, 'supplier_performance', partition_cols=['supplier_key'])

# 3. dm_inventory_summary (by part)
inv = fact.join(dim_part, 'part_key', 'left').groupBy('part_key').agg(_sum('quantity').alias('units_ordered'), _sum(expr('extended_price*(1-discount)')).alias('revenue'))
write_mart(inv, 'inventory_summary', partition_cols=['part_key'])

# 4. dm_order_fulfillment: order to ship/receipt times (requires commit/receipt dates)
from pyspark.sql.functions import datediff
fulfillment = fact.select('order_key','customer_key','part_key','supplier_key','ship_date','commit_date','receipt_date')
fulfill_metrics = fulfillment.withColumn('ship_delay_days', datediff(col('ship_date'), col('commit_date'))).withColumn('fulfillment_days', datediff(col('receipt_date'), col('ship_date')))
fulfill_agg = fulfill_metrics.groupBy('supplier_key').agg(avg('ship_delay_days').alias('avg_ship_delay'), avg('fulfillment_days').alias('avg_fulfillment_days'), count('*').alias('orders'))
write_mart(fulfill_agg, 'order_fulfillment', partition_cols=['supplier_key'])

spark.stop()

