# DX House Troubleshooting Guide

Common issues and solutions for DX House implementation.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Service Startup Problems](#service-startup-problems)
3. [Data Ingestion Issues](#data-ingestion-issues)
4. [Query Performance Problems](#query-performance-problems)
5. [Storage Issues](#storage-issues)
6. [Security & Access Issues](#security--access-issues)
7. [Airflow DAG Failures](#airflow-dag-failures)

---

## Installation Issues

### Docker Container Won't Start

**Symptoms**: Container exits immediately after starting

**Solutions**:
```bash
# Check container logs
docker logs dx-master

# Check available resources
docker stats

# Verify network connectivity
docker network ls
docker network inspect bridge

# Restart with more resources
docker run -d --name dx-master --memory="12g" --cpus="5" dxhouse-cls:latest
```

### Port Conflicts

**Symptoms**: "Port already in use" error

**Solutions**:
```bash
# Check which process is using the port
netstat -tulpn | grep 8080

# Kill the process or use different port
docker run -d -p 8081:8080 dxhouse-cls:latest
```

---

## Service Startup Problems

### HDFS NameNode Not Starting

**Symptoms**: `hdfs dfsadmin -report` fails

**Solutions**:
```bash
# Check NameNode logs
tail -f /opt/hadoop/logs/hadoop-*-namenode-*.log

# Format NameNode (CAUTION: Deletes all data)
hdfs namenode -format

# Check disk space
df -h

# Verify configuration
hdfs getconf -confKey dfs.namenode.name.dir
```

### Hive Metastore Connection Failed

**Symptoms**: "Could not connect to meta store" error

**Solutions**:
```bash
# Check if Metastore is running
netstat -tulpn | grep 9083

# Start Metastore manually
hive --service metastore &

# Verify MySQL connection
mysql -h dx-database -u hive -p

# Check hive-site.xml configuration
grep -A 2 "javax.jdo.option.ConnectionURL" /opt/hive/conf/hive-site.xml
```

### Spark Not Connecting to Hive

**Symptoms**: "Table not found" in Spark jobs

**Solutions**:
```bash
# Verify Spark can access Hive Metastore
spark-sql -e "SHOW DATABASES;"

# Check spark-defaults.conf
grep metastore /opt/spark/conf/spark-defaults.conf

# Copy hive-site.xml to Spark conf
cp /opt/hive/conf/hive-site.xml /opt/spark/conf/

# Restart Spark
stop-all.sh && start-all.sh
```

---

## Data Ingestion Issues

### Sqoop Import Fails

**Symptoms**: Sqoop job fails with connection error

**Solutions**:
```bash
# Test MySQL connectivity
mysql -h dx-database -u hive -p tpch

# Verify JDBC driver
ls /opt/sqoop/lib/mysql-connector-j-8.0.33.jar

# Check Sqoop version
sqoop version

# Run with verbose logging
sqoop import --verbose \
    --connect jdbc:mysql://dx-database:3306/tpch \
    --username hive \
    --password hivepass \
    --table orders
```

### Low Ingestion Throughput

**Symptoms**: Sqoop import is very slow

**Solutions**:
```bash
# Increase number of mappers
sqoop import --num-mappers 8 ...

# Use direct mode (MySQL specific)
sqoop import --direct ...

# Increase fetch size
sqoop import --fetch-size 10000 ...

# Check network bandwidth
iperf3 -c dx-database
```

### Partition Repair Fails

**Symptoms**: `MSCK REPAIR TABLE` doesn't add partitions

**Solutions**:
```bash
# Check HDFS directory structure
hdfs dfs -ls /storage/tpch/orders/

# Manually add partitions
hive -e "ALTER TABLE raw.orders ADD PARTITION (year='2024', month='12', day='03', hour='10');"

# Verify partition format matches table definition
hive -e "SHOW CREATE TABLE raw.orders;"
```

---

## Query Performance Problems

### Slow Hive Queries

**Symptoms**: Queries take too long to execute

**Solutions**:
```bash
# Use Tez instead of MapReduce
hive -e "SET hive.execution.engine=tez;"

# Enable vectorization
hive -e "SET hive.vectorized.execution.enabled=true;"

# Increase memory
hive -e "SET hive.tez.container.size=4096;"

# Check query plan
hive -e "EXPLAIN SELECT * FROM orders WHERE o_orderstatus='F';"
```

### Trino Query Timeout

**Symptoms**: "Query exceeded maximum time" error

**Solutions**:
```bash
# Increase query timeout in config.properties
echo "query.max-execution-time=30m" >> /opt/trino/etc/config.properties

# Restart Trino
systemctl restart trino

# Check Trino worker status
trino-cli --execute "SELECT * FROM system.runtime.nodes;"
```

### Out of Memory Errors

**Symptoms**: "Java heap space" or "GC overhead limit exceeded"

**Solutions**:
```bash
# Increase Spark executor memory
spark-submit --executor-memory 4g --driver-memory 4g ...

# Increase Hive container size
hive -e "SET hive.tez.container.size=4096;"

# Reduce data processed per task
hive -e "SET hive.exec.reducers.bytes.per.reducer=256000000;"

# Enable dynamic partition pruning
hive -e "SET hive.optimize.ppd=true;"
```

---

## Storage Issues

### HDFS Out of Space

**Symptoms**: "No space left on device" error

**Solutions**:
```bash
# Check HDFS usage
hdfs dfsadmin -report

# Find large directories
hdfs dfs -du -h / | sort -h | tail -20

# Delete old data
hdfs dfs -rm -r /storage/tpch/*/year=2023

# Reduce replication factor
hdfs dfs -setrep -w 2 /storage/tpch

# Clean up trash
hdfs dfs -expunge
```

### Iceberg Table Corruption

**Symptoms**: "Table metadata not found" error

**Solutions**:
```bash
# Check Iceberg metadata
hdfs dfs -ls /user/hive/warehouse/datawarehouse.db/fact_sales/metadata/

# Rollback to previous snapshot
spark-sql -e "CALL local.system.rollback_to_snapshot('datawarehouse.fact_sales', <snapshot_id>);"

# List available snapshots
spark-sql -e "SELECT * FROM datawarehouse.fact_sales.snapshots;"

# Expire old snapshots
spark-sql -e "CALL local.system.expire_snapshots('datawarehouse.fact_sales', TIMESTAMP '2025-01-01 00:00:00');"
```

### Slow HDFS Read/Write

**Symptoms**: Data operations are very slow

**Solutions**:
```bash
# Check DataNode health
hdfs dfsadmin -report

# Check network latency
hdfs dfsadmin -printTopology

# Increase block size for large files
hdfs dfs -D dfs.block.size=268435456 -put large_file.csv /storage/

# Balance HDFS blocks
hdfs balancer -threshold 10
```

---

## Security & Access Issues

### Ranger Policy Not Working

**Symptoms**: User can't access data despite policy

**Solutions**:
```bash
# Check Ranger audit logs
tail -f /opt/ranger/logs/ranger-admin-*.log

# Verify policy is enabled
# Navigate to Ranger UI → Policies → Check status

# Force policy refresh
# Ranger UI → Service Manager → Refresh

# Check user group membership
# Ranger UI → Settings → Users/Groups

# Verify service is registered with Ranger
curl http://dx-worker3:6080/service/public/v2/api/service
```

### KMS Encryption Zone Issues

**Symptoms**: Can't write to encrypted directory

**Solutions**:
```bash
# Check KMS status
hadoop key list

# Verify encryption zone
hdfs crypto -listZones

# Check key permissions
hadoop key list -metadata

# Create new encryption key if needed
hadoop key create key_storage_zone

# Recreate encryption zone
hdfs crypto -createZone -keyName key_storage_zone -path /storage/tpch
```

### Authentication Failures

**Symptoms**: "Permission denied" errors

**Solutions**:
```bash
# Check user permissions
hdfs dfs -ls -R /storage/tpch | grep username

# Grant permissions
hdfs dfs -chmod -R 755 /storage/tpch
hdfs dfs -chown -R hive:hadoop /storage/tpch

# Verify Ranger policies
# Check Ranger UI for applicable policies

# Check Hive authorization
hive -e "SHOW GRANT USER username ON DATABASE raw;"
```

---

## Airflow DAG Failures

### DAG Import Errors

**Symptoms**: DAG doesn't appear in Airflow UI

**Solutions**:
```bash
# Check DAG file syntax
python /opt/airflow/dags/batch_ingestion_dag.py

# Check Airflow logs
tail -f /opt/airflow/logs/scheduler/latest/*.log

# Verify DAG directory permissions
ls -la /opt/airflow/dags/

# Restart Airflow scheduler
airflow scheduler restart
```

### Task Timeout

**Symptoms**: Tasks fail with timeout error

**Solutions**:
```python
# Increase task timeout in DAG definition
task = SSHOperator(
    task_id='import_lineitem',
    cmd_timeout=3600,  # 1 hour
    ...
)

# Or set globally in airflow.cfg
[core]
dagrun_timeout = 3600
```

### SSH Connection Failed

**Symptoms**: SSHOperator can't connect to dx-master

**Solutions**:
```bash
# Test SSH connectivity
ssh hadoop@dx-master

# Check SSH connection in Airflow
airflow connections get hadoop_ssh

# Update connection if needed
airflow connections add hadoop_ssh \
    --conn-type ssh \
    --conn-host dx-master \
    --conn-login hadoop \
    --conn-port 22

# Verify SSH keys
ls -la ~/.ssh/
```

### Spark Submit Fails

**Symptoms**: SparkSubmitOperator fails

**Solutions**:
```bash
# Check Spark connection
airflow connections get spark

# Test Spark submit manually
spark-submit --master spark://dx-master:7077 \
    /opt/airflow/scripts/transform/datawarehouse/create_star_schema.py

# Check Spark master logs
tail -f /opt/spark/logs/spark-*-master-*.out

# Verify JAR files exist
ls -la /opt/airflow/scripts/jars/
```

---

## Performance Tuning

### General Performance Tips

1. **Use Trino for interactive queries** (7.6x faster than Hive)
2. **Partition large tables** by date or frequently filtered columns
3. **Use Iceberg format** for ACID transactions and time travel
4. **Enable compression** (Snappy for balance, Gzip for size)
5. **Increase parallelism** (more mappers/executors for large datasets)
6. **Monitor resource usage** (CPU, memory, disk, network)

### Cluster Health Checks

```bash
# Daily health check script
#!/bin/bash

# HDFS health
hdfs dfsadmin -report | grep "Live datanodes"

# YARN health
yarn node -list | grep RUNNING

# Hive Metastore
hive -e "SHOW DATABASES;" > /dev/null && echo "Hive OK"

# Airflow
curl -s http://localhost:8080/health | grep healthy

# Disk space
df -h | grep -E "(/|/opt|/var)"

# Memory
free -h

# Load average
uptime
```

---

## Getting Help

### Log Locations

- **Hadoop**: `/opt/hadoop/logs/`
- **Hive**: `/opt/hive/logs/`
- **Spark**: `/opt/spark/logs/`
- **Airflow**: `/opt/airflow/logs/`
- **Trino**: `/opt/trino/var/log/`
- **Ranger**: `/opt/ranger/logs/`

### Useful Commands

```bash
# Check all services status
jps

# Monitor cluster resources
htop

# Check network connectivity
netstat -tulpn

# View recent logs
journalctl -xe

# Check Docker container status
docker ps -a
docker stats
```

### Support Resources

- **Documentation**: See [USER_GUIDE.md](USER_GUIDE.md)
- **Configuration**: See [CONFIGURATION.md](CONFIGURATION.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **GitHub Issues**: Report bugs and request features

---

**Last Updated**: 2025-01-03  
**Version**: 1.0
