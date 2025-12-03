#!/bin/bash
# Script to set up Airflow connections for the DXhouse cluster

pip install -r /opt/airflow/scripts/bin/requirements.txt

# Verify the version
python -c "import pyspark; print(f'PySpark version: {pyspark.__version__}')"

airflow providers list
airflow plugins

echo "Setting up Airflow connections..."

# MySQL connection
airflow connections add 'mysql' \
    --conn-type 'mysql' \
    --conn-host 'dx-database' \
    --conn-login 'hive' \
    --conn-password <HIVE_PASSWORD> \
    --conn-schema 'metastore' \
    --conn-port 3306

# Hadoop HTTP connection
airflow connections add 'hadoop_http' \
    --conn-type 'http' \
    --conn-host 'dx-master' \
    --conn-port 8020

# Hadoop SSH connection
airflow connections add 'hadoop_ssh' \
    --conn-type 'ssh' \
    --conn-host 'dx-master' \
    --conn-login 'hadoop' \
    --conn-password <HADOOP_PASSWORD> \
    --conn-port 22

# Spark connection (for SparkSubmitOperator if needed)
airflow connections add 'spark' \
    --conn-type 'spark' \
    --conn-host 'spark://dx-master' \
    --conn-port 7077

# Hive connection
airflow connections add 'hive' \
    --conn-type 'hiveserver2' \
    --conn-host 'dx-master' \
    --conn-port 10000 \
    --conn-extra '{"use_beeline": true, "auth": ""}'

# HDFS connection
airflow connections add 'hdfs' \
    --conn-type 'hdfs' \
    --conn-host 'dx-master' \
    --conn-port 8020

echo "Airflow connections setup complete!"

# List all connections to verify
echo "Current connections:"
airflow connections list