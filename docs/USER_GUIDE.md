# DX House User Guide

Complete guide for using the DX House unified data management architecture.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Data Ingestion](#data-ingestion)
3. [Data Transformation](#data-transformation)
4. [Data Delivery](#data-delivery)
5. [Query Execution](#query-execution)
6. [Security & Access Control](#security--access-control)
7. [Monitoring & Management](#monitoring--management)

---

## Getting Started

### Prerequisites

- Docker installed and running
- 4-node cluster (1 master + 3 workers) or equivalent resources
- Minimum 8GB RAM per node
- 100GB disk space per node

### Initial Setup

1. **Start the cluster**:
```bash
# On master node
docker run -d --name dx-master --hostname dx-master dxhouse-cls:latest

# On worker nodes
docker run -d --name dx-worker1 --hostname dx-worker1 dxhouse-cls:latest
docker run -d --name dx-worker2 --hostname dx-worker2 dxhouse-cls:latest
docker run -d --name dx-worker3 --hostname dx-worker3 dxhouse-cls:latest
```

2. **Verify services**:
```bash
# Check HDFS
hdfs dfsadmin -report

# Check YARN
yarn node -list

# Check Hive Metastore
hive -e "SHOW DATABASES;"
```

3. **Access web interfaces**:
- Airflow: http://dx-worker3:8082
- Superset: http://dx-worker3:9099
- Hue: http://dx-worker3:8888
- Ranger: http://dx-worker3:6080
- Gravitino: http://dx-worker3:7070
- Trino: http://dx-worker3:8090

---

## Data Ingestion

### Batch Ingestion

Use Airflow DAG for automated batch ingestion:

1. **Access Airflow UI**: http://dx-worker3:8082
2. **Trigger DAG**: `batch_ingestion_dag`
3. **Monitor progress**: Check task status in Airflow UI

**Manual Sqoop Import**:
```bash
sqoop import \
    --connect jdbc:mysql://dx-database:3306/tpch \
    --username hive \
    --password ${HIVE_DB_PASSWORD} \
    --table orders \
    --target-dir /storage/tpch/orders \
    --fields-terminated-by ',' \
    --compress \
    --compression-codec org.apache.hadoop.io.compress.SnappyCodec
```

### Incremental Ingestion

For delta updates on high-velocity tables:

1. **Trigger DAG**: `incremental_ingestion_dag`
2. **Tables supported**: orders, lineitem
3. **Schedule**: Can be configured for hourly/daily runs

**Performance**:
- Throughput: 0.04 - 15.4 MB/s
- Parallel mappers: 1-6 depending on table size
- Compression: Snappy (2:1 ratio)

---

## Data Transformation

### Initialize Data Warehouse

Create star schema and databases:

1. **Trigger DAG**: `init_databases_start_schema`
2. **Databases created**:
   - `datawarehouse` - Star schema for analytics
   - `delivery` - Business data marts
   - `sandbox` - ML/AI experimentation

3. **Star Schema Components**:
   - Fact table: `fact_sales` (partitioned by date)
   - Dimensions: customer, supplier, part, order, geography, time

### Populate Star Schema

Transform raw data into analytical format:

1. **Trigger DAG**: `populate_star_schema` (runs after init)
2. **Process**: Joins raw tables, applies transformations
3. **Format**: Apache Iceberg for ACID transactions

### Refresh Data Warehouse

For incremental updates:

1. **Trigger DAG**: `refresh_datawarehouse`
2. **Frequency**: After incremental ingestion
3. **Method**: Merge new records into existing tables

---

## Data Delivery

### Create Data Marts

Build business-specific aggregated views:

1. **Trigger DAG**: `build_datamart_delivery`
2. **Data Marts Created**:
   - `sales_by_customer` - Revenue per customer
   - `sales_by_region` - Geographic analysis
   - `sales_summary` - Time-series trends

### Query Data Marts

**Using Trino** (recommended for performance):
```sql
-- Connect to Trino
trino --catalog hive --schema delivery

-- Query data mart
SELECT * FROM sales_by_region ORDER BY total_revenue DESC;
```

**Using Hive**:
```sql
-- Connect to Hive
hive

-- Query data mart
USE delivery;
SELECT * FROM sales_by_customer LIMIT 10;
```

---

## Query Execution

### Query Engines

**Trino** (7.6x faster than Hive):
- Best for: Interactive queries, ad-hoc analysis
- Access: Hue UI or CLI
- Performance: Optimized for low-latency

**Hive**:
- Best for: Batch processing, ETL jobs
- Access: Hive CLI or Hue
- Performance: Suitable for large-scale transformations

### Example Queries

**Simple Aggregation**:
```sql
SELECT 
    o_orderpriority, 
    COUNT(*) as order_count 
FROM orders 
GROUP BY o_orderpriority;
```

**Join with Aggregation**:
```sql
SELECT 
    c.c_name, 
    SUM(l.l_extendedprice) as total_spent
FROM customer c
JOIN orders o ON c.c_custkey = o.o_custkey
JOIN lineitem l ON o.o_orderkey = l.l_orderkey
GROUP BY c.c_name
ORDER BY total_spent DESC
LIMIT 10;
```

### Query Performance Tips

1. **Use Trino for interactive queries** (7.6x speedup)
2. **Leverage partitioning** (date-based partitions)
3. **Use Iceberg time travel** for historical analysis
4. **Enable predicate pushdown** in query engines

---

## Security & Access Control

### Apache Ranger

**Access Ranger UI**: http://dx-worker3:6080

**Default Credentials**:
- Username: admin
- Password: admin (change immediately)

### Create User Roles

1. **Navigate to**: Settings → Users/Groups
2. **Create roles**:
   - `admin` - Full access
   - `data_engineer` - Read/write on raw and datawarehouse
   - `analyst` - Read-only on delivery and datawarehouse
   - `data_scientist` - Full access to sandbox

### Define Access Policies

1. **Navigate to**: Access Manager → Resource Based Policies
2. **Create policy**:
   - Service: Hadoop SQL
   - Database: delivery
   - Table: sales_by_customer
   - Permissions: SELECT
   - Users/Groups: analyst_group

### Encryption

**At Rest** (Hadoop KMS):
- Security zones configured for storage and warehouse paths
- Automatic encryption/decryption

**In Transit** (SSL/TLS):
- All service communications encrypted
- HTTPS enabled for web interfaces

---

## Monitoring & Management

### Apache Gravitino

**Metadata Management**: http://dx-worker3:7070

**Features**:
- Unified catalog across all databases
- Schema evolution tracking
- Lineage visualization

### Apache Superset

**BI Dashboards**: http://dx-worker3:9099

**Create Dashboard**:
1. **Add Dataset**: Connect to delivery database
2. **Create Chart**: Choose visualization type
3. **Build Dashboard**: Combine multiple charts
4. **Share**: Set permissions and publish

### Hue

**SQL Editor**: http://dx-worker3:8888

**Features**:
- Interactive query editor
- Query history and saved queries
- File browser for HDFS
- Job browser for YARN

### Airflow Monitoring

**Workflow Management**: http://dx-worker3:8082

**Monitor DAGs**:
1. **View DAG runs**: Check execution history
2. **Task logs**: Debug failed tasks
3. **Gantt chart**: Visualize task dependencies
4. **Trigger manually**: Run DAGs on-demand

---

## Best Practices

### Data Ingestion
- Use batch ingestion for initial loads
- Switch to incremental for ongoing updates
- Monitor Sqoop mapper performance
- Compress data with Snappy

### Data Transformation
- Partition large tables by date
- Use Iceberg for ACID transactions
- Leverage Spark for complex transformations
- Maintain star schema integrity

### Query Optimization
- Use Trino for interactive queries
- Create appropriate indexes
- Partition pruning for better performance
- Cache frequently accessed data

### Security
- Change default passwords immediately
- Implement least privilege access
- Enable audit logging
- Regular security policy reviews
- Encrypt sensitive data

### Monitoring
- Check cluster health daily
- Monitor disk usage (HDFS)
- Review query performance
- Track DAG execution times
- Set up alerts for failures

---

## Troubleshooting

For common issues and solutions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

For configuration details, see [CONFIGURATION.md](CONFIGURATION.md).

For architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

**Last Updated**: December 1, 2025
**Version**: 1.0
