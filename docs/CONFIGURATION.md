# DX House Configuration Guide

Comprehensive configuration guide for all DX House components.

## Table of Contents

1. [Hadoop Configuration](#hadoop-configuration)
2. [Hive Configuration](#hive-configuration)
3. [Spark Configuration](#spark-configuration)
4. [Trino Configuration](#trino-configuration)
5. [Airflow Configuration](#airflow-configuration)
6. [Ranger Configuration](#ranger-configuration)
7. [Gravitino Configuration](#gravitino-configuration)
8. [Hue Configuration](#hue-configuration)

---

## Hadoop Configuration

### Core Configuration (core-site.xml)

**Location**: `/opt/hadoop/etc/hadoop/core-site.xml`

**Key Properties**:
```xml
<property>
    <name>fs.defaultFS</name>
    <value>hdfs://dx-master:8020</value>
    <description>Default file system URI</description>
</property>

<property>
    <name>hadoop.tmp.dir</name>
    <value>/opt/hadoop/tmp</value>
    <description>Temporary directory</description>
</property>

<property>
    <name>hadoop.security.key.provider.path</name>
    <value>kms://http@dx-master:9600/kms</value>
    <description>KMS provider for encryption</description>
</property>
```

### HDFS Configuration (hdfs-site.xml)

**Location**: `/opt/hadoop/etc/hadoop/hdfs-site.xml`

**Key Properties**:
```xml
<property>
    <name>dfs.replication</name>
    <value>2</value>
    <description>Block replication factor</description>
</property>

<property>
    <name>dfs.namenode.name.dir</name>
    <value>file:///opt/hadoop/data/namenode</value>
    <description>NameNode metadata directory</description>
</property>

<property>
    <name>dfs.datanode.data.dir</name>
    <value>file:///opt/hadoop/data/datanode</value>
    <description>DataNode data directory</description>
</property>

<property>
    <name>dfs.encryption.key.provider.uri</name>
    <value>kms://http@dx-master:9600/kms</value>
    <description>Encryption key provider</description>
</property>
```

**Tuning Parameters**:
- `dfs.block.size`: 128MB (default) or 256MB for large files
- `dfs.namenode.handler.count`: 10 * log2(cluster size)
- `dfs.datanode.max.transfer.threads`: 4096 for high concurrency

### YARN Configuration (yarn-site.xml)

**Location**: `/opt/hadoop/etc/hadoop/yarn-site.xml`

**Key Properties**:
```xml
<property>
    <name>yarn.resourcemanager.hostname</name>
    <value>dx-master</value>
</property>

<property>
    <name>yarn.nodemanager.resource.memory-mb</name>
    <value>6144</value>
    <description>Memory available for containers</description>
</property>

<property>
    <name>yarn.nodemanager.resource.cpu-vcores</name>
    <value>4</value>
    <description>CPU cores available</description>
</property>

<property>
    <name>yarn.scheduler.maximum-allocation-mb</name>
    <value>4096</value>
    <description>Maximum memory per container</description>
</property>
```

### KMS Configuration (kms-site.xml)

**Location**: `/opt/hadoop/etc/hadoop/kms-site.xml`

**Key Properties**:
```xml
<property>
    <name>hadoop.kms.authentication.type</name>
    <value>simple</value>
</property>

<property>
    <name>hadoop.kms.key.provider.uri</name>
    <value>jceks://file@/opt/hadoop/etc/hadoop/kms.keystore</value>
</property>
```

**Security Zones**:
```bash
# Create encryption keys
hadoop key create key_storage_zone
hadoop key create key_transform_delivery_zone

# Create encryption zones
hdfs crypto -createZone -keyName key_storage_zone -path /storage
hdfs crypto -createZone -keyName key_transform_delivery_zone -path /user/hive/warehouse
```

---

## Hive Configuration

### Hive Site Configuration (hive-site.xml)

**Location**: `/opt/hive/conf/hive-site.xml`

**Metastore Configuration**:
```xml
<property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://dx-database:3306/metastore?createDatabaseIfNotExist=true</value>
</property>

<property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>com.mysql.cj.jdbc.Driver</value>
</property>

<property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>hive</value>
</property>

<property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>hivepass</value>
</property>

<property>
    <name>hive.metastore.uris</name>
    <value>thrift://dx-master:9083</value>
</property>
```

**Warehouse Configuration**:
```xml
<property>
    <name>hive.metastore.warehouse.dir</name>
    <value>/user/hive/warehouse</value>
</property>

<property>
    <name>hive.exec.scratchdir</name>
    <value>/tmp/hive</value>
</property>
```

**Performance Tuning**:
```xml
<property>
    <name>hive.execution.engine</name>
    <value>tez</value>
    <description>Use Tez for better performance</description>
</property>

<property>
    <name>hive.vectorized.execution.enabled</name>
    <value>true</value>
</property>

<property>
    <name>hive.optimize.ppd</name>
    <value>true</value>
    <description>Enable predicate pushdown</description>
</property>

<property>
    <name>hive.exec.dynamic.partition.mode</name>
    <value>nonstrict</value>
</property>
```

**Iceberg Integration**:
```xml
<property>
    <name>iceberg.engine.hive.enabled</name>
    <value>true</value>
</property>
```

---

## Spark Configuration

### Spark Defaults (spark-defaults.conf)

**Location**: `/opt/spark/conf/spark-defaults.conf`

**Core Configuration**:
```properties
spark.master                     spark://dx-master:7077
spark.eventLog.enabled           true
spark.eventLog.dir               hdfs://dx-master:8020/spark-logs
spark.history.fs.logDirectory    hdfs://dx-master:8020/spark-logs
```

**Executor Configuration**:
```properties
spark.executor.memory            4g
spark.executor.cores             2
spark.executor.instances         3
spark.driver.memory              4g
spark.driver.cores               2
```

**Hive Integration**:
```properties
spark.sql.catalogImplementation  hive
spark.sql.hive.metastore.uris    thrift://dx-master:9083
spark.sql.warehouse.dir          hdfs://dx-master:8020/user/hive/warehouse
```

**Iceberg Configuration**:
```properties
spark.sql.extensions             org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
spark.sql.catalog.spark_catalog  org.apache.iceberg.spark.SparkSessionCatalog
spark.sql.catalog.spark_catalog.type  hive
spark.sql.catalog.local          org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.local.type     hadoop
spark.sql.catalog.local.warehouse  hdfs://dx-master:8020/user/hive/warehouse
```

**Performance Tuning**:
```properties
spark.sql.adaptive.enabled       true
spark.sql.adaptive.coalescePartitions.enabled  true
spark.sql.shuffle.partitions     200
spark.serializer                 org.apache.spark.serializer.KryoSerializer
```

---

## Trino Configuration

### Server Configuration (config.properties)

**Location**: `/opt/trino/etc/config.properties`

```properties
coordinator=true
node-scheduler.include-coordinator=false
http-server.http.port=8081
query.max-memory=4GB
query.max-memory-per-node=2GB
discovery.uri=http://dx-worker3:8081
```

### JVM Configuration (jvm.config)

**Location**: `/opt/trino/etc/jvm.config`

```
-server
-Xmx8G
-XX:+UseG1GC
-XX:G1HeapRegionSize=32M
-XX:+UseGCOverheadLimit
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:+ExitOnOutOfMemoryError
```

### Catalog Configuration

**Hive Catalog** (`catalog/hive.properties`):
```properties
connector.name=hive
hive.metastore.uri=thrift://dx-master:9083
hive.allow-drop-table=true
hive.allow-rename-table=true
```

**Iceberg Catalog** (`catalog/iceberg.properties`):
```properties
connector.name=iceberg
hive.metastore.uri=thrift://dx-master:9083
iceberg.catalog.type=hive
```

---

## Airflow Configuration

### Airflow Configuration (airflow.cfg)

**Location**: `/opt/airflow/airflow.cfg`

**Core Settings**:
```ini
[core]
dags_folder = /opt/airflow/dags
base_log_folder = /opt/airflow/logs
executor = LocalExecutor
sql_alchemy_conn = sqlite:////opt/airflow/airflow.db
parallelism = 32
dag_concurrency = 16
max_active_runs_per_dag = 16
```

**Webserver Settings**:
```ini
[webserver]
web_server_host = 0.0.0.0
web_server_port = 8080
base_url = http://dx-worker3:8080
```

**Scheduler Settings**:
```ini
[scheduler]
scheduler_heartbeat_sec = 5
max_threads = 2
catchup_by_default = False
```

### Connections

**Hadoop SSH Connection**:
```bash
airflow connections add hadoop_ssh \
    --conn-type ssh \
    --conn-host dx-master \
    --conn-login hadoop \
    --conn-port 22
```

**Spark Connection**:
```bash
airflow connections add spark \
    --conn-type spark \
    --conn-host spark://dx-master:7077
```

---

## Ranger Configuration

### Installation Properties (install.properties)

**Location**: `/opt/ranger/install.properties`

**Database Configuration**:
```properties
DB_FLAVOR=MYSQL
SQL_CONNECTOR_JAR=/opt/ranger/mysql-connector-j-8.0.33.jar
db_root_user=root
db_root_password=rootpass
db_host=dx-database:3306
db_name=ranger
db_user=rangeradmin
db_password=rangerpass
```

**Ranger Admin**:
```properties
rangerAdmin_password=admin
rangerTagsync_password=tagsync
rangerUsersync_password=usersync
keyadmin_password=keyadmin
```

**Policy Manager**:
```properties
policymgr_external_url=http://dx-worker3:6080
policymgr_http_enabled=true
```

### Service Configuration

**Hadoop Service**:
1. Navigate to Ranger UI → Service Manager
2. Add new Hadoop service
3. Configure:
   - Service Name: hadoop
   - Username: hadoop
   - Password: hadoop
   - HDFS URL: hdfs://dx-master:8020

**Hive Service**:
1. Add new Hive service
2. Configure:
   - Service Name: hive
   - JDBC URL: jdbc:hive2://dx-master:10000
   - Username: hive

---

## Gravitino Configuration

### Gravitino Configuration (gravitino.conf)

**Location**: `/opt/gravitino/conf/gravitino.conf`

```properties
gravitino.server.webserver.host = 0.0.0.0
gravitino.server.webserver.httpPort = 8090
gravitino.catalog.backend = hive
gravitino.catalog.hive.metastore.uris = thrift://dx-master:9083
```

### Iceberg REST Server (gravitino-iceberg-rest-server.conf)

```properties
gravitino.iceberg-rest.warehouse = hdfs://dx-master:8020/user/hive/warehouse
gravitino.iceberg-rest.catalog-backend = hive
gravitino.iceberg-rest.uri = thrift://dx-master:9083
```

---

## Hue Configuration

### Hue Configuration (hue.ini)

**Location**: `/opt/hue/conf/hue.ini`

**Server Configuration**:
```ini
[desktop]
http_host=0.0.0.0
http_port=8888
time_zone=UTC
```

**Database Configuration**:
```ini
[[database]]
engine=mysql
host=dx-database
port=3306
user=hue
password=huepass
name=hue
```

**Hive Configuration**:
```ini
[beeswax]
hive_server_host=dx-master
hive_server_port=10000
hive_conf_dir=/opt/hive/conf
```

**HDFS Configuration**:
```ini
[hadoop]
[[hdfs_clusters]]
[[[default]]]
fs_defaultfs=hdfs://dx-master:8020
webhdfs_url=http://dx-master:9870/webhdfs/v1
```

---

## Performance Tuning Guidelines

### Memory Allocation

**Total Memory per Node**: 8-18 GB

**Recommended Distribution**:
- YARN NodeManager: 6 GB
- Spark Executors: 4 GB
- OS and other services: 2-8 GB

### CPU Allocation

**Total Cores per Node**: 5

**Recommended Distribution**:
- YARN containers: 4 cores
- OS and services: 1 core

### Disk Configuration

- **HDFS**: Use separate disks for NameNode and DataNode
- **Logs**: Separate partition for logs
- **Temp**: Fast SSD for temporary files

### Network Optimization

- **Bandwidth**: Minimum 1 Gbps between nodes
- **Latency**: <1ms within cluster
- **Firewall**: Allow required ports

---

## Security Best Practices

1. **Change Default Passwords**: All services
2. **Enable SSL/TLS**: For all web interfaces
3. **Configure Kerberos**: For production environments
4. **Regular Updates**: Keep software up to date
5. **Audit Logging**: Enable and monitor
6. **Backup**: Regular configuration backups

---

## Configuration Validation

### Verification Commands

```bash
# Hadoop
hdfs dfsadmin -report
yarn node -list

# Hive
hive -e "SHOW DATABASES;"

# Spark
spark-submit --version

# Trino
trino --execute "SELECT 1;"

# Airflow
airflow dags list

# Ranger
curl http://dx-worker3:6080/service/public/v2/api/service
```

---

**Last Updated**: 2025-01-03  
**Version**: 1.0
