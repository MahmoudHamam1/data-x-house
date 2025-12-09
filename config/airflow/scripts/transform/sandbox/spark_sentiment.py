#!/usr/bin/env python3
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType, FloatType

# naive sentiment using keywords; if VADER is installed, can switch

def sentiment_score(text):
    if text is None:
        return 0.0
    t = text.lower()
    pos_words = ['love','excellent','recommend','exceeded','good','great','fast']
    neg_words = ['terrible','not worth','disappointed','poor','bad','stopped']
    score = 0
    for w in pos_words:
        if w in t:
            score += 1
    for w in neg_words:
        if w in t:
            score -= 1
    return float(score)


def sentiment_label(score):
    if score > 0:
        return 'Positive'
    elif score < 0:
        return 'Negative'
    else:
        return 'Neutral'

parser = argparse.ArgumentParser()
parser.add_argument('--comments_dir', required=True)
parser.add_argument('--dw_db', required=True)
parser.add_argument('--sandbox_db', required=True)
parser.add_argument('--iceberg_warehouse', required=True)
args = parser.parse_args()

spark = SparkSession.builder \
    .appName('sandbox_sentiment') \
    .config('spark.sql.catalog.dxhouse', 'org.apache.iceberg.spark.SparkCatalog') \
    .config('spark.sql.catalog.dxhouse.type', 'hadoop') \
    .config('spark.sql.catalog.dxhouse.warehouse', args.iceberg_warehouse) \
    .config('spark.sql.extensions', 'org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions') \
    .enableHiveSupport() \
    .getOrCreate()

# Read comments CSVs
comments = spark.read.option('header','true').option('escape','"').csv(args.comments_dir)

# UDFs
sent_score_udf = udf(sentiment_score, FloatType())
sent_label_udf = udf(sentiment_label, StringType())

comments = comments.withColumn('sentiment_score', sent_score_udf(col('comment_text'))).withColumn('sentiment', sent_label_udf(col('sentiment_score')))

# Join with dimensions to map product/customer id -> keys in dims
# Our dims use padded keys (e.g., P000001), so match on product_id -> part_key
# Read dims from dxhouse.datawarehouse_
CAT = 'dxhouse'
DW = args.dw_db

# Try to join by IDs; if product ids are different formats adjust mapping
try:
    dim_customer = spark.table(f"{CAT}.{DW}_dim_customer")
    dim_part = spark.table(f"{CAT}.{DW}_dim_part")
    # join
    enriched = comments.join(dim_customer, comments.customer_id == dim_customer.customer_key, 'left').join(dim_part, comments.product_id == dim_part.part_key, 'left')
except Exception as e:
    # if schema mismatch, just keep comments and write as-is with sentiment
    enriched = comments

# write to Iceberg in sandbox DB
enriched.writeTo(f"{CAT}.{args.sandbox_db}_sentiment_analysis_results").using('iceberg').createOrReplace()

spark.stop()
