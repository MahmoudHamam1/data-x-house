# DXHouse Cluster Setup & Configuration Guide

## Table of Contents
- [1. Overview](#1-overview)
- [2. Prerequisites](#2-prerequisites)
- [3. Provision VMs with Docker](#3-provision-vms-with-docker)
  - [3.1 Build DXHouse Docker Image](#31-build-dxhouse-docker-image)
    - [3.1.1 Hadoop](#311-hadoop)
    - [3.1.2 YARN](#312-yarn)
    - [3.1.3 MapReduce](#313-mapreduce)
    - [3.1.4 Hive](#314-hive)
    - [3.1.5 Spark](#315-spark)
    - [3.1.6 Iceberg](#316-iceberg)
  - [3.2 Ranger](#32-ranger)
  - [3.3 Hue](#33-hue)
  - [3.4 Trino](#34-trino)
  - [3.5 Airflow](#35-airflow)
  - [3.6 Gravitino](#36-gravitino)
  - [3.7 Superset](#37-superset)
- [4. Verification & Testing](#4-verification--testing)
- [5. Troubleshooting](#5-troubleshooting)
- [6. Maintenance](#6-maintenance)
- [7. Appendix](#7-appendix)

---

## 1. Overview

### Project Name
**DXHouse Big Data Cluster**

### Objective
DXHouse is a Docker-based distributed big data environment designed for local testing, experimentation, and analytics development.  
It replicates an enterprise-grade Hadoop ecosystem in a contained environment using multiple CentOS-based VMs and Docker containers.

### Architecture Summary
- **Nodes:** 1 Master + 2 Workers  
- **Network:** `dxhouse-net`  
- **Directory Base:** `/dxhouse`  
- **Core Components:** Hadoop, YARN, Hive, Spark, Iceberg  
- **Optional Components:** Ranger, Hue, Trino, Airflow, Gravitino, Superset

### Purpose
This guide provides all steps to provision the environment, build Docker images, configure services, and verify the full cluster operation.

---

## 2. Prerequisites

| Category | Details |
|-----------|----------|
| OS | CentOS 7 (or compatible) |
| RAM | 8 GB per node (minimum) |
| CPU | 4 cores per node |
| Disk | 100 GB per node |
| Hostnames | `dx-master`, `dx-worker1`, `dx-worker2` |
| Directory | `/dxhouse` |
| Network | Docker network `dxhouse-net` |
| External DB | MariaDB for Hive metastore |
| Dependencies | Java 1.8, Docker, Docker Compose |

### Pre-Setup Checklist
- [ ] Update system packages  
- [ ] Configure `/etc/hosts` for all nodes  
- [ ] Set up SSH key-based access  
- [ ] Create Docker network  
- [ ] Verify Docker permissions for user `hadoop`  

---

## 3. Provision VMs with Docker

Each VM acts as a node in the cluster and runs specific services in containers.

### Steps
1. Create 3 VMs (`dx-master`, `dx-worker1`, `dx-worker2`).
2. Install Docker on all nodes.
3. Create a shared network:
   ```bash
   docker network create dxhouse-net
   ```
4. Verify connectivity using ping or Docker network inspect.

---

## 3.1 Build DXHouse Docker Image

The base image includes all Hadoop ecosystem components.  
Each service will run using this shared base image for consistency.

### 3.1.1 Hadoop
- **Version:** 3.3.6  
- **Base Path:** `/dxhouse/hadoop`
- **Configs:**
  - `core-site.xml`
  - `hdfs-site.xml`
- **Commands:**
  ```bash
  hdfs namenode -format
  start-dfs.sh
  ```

### 3.1.2 YARN
- **Version:** 3.3.6  
- **Configs:**
  - `yarn-site.xml`
  - `capacity-scheduler.xml`
- **Start Command:**
  ```bash
  start-yarn.sh
  ```

### 3.1.3 MapReduce
- **Version:** Integrated with Hadoop 3.3.6  
- **Configs:**
  - `mapred-site.xml`
- **Validation Command:**
  ```bash
  hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar pi 2 5
  ```

### 3.1.4 Hive
- **Version:** 3.1.3  
- **Metastore:** MariaDB  
- **Configs:**
  - `hive-site.xml`
- **Init Command:**
  ```bash
  schematool -initSchema -dbType mysql
  hive --service metastore
  ```

### 3.1.5 Spark
- **Version:** 3.4.2  
- **Mode:** YARN Cluster  
- **Configs:**
  - `spark-defaults.conf`
- **Validation Command:**
  ```bash
  spark-submit --class org.apache.spark.examples.SparkPi   /dxhouse/spark/examples/jars/spark-examples_2.12-3.4.2.jar 10
  ```

### 3.1.6 Iceberg
- **Version:** 1.6.0  
- **Catalog:** Hive or REST-based  
- **Configs:**
  - `iceberg-site.xml`
- **Setup Command:**
  ```bash
  CREATE CATALOG local_catalog WITH (
    'type'='hive',
    'uri'='thrift://dx-master:9083'
  );
  ```

---

## 3.2 Ranger

- **Purpose:** Centralized security and policy management for Hadoop ecosystem  
- **Version:** 2.4  
- **Configs:**
  - Database setup
  - Policy sync to HDFS, Hive, YARN  
- **Validation Command:**
  Access Ranger admin UI at `http://dx-master:6080`

---

## 3.3 Hue

- **Purpose:** Web UI for HDFS, Hive, and Spark interaction  
- **Version:** 4.11+  
- **Configs:** `hue.ini`  
- **Validation Command:**
  Access Hue at `http://dx-master:8888`

---

## 3.4 Trino

- **Purpose:** Interactive SQL query engine for federated data access  
- **Version:** Latest  
- **Configs:**
  - `config.properties`
  - `catalog/hive.properties`  
- **Run Command:**
  ```bash
  docker run -d --name dx-trino --network dxhouse-net     -p 8085:8080 -v /dxhouse/config/trino:/etc/trino trinodb/trino:latest
  ```

---

## 3.5 Airflow

- **Purpose:** Workflow orchestration and scheduling  
- **Executor:** LocalExecutor  
- **Configs:**
  - `airflow.cfg`
- **Start Command:**
  ```bash
  airflow db init
  airflow webserver &
  airflow scheduler &
  ```

---

## 3.6 Gravitino

- **Purpose:** Metadata and catalog federation across Iceberg, Hive, and Trino  
- **Version:** Latest stable  
- **Config:** `gravitino.properties`  
- **Validation Command:**
  ```bash
  curl http://dx-master:8090/api/v1/catalogs
  ```

---

## 3.7 Superset

- **Purpose:** Data visualization and BI on top of Trino and Hive  
- **Version:** 3.0+  
- **Setup Commands:**
  ```bash
  superset db upgrade
  superset fab create-admin
  superset load_examples
  superset run -p 8088 --with-threads --reload
  ```
- **Access:** [http://dx-master:8088](http://dx-master:8088)

---

## 4. Verification & Testing

| Service | Verification Command | Expected Result |
|----------|---------------------|-----------------|
| HDFS | `hdfs dfsadmin -report` | Shows live datanodes |
| YARN | `yarn node -list` | Shows worker nodes |
| Hive | `hive -e "SHOW DATABASES;"` | Lists default and user DBs |
| Spark | `spark-shell` | Opens REPL |
| Ranger | Web UI login | Success |
| Hue | Login page loads | Success |
| Trino | `trino --execute "SHOW CATALOGS;"` | Lists catalogs |
| Superset | Dashboard loads | OK |

---

## 5. Troubleshooting

| Issue | Cause | Solution |
|-------|--------|----------|
| `Network not found: dxhouse-net` | Docker network missing | `docker network create dxhouse-net` |
| `Permission denied` when writing logs | Wrong ownership | `chown -R hadoop:hadoop /dxhouse` |
| `No route to host` between nodes | Host file or firewall | Check `/etc/hosts` and `firewalld` |
| Hive not connecting to MariaDB | JDBC config issue | Verify `hive-site.xml` DB URL |

---

## 6. Maintenance

- **Start all containers:**
  ```bash
  docker start $(docker ps -a -q)
  ```
- **Stop all containers:**
  ```bash
  docker stop $(docker ps -q)
  ```
- **Backup Configurations:**
  ```bash
  tar -czvf dxhouse-config-backup.tar.gz /dxhouse/config
  ```
- **Update Process:**
  - Stop services
  - Rebuild Docker image
  - Restart containers

---

## 7. Appendix

### Version Matrix
| Component | Version |
|------------|----------|
| Hadoop | 3.3.6 |
| YARN | 3.3.6 |
| Hive | 3.1.3 |
| Spark | 3.4.2 |
| Iceberg | 1.6.0 |
| Ranger | 2.4 |
| Hue | 4.11 |
| Trino | Latest |
| Airflow | 2.x |
| Gravitino | Latest |
| Superset | 3.x |

### Network Diagram
You can visualize your cluster using [draw.io](https://app.diagrams.net) or embed an image like:

```
dx-master
 ├── HDFS NameNode
 ├── YARN ResourceManager
 ├── Hive Metastore
 ├── Ranger, Hue, Trino, Airflow, Gravitino, Superset
 └── dx-worker1, dx-worker2 → DataNode + NodeManager
```

### References
- [Apache Hadoop](https://hadoop.apache.org/)
- [Apache Spark](https://spark.apache.org/)
- [Apache Hive](https://hive.apache.org/)
- [Trino Docs](https://trino.io/docs.html)
- [Apache Airflow](https://airflow.apache.org/)
- [Apache Superset](https://superset.apache.org/)

---
© 2025 DXHouse Project — Maintained by DXHouse Team
