#!/bin/bash

# ===============================
# CONFIGURATION
# ===============================
SRC_DB_NAME="tpch"
TGT_DB_NAME="raw"
TABLE_NAME="orders"
TARGET_DIR="/storage/tpch/${TABLE_NAME}/$(date +"year=%Y/month=%m/day=%d/hour=%H")"

# ===============================
# SQOOP IMPORT
# ===============================
echo ">>> Starting Sqoop import for table: ${TABLE_NAME}"

sqoop import \
    --connect jdbc:mysql://dx-database:3306/${SRC_DB_NAME} \
    --driver com.mysql.cj.jdbc.Driver \
    --username hive \
    --password <HIVE_PASSWORD> \
    --table ${TABLE_NAME} \
    --target-dir ${TARGET_DIR} \
    --delete-target-dir \
    --where "ORDERDATE >= '1992-01-01' and ORDERDATE < '1994-01-01'" \
    --fields-terminated-by ',' \
    --lines-terminated-by '\n' \
    --as-textfile \
    --compress \
    --compression-codec org.apache.hadoop.io.compress.SnappyCodec \
    --split-by ORDERDATE

echo ">>> Sqoop import completed successfully."

# ===============================
# HIVE TABLE CREATION
# ===============================
echo ">>> Ensuring Hive table exists..."

hive -e "CREATE DATABASE IF NOT EXISTS ${TGT_DB_NAME}"

hive -e "
CREATE EXTERNAL TABLE IF NOT EXISTS ${TGT_DB_NAME}.${TABLE_NAME} (
  o_orderkey INT,
  o_custkey INT,
  o_orderstatus STRING,
  o_totalprice STRING,
  o_orderdate STRING,
  o_orderpriority STRING,
  o_clerk STRING,
  o_shippriority INT,
  o_comment STRING
)
PARTITIONED BY (year STRING, month STRING, day STRING, hour STRING)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/storage/tpch/${TABLE_NAME}';
"

# ===============================
# REFRESH HIVE PARTITIONS
# ===============================
echo ">>> Repairing Hive partitions..."
hive -e "MSCK REPAIR TABLE ${TGT_DB_NAME}.${TABLE_NAME};"

echo ">>> Batch ingestion for ${TABLE_NAME} completed successfully!"