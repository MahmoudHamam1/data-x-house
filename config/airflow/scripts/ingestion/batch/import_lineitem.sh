#!/bin/bash

# ===============================
# CONFIGURATION
# ===============================
SRC_DB_NAME="tpch"
TGT_DB_NAME="raw"
TABLE_NAME="lineitem"
TARGET_DIR="/storage/tpch/${TABLE_NAME}/$(date +"year=%Y/month=%m/day=%d/hour=%H")"

# ===============================
# SQOOP IMPORT
# ===============================
echo ">>> Starting Sqoop import for table: ${TABLE_NAME}"

sqoop import \
    --connect jdbc:mysql://dx-database:3306/${SRC_DB_NAME} \
    --driver com.mysql.cj.jdbc.Driver \
    --username hive \
    --password ${HIVE_DB_PASSWORD} \
    --table ${TABLE_NAME} \
    --target-dir ${TARGET_DIR} \
    --delete-target-dir \
    --where "SHIPDATE >= '1992-01-01' and SHIPDATE < '1992-06-01'" \
    --fields-terminated-by ',' \
    --lines-terminated-by '\n' \
    --as-textfile \
    --compress \
    --compression-codec org.apache.hadoop.io.compress.SnappyCodec \
    --split-by SHIPDATE

echo ">>> Sqoop import completed successfully."

# ===============================
# HIVE TABLE CREATION
# ===============================
echo ">>> Ensuring Hive table exists..."

hive -e "CREATE DATABASE IF NOT EXISTS ${TGT_DB_NAME}"

hive -e "
CREATE EXTERNAL TABLE IF NOT EXISTS ${TGT_DB_NAME}.${TABLE_NAME} (
  l_orderkey INT,
  l_partkey INT,
  l_suppkey INT,
  l_linenumber INT,
  l_quantity DOUBLE,
  l_extendedprice DOUBLE,
  l_discount DOUBLE,
  l_tax DOUBLE,
  l_returnflag STRING,
  l_linestatus STRING,
  l_shipdate STRING,
  l_commitdate STRING,
  l_receiptdate STRING,
  l_shipinstruct STRING,
  l_shipmode STRING,
  l_comment STRING
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