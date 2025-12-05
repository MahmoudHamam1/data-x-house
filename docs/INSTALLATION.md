# DXHouse Cluster Setup & Configuration Guide

## Table of Contents
- [1. Overview](#1-overview)
- [2. Prerequisites](#2-prerequisites)
- [3. Provision VMs with Docker](#3-provision-vms-with-docker)
  - [4. Configure Docker Cluster](#4-configure-docker-cluster)
  - [4.1 Build DXHouse Docker Image](#31-build-dxhouse-docker-image)
    - [3.1.1 Hadoop](#311-hadoop)
    - [3.1.2 YARN](#312-yarn)
    - [3.1.3 MapReduce](#313-mapreduce)
    - [3.1.4 Hive](#314-hive)
    - [3.1.5 Spark](#315-spark)
    - [3.1.6 Iceberg](#316-iceberg)
    - [4.2 Ranger](#32-ranger)
    - [4.3 Hue](#33-hue)
    - [4.4 Trino](#34-trino)
    - [4.5 Airflow](#35-airflow)
    - [4.6 Gravitino](#36-gravitino)
    - [4.7 Superset](#37-superset)
- [5. Verification & Testing](#4-verification--testing)
- [6. Troubleshooting](#5-troubleshooting)
- [7. Maintenance](#6-maintenance)
- [8. Appendix](#7-appendix)

---

## 1. Overview

### Project Name
**DXHouse Big Data Cluster**

### Objective
DXHouse is a Docker-based distributed big data environment designed for local testing, experimentation, and analytics development.  
It replicates an enterprise-grade Hadoop ecosystem in a contained environment using multiple CentOS-based VMs and Docker containers.

### Architecture Summary
- **Nodes:** 1 Master + 3 Workers  
- **Network:** Docker overlay network `dxhouse-net`  
- **Directory Base:** `/dxhouse`  
- **Core Components:** Hadoop, YARN, Hive, Spark, Iceberg  
- **Optional Components:** Ranger, Hue, Trino, Airflow, Gravitino, Superset

### Purpose
This guide provides all steps to provision the environment, build Docker images, configure services, and verify the full cluster operation.

---

## 2. Prerequisites

| Category | Details |
|-----------|----------|
| OS | CentOS 7, RHEL 7, or compatible Linux |
| RAM | 8 GB per node (minimum) |
| CPU | 5 cores per node |
| Disk | 100 GB per node |
| Hostnames | `dx-master`, `dx-worker1`, `dx-worker2`, `dx-worker3` |
| Directory | `/dxhouse` |
| Network | Docker overlay network `dxhouse-net` |
| External DB | MySQL 8.0 as metastore and services database backend |
| Dependencies | Java 1.8, Docker, Docker Compose |

### Pre-Setup Checklist
- [ ] Update system packages  
- [ ] Setup the network and IPs
- [ ] Configure `/etc/hosts` for all nodes  
- [ ] Set up SSH passwordless access  
- [ ] Create Docker overlay network  
- [ ] Verify Docker permissions for user `hadoop`  

---

## 3. Provision VMs with Docker

Each VM acts as a node in the cluster and runs specific services in containers.

### Steps (`ALL Nodes`)
1. Create 4 VMs (`dx-master`, `dx-worker1`, `dx-worker2`, `dx-worker3`).
2. Prep Cluster ENV (HostName, Network, SSH)
   1. Set HostNames
        ```bash
        # Set HostNames
        hostname -f
        # On Master Node
        hostname dx-master.domain.name
        sudo nano /etc/hostname # Add HostName
        # On Worker Nodes 
        hostname dx-worker-<$>.domain.name
        sudo nano /etc/hostname # Add HostName
        ```
   2. Edit Network Configuration File
        ```bash
        # Modify the HOSTNAME property to its FQDN
        nano /etc/sysconfig/network
            # Set NETWORK=yes
            # Set HOSTNAME=$HostName$
        # Set ip address
        nano /etc/sysconfig/network-scripts/ifcfg-ens33
            # Master: IPADDR=192.168.2.100 
            # Worker-1: IPADDR=192.168.2.101 
            # Worker-2: IPADDR=192.168.2.102
            # Worker-3: IPADDR=192.168.2.103 
        ```
   3. Edit Hosts File
        ```bash
        nano /etc/hosts
            # 192.168.2.100 dx-master dx-master.domain.name
            # 192.168.2.101 dx-worker1 dx-worker-1.domain.name
            # 192.168.2.102 dx-worker2 dx-worker-2.domain.name
            # 192.168.2.103 dx-worker3 dx-worker-3.domain.name
        ```
   4. Setup password-less SSH
        ```bash
        # On Master Node
        ssh-keygen -t rsa
        ssh-copy-id localhost
        ssh dx-master

        # Share the Keys with worker nodes
        scp -pr /root/.ssh root@dx-worker2:/root/
        cat .ssh/id_rsa.pub | ssh root@dx-worker$ 'cat >> .ssh/authorized_keys'
        ssh root@dx-worker2; chmod 700 .ssh; chmod 640 .ssh/authorized_keys
        
        # Test the connection between the nodes
        ssh root@dx-worker$
        ```
   5. Setup NTP & Configure firewall 
        ```bash
        # Install and Enable NTP
        yum install -y ntp
        systemctl enable ntpd
        systemctl start ntpd
        # Check status
        timedatectl status

        # Disable Firewall
        systemctl disable firewalld
        service firewalld stop
        # Update SELINUX value from enhancing to disabled 
        nano /etc/selinux/config
        ```
3. Update system Packages
   1. Update CentOS repo
        ```bash
        sudo sed -i 's/^mirrorlist=/#mirrorlist=/g' /etc/yum.repos.d/CentOS-Base.repo
        sudo sed -i 's|^#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-Base.repo

        sudo yum clean all
        sudo yum makecache
        ```
4. Install Docker.
    ```bash 
    sudo yum install -y https://vault.centos.org/7.9.2009/extras/x86_64/Packages/container-selinux-2.119.2-1.911c772.el7_8.noarch.rpm
    sudo sed -i 's|http://vault.centos.org|https://vault.centos.org|g' /etc/yum.repos.d/CentOS-Base.repo
    sudo yum clean all
    sudo yum makecache
    sudo yum remove -y docker docker-client docker-client-latest docker-common \
                    docker-latest docker-latest-logrotate docker-logrotate docker-engine

    sudo yum install -y yum-utils

    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    systemctl start docker
    systemctl enable docker
    ```
5. Docker Shared Network
   1. Create a shared network: (`On Master`)
        ```bash 
        # Create the overlay network
        docker swarm init --advertise-addr 192.168.2.100
        docker network create --driver overlay --attachable dxhouse-net

        # Get the Join command 
        docker swarm join-token worker

        # Verify the attached nodes
        docker node ls
        ```
   2. Join the Network (`On Admin & Workers`) 
        ```bash
            # Use the Join command to attach the network
            docker swarm join --token SWMTKN-1-xxxxx 192.168.2.100:2377
        ```
6. Verify connectivity using ping or Docker network inspect.

---

## 4. Configure Docker Cluster

### 4.1 Build DXHouse Docker Image

The base image includes the main Hadoop ecosystem components. We have used this image to create the `Master` and `Worker` nodes.

- **Build the dxhouse-cls image**
    ```bash
    # Make Sure you have mounted the Repo
    # Then go to the repo dir
    cd /mnt/hgfs/$dxshared$/dxhouse-image

    # Build the Image
    docker build -t dxhouse-cls .

    # Save the Image as tar file
    docker save dxhouse-cls > dxhouse-cls.tar

    # Share the Image with the worker VMs
    scp dxhouse-cls.tar root@dx-worker2:/tmp/ && scp dxhouse-cls.tar root@dx-worker1:/tmp/
    ```
- **Start Master & Worker Nodes** 
  1. Create the container on the Master Node
        ``` bash
        # Create the Container 
        docker run -itd --name dx-master --hostname dx-master \
        --network dxhouse-net \
        -p 9870:9870 -p 8088:8088 -p 10000:10000 -p 9083:9083 -p 7077:7077 -p 4040:4040 \
        dxhouse-cls
        
        # Open the container shell
        docker exec -it dx-master /bin/bash

        # Before recreate the container, we have to stop and remove the container
        docker stop dx-master && docker rm dx-master
        ```
  2.  Create Container on the Worker Node
        ```bash
        # Load the Image
        docker load < dxhouse-cls.tar

        # Create the Container
        docker run -itd --hostname dx-worker1 --network dxhouse-net --name dx-worker1 --link dx-master:dx-master -p 9864:9864 -p 8042:8042 dxhouse-cls
        ```
  3.  Configure and Start Hadoop Services
        ```bash
        # Open the master container shell
        docker exec -it dx-master /bin/bash

        # Run the setup hosts file
        /dxhouse/bin/setup-hosts.sh

        # Run the cluster configure file
        su hadoop
        /dxhouse/bin/cluster-entrypoint.sh
        ```

#### 4.1.1 Hadoop
- **Version:** 3.3.6  
- **Base Path:** `/dxhouse-image/config/hadoop`
- **Configs:**
  - `core-site.xml`
  - `hdfs-site.xml`
- **Commands:**
  ```bash
  hdfs namenode -format
  start-dfs.sh
  ```

#### 4.1.2 YARN
- **Version:** 3.3.6  
- **Configs:**
  - `yarn-site.xml`
  - `capacity-scheduler.xml`
- **Start Command:**
  ```bash
  start-yarn.sh
  ```

#### 4.1.3 MapReduce
- **Version:** Integrated with Hadoop 3.3.6  
- **Configs:**
  - `mapred-site.xml`
- **Validation Command:**
  ```bash
  hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar pi 2 5
  ```

#### 4.1.4 Hive
- **Version:** 3.1.3  
- **Metastore:** MySQL  
- **Configs:**
  - `hive-site.xml`
- **Init Command:**
  ```bash
  schematool -initSchema -dbType mysql
  hive --service metastore
  ```

#### 4.1.5 Spark
- **Version:** 3.4.2  
- **Mode:** Standalone with 3 workers  
- **Configs:**
  - `spark-defaults.conf` (8GB max memory, 6GB max result size, 2 cores per executor)
  - `workers` (3 worker nodes)
- **Validation Command:**
  ```bash
  spark-submit --class org.apache.spark.examples.SparkPi   /dxhouse/spark/examples/jars/spark-examples_2.12-3.4.2.jar 10
  ```

#### 4.1.6 Iceberg
- **Version:** 1.3.1  
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

### 4.2 Database

- **Purpose:** Host all services metadata and configurations (Hive metastore, Airflow, Ranger, etc.)
- **Version:** 8.0 
- **HOST VM:** dx-worker3
- **Setup Command:**
  ```bash
  # Start the container 
  docker run -d --name dx-database --hostname dx-database \
  --network dxhouse-net \
  -e MYSQL_ROOT_PASSWORD=${DB_ROOT_PASSWORD} \
  -e MYSQL_DATABASE=metastore \
  -e MYSQL_USER=hive \
  -e MYSQL_PASSWORD=${HIVE_DB_PASSWORD} \
  mysql/mysql-server
  ```

### 4.3 Ranger

- **Purpose:** Centralized security and policy management for Hadoop ecosystem  
- **Version:** 2.7.0  
- **HOST VM:** dx-worker3
- **Configs:**
  - `install.properties`
  - Database setup
  - Policy sync to HDFS, Hive, YARN  
- **Setup Commands**
    ```bash
    # Create Ranger container with its deps
    export RANGER_VERSION=2.7.0

    # Create ZooKeeper container
    docker run -d \
    --name ranger-zk \
    --hostname ranger-zk \
    --network dxhouse-net \
    -p 2181:2181 \
    apache/ranger-zk:${RANGER_VERSION}

    # Create Solr container
    docker run -d \
    --name dx-solr \
    --hostname dx-solr \
    --network dxhouse-net \
    -p 8983:8983 \
    apache/ranger-solr:${RANGER_VERSION} \
    solr-precreate ranger_audits /opt/solr/server/solr/configsets/ranger_audits/

    #  Create Ranger container
    docker run -d \
    --name dx-ranger \
    --hostname dx-ranger \
    --network dxhouse-net \
    -p 6080:6080 \
    -e SOLR_HOST=dx-solr \
    -e SOLR_PORT=8983 \
    apache/ranger:${RANGER_VERSION}
    ```
- **Validation Command:**
  Access Solr UI at `http://dx-worker3:8983`
  Access Ranger admin UI at `http://dx-worker3:6080`

---

### 4.4 Hue

- **Purpose:** Web UI for HDFS, Hive, and Spark interaction  
- **Version:** 4.11+  
- **HOST VM:** dx-worker3
- **Configs:** `hue.ini`  
- **Setup Commands**
    ```bash
    # Create Hue Container
    docker run -d --name dx-hue --hostname dx-hue \
    --network dxhouse-net -p 8888:8888 \
    -v /path/to/config/hue/hue.ini:/usr/share/hue/desktop/conf/hue.ini \
    --privileged gethue/hue:latest

    # Attach bridge network
    docker network connect bridge dx-hue
    ```
- **Validation Command:**
    Access Hue at `http://dx-worker3:8888`

---

### 4.5 Trino

- **Purpose:** Interactive SQL query engine for federated data access  
- **Version:** 477  
- **HOST VM:** dx-worker3
- **Configs:**
  - `config.properties`
  - `jvm.config`
  - `hive.properties`
  - `iceberg.properties`  
- **Setup Command:**
  ```bash
  # Create the Trino container
  docker run -d \
  --name dx-trino \
  --hostname dx-trino \
  --network dxhouse-net \
  -p 8090:8080 \
  -v /path/to/config/trino/catalog:/etc/trino/catalog \
  -v /path/to/config/trino/config.properties:/etc/trino/config.properties \
  -v /path/to/config/trino/jvm.config:/etc/trino/jvm.config \
  trinodb/trino:477

  # Attach bridge network
  docker network connect bridge dx-trino
  ```
- **Validation Command:**
    Access Trino at `http://dx-worker3:8090`

---

### 4.6 Airflow

- **Purpose:** Workflow orchestration and scheduling  
- **Version:** 3.0.6
- **Executor:** LocalExecutor  
- **HOST VM:** dx-worker3
- **Configs:**
  - `airflow.cfg`
- **Start Command:**
  ```bash
  # Create Airflow Container 
  docker run -d \
  --name dx-airflow \
  --hostname dx-airflow \
  --network dxhouse-net \
  -p 8082:8080 \
  -p 7001-7010:7001-7010 \
  -p 44000-45000:44000-45000 \
  -e AIRFLOW_HOME=/opt/airflow \
  -v /path/to/config/airflow/airflow.cfg:/opt/airflow/airflow.cfg \
  -v /path/to/config/airflow/dags:/opt/airflow/dags/ \
  -v /path/to/config/airflow/scripts:/opt/airflow/scripts/ \
  apache/airflow:latest-python3.11 standalone

  # Init DB
  docker exec -it dx-airflow airflow db migrate

  # Attach bridge network
  docker network connect bridge dx-airflow
  ```
- **Validation Command:**
  Access Airflow at `http://dx-worker3:8082`

---

### 4.7 Gravitino

- **Purpose:** Metadata and catalog federation across Iceberg, Hive, and Trino  
- **Version:** 0.7.0-incubating  
- **HOST VM:** dx-worker3
- **Config:** `gravitino.conf`  
- **Start Command:**
  ```bash
  # Create gravitino container
  docker run -d \
  --name dx-gravitino \
  --hostname dx-gravitino \
  --network dxhouse-net \
  -p 7070:7070 \
  -p 9001:9001 \
  -v /path/to/config/gravitino/conf:/root/gravitino/conf \
  -v /path/to/config/gravitino/catalogs:/root/gravitino/catalogs \
  -v /path/to/config/gravitino/libs:/root/gravitino/libs \
  apache/gravitino:0.7.0-incubating

  # Attach bridge network
  docker network connect bridge dx-gravitino
  ```
- **Validation Command:**
  ```bash
  curl http://dx-worker3:7070/
  ```

---

### 4.8 Superset

- **Purpose:** Data visualization and BI on top of Trino and Hive  
- **Version:** 5.0.0  
- **HOST VM:** dx-worker3
- **Setup Commands:**
  ```bash
  # Create Superset Container
  docker run -d \
  --name dx-superset \
  --network dxhouse-net \
  -p 9099:8088 \
  -e SUPERSET_SECRET_KEY="${SUPERSET_SECRET_KEY}" \
  apache/superset
  
  # configure user
  docker exec -it dx-superset superset fab create-admin \
     --username admin \
     --firstname Admin \
     --lastname User \
     --email admin@dxhouse.local \
     --password admin123
  
  # INIT DB
  docker exec -it dx-superset superset db upgrade
  docker exec -it dx-superset superset init
  
  # Attach bridge Network
  docker network connect bridge dx-superset
  ```
- **Access:** [http://dx-worker3:9099](http://dx-worker3:9099)

---

## 5. Verification & Testing

| Service | Verification Command | Expected Result |
|----------|---------------------|-----------------|
| HDFS | `hdfs dfsadmin -report` | Shows live datanodes |
| YARN | `yarn node -list` | Shows worker nodes |
| Sqoop | `sqoop eval --connect "jdbc:mysql://dx-database:3306/tpch" --username hive --password ${HIVE_DB_PASSWORD} --query "SELECT * FROM nation LIMIT 5"` | Shows query results |
| Hive | `hive -e "SHOW DATABASES;"` | Lists default and user DBs |
| Spark | `spark-sql` | Opens Editor |
| Ranger | Web UI login | Success |
| Gravitino | Web UI login | Success |
| Hue | Login page loads | Success |
| Airflow | Login page loads | Success |
| Trino | `trino --execute "SHOW CATALOGS;"` | Lists catalogs |
| Superset | Login page loads | Success |

---

## 6. Troubleshooting

- **Network not found: dxhouse-net:** Docker overlay network missing
    ```bash
    # Create the overlay network
    docker swarm init --advertise-addr 192.168.2.100
    docker network create --driver overlay --attachable dxhouse-net
    ```
- **Permission denied when writing logs:** Wrong ownership 
    ```bash
    chown -R hadoop:hadoop /dxhouse/$PATH$
    ```
- **Hive not connecting to MySQL:** JDBC config issue
    ```bash
    # Verify hive-site.xml DB URL and the MySQL JAR File
    ```
- **Overlay Network Issue:** VM Got crashed
    ```bash 
    # Check swarm network 
    docker info | grep "Swarm"
    docker network ls
    # Refresh the overlay connection 
    docker swarm leave --force # (worker)
    docker node ls # (master)
    docker node rm worker-name # (master)
    docker swarm join-token worker # (master)
    # copy the results from master and apply e.g docker swarm join --token SWMTKN-1-xxxxx 192.168.2.100:2377 (worker)
    # Recreate the docker containers on this machine
    ```

---

## 7. Maintenance

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

## 8. Appendix

### Version Matrix
| Component | Version |
|------------|----------|
| Hadoop | 3.3.6 |
| YARN | 3.3.6 |
| Hive | 3.1.3 |
| Spark | 3.4.2 |
| Iceberg | 1.3.1 |
| Ranger | 2.7.0 |
| Hue | 4.11 |
| Trino | 477 |
| Airflow | 3.0.6 |
| Gravitino | 0.7.0 |
| Superset | 5.0.0 |

### Network Diagram
You can visualize your cluster using [draw.io](https://app.diagrams.net) or embed an image like:

```
dx-master
 ├── HDFS NameNode
 ├── YARN ResourceManager
 ├── Hive Metastore
 └── Spark Master

 dx-worker1, dx-worker2, dx-worker3
 ├── HDFS DataNode
 ├── YARN NodeManager
 └── Spark Worker

 dx-worker3 (Admin)
 ├── Database (MySQL)
 ├── Hue
 ├── Trino
 ├── Airflow
 ├── Gravitino 
 ├── Ranger
 └── Superset
```

### References
- [Apache Hadoop](https://hadoop.apache.org/)
- [Apache Spark](https://spark.apache.org/)
- [Apache Hive](https://hive.apache.org/)
- [Trino Docs](https://trino.io/docs.html)
- [Apache Airflow](https://airflow.apache.org/)
- [Apache Superset](https://superset.apache.org/)

---
© 2025 Mahmoud Hamam Mekled. All rights reserved.
