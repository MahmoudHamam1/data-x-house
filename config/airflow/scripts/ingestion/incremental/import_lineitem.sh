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
    --password <HIVE_PASSWORD> \
    --table ${TABLE_NAME} \
    --target-dir ${TARGET_DIR} \
    --delete-target-dir \
    --where "SHIPDATE >= '1992-10-01' and SHIPDATE < '1993-01-01'" \
    --fields-terminated-by ',' \
    --lines-terminated-by '\n' \
    --as-textfile \
    --compress \
    --compression-codec org.apache.hadoop.io.compress.SnappyCodec \
    --split-by SHIPDATE

echo ">>> Sqoop import completed successfully."


# ===============================
# REFRESH HIVE PARTITIONS
# ===============================
echo ">>> Repairing Hive partitions..."
hive -e "MSCK REPAIR TABLE ${TGT_DB_NAME}.${TABLE_NAME};"

echo ">>> Batch ingestion for ${TABLE_NAME} completed successfully!"