#!/usr/bin/env python3
# /dxhouse/airflow/scripts/sentiment_analysis_spark.py
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, lower, lit, when
from pyspark.sql.types import StringType, DoubleType

parser = argparse.ArgumentParser()
parser.add_argument("--raw_db", required=True)
parser.add_argument("--raw_table", required=True)
parser.add_argument("--dim_db", required=True)
parser.add_argument("--dim_table", required=True)
parser.add_argument("--sandbox_db", required=True)
parser.add_argument("--sandbox_table", required=True)
args = parser.parse_args()

spark = SparkSession.builder \
    .appName("spark_sentiment_analysis") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
    .config("spark.sql.catalog.spark_catalog.type", "hive") \
    .config("spark.sql.catalog.spark_catalog.uri", "thrift://dx-master:9083") \
    .enableHiveSupport() \
    .getOrCreate()

# -----------------------------
# Load Data
# -----------------------------
comments_df = spark.table(f"{args.raw_db}.{args.raw_table}")
customers_df = spark.table(f"{args.dim_db}.{args.dim_table}")

# -----------------------------
# Rule-based Sentiment Scoring (can later be replaced by ML UDF)
# -----------------------------
positive_words = ["love", "excellent", "recommend", "great", "good", "satisfied", "fast", "happy", "best"]
negative_words = ["terrible", "bad", "not worth", "disappointed", "poor", "worse", "unusable", "return"]

def get_sentiment(text):
    if not text:
        return ("neutral", 0.0)
    txt = text.lower()
    score = 0
    for w in positive_words:
        if w in txt: score += 1
    for w in negative_words:
        if w in txt: score -= 1
    if score > 0:
        return ("positive", float(score))
    elif score < 0:
        return ("negative", float(score))
    else:
        return ("neutral", 0.0)

sentiment_udf = udf(lambda t: get_sentiment(t)[0], StringType())
score_udf = udf(lambda t: get_sentiment(t)[1], DoubleType())

scored_df = (
    comments_df
    .withColumn("predicted_label", sentiment_udf(col("comment")))
    .withColumn("score", score_udf(col("comment")))
)

# -----------------------------
# Join with Customer Dimension
# -----------------------------
joined_df = (
    scored_df.join(customers_df, scored_df.custkey == customers_df.custkey, "left")
    .select(
        scored_df.custkey,
        customers_df.name.alias("customer_name"),
        customers_df.nationkey,
        scored_df.comment,
        scored_df.predicted_label,
        scored_df.score
    )
)

# -----------------------------
# Write to Sandbox Table
# -----------------------------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {args.sandbox_db}.{args.sandbox_table} (
    custkey STRING,
    customer_name STRING,
    nationkey BIGINT,
    comment STRING,
    predicted_label STRING,
    score DOUBLE
)
USING iceberg
""")

joined_df.writeTo(f"{args.sandbox_db}.{args.sandbox_table}").append()

print(f"✅ Saved {joined_df.count()} enriched sentiment records to {args.sandbox_db}.{args.sandbox_table}")
