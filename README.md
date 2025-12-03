# DX House: Unified Data Management Architecture

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.XXXXXX-blue)](https://doi.org/10.5281/zenodo.XXXXXX)
[![Journal](https://img.shields.io/badge/Journal-Big%20Data-green)](https://journalofbigdata.springeropen.com/)

Implementation artifacts for **Data-X-House (DX House)**: A comprehensive, unified data management architecture that combines data lake and data warehouse capabilities for on-premise big data platforms in highly regulated sectors.

> **Associated Publication:**  
> Mekled, M.H. (2025). Data-X-House: A Novel Unified Data Management Architecture Based on DLAF. *Journal of Big Data* (Under Review).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Performance Benchmarks](#performance-benchmarks)
- [Documentation](#documentation)
- [Citation](#citation)
- [License](#license)
- [Contact](#contact)

---

## Overview

DX House addresses the critical challenge that only 14% of big data proof-of-concept projects successfully transition to production environments. This implementation provides:

- **Unified Architecture**: Seven-layer design combining data lake and warehouse capabilities
- **On-Premise Deployment**: Docker-based containerization for regulated sectors
- **DLAF Framework**: Extended Data Lake Architecture Framework (9→11 aspects)
- **Security & Governance**: Enterprise-level compliance (GDPR, HIPAA, PCI-DSS, SOX)
- **Production-Ready**: Validated with TPC-H benchmark on 4-node cluster

### Problem Statement

Traditional data architectures face significant limitations:
- **Data Warehouses**: Inflexible for unstructured data and advanced analytics
- **Data Lakes**: Governance challenges and limited transactional consistency
- **Hybrid Approaches**: Operational complexity and data redundancy
- **Cloud Lakehouses**: Unsuitable for highly regulated sectors with on-premise requirements

DX House provides a comprehensive solution that addresses these limitations while supporting both cloud and on-premise deployments.

---

## Architecture

DX House consists of **seven architectural layers**:

### Storage & Processing Layers (5)
1. **Ingestion Layer**: Batch, incremental, and streaming data ingestion
2. **Storage Layer**: Unified distributed storage (HDFS + Iceberg)
3. **Processing & Analysis Layer**: Data warehouse + sandbox for ML
4. **Archive Layer**: Cost-effective long-term storage
5. **Delivery Layer**: APIs, dashboards, and query interfaces

### Management Layers (2)
6. **Metadata Layer**: Technical, operational, and business metadata
7. **Security & Administration Layer**: Access control, encryption, monitoring

![DX House Architecture](docs/images/architecture-diagram.png)

### Data Pipeline Architecture

The implementation features a **three-layer data pipeline** orchestrated by Apache Airflow:

**Ingestion → Transformation → Delivery**

1. **Ingestion Layer**
   - Batch ingestion: 8 TPC-H tables via Apache Sqoop (MySQL → HDFS)
   - Incremental ingestion: Delta updates for high-velocity tables
   - Partitioned storage with Snappy compression

2. **Transformation Layer**
   - Star schema creation with Apache Spark + Iceberg
   - Fact table: `fact_sales` (partitioned by date)
   - Dimensions: customer, supplier, part, order, geography, time
   - Sandbox zone for ML/AI analytics

3. **Delivery Layer**
   - Business-specific data marts: sales by customer, region, time
   - Optimized for BI tools (Superset, Tableau)
   - ACID transactions and time travel via Iceberg

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Storage** | HDFS 3.3.6, Apache Hive 3.1.3, Apache Iceberg 1.3.1 |
| **Processing** | Apache Spark 3.4.2, Apache Tez 0.10.4 |
| **Ingestion** | Apache Sqoop 1.4.7, Apache Airflow 3.0.6 |
| **Security** | Apache Ranger 2.7.0, Hadoop KMS |
| **Metadata** | Apache Gravitino 0.7.0, Hive Metastore |
| **Query** | Trino 477, Hive 3.1.3 |
| **Visualization** | Apache Superset 5.0.0, Hue 4.11 |

---

## Key Features

### Security & Governance
- Encryption at rest (HDFS TDE + Hadoop KMS) and in transit (TLS/SSL)
- Fine-grained access control via Apache Ranger
- Comprehensive audit logging across all layers
- Dynamic data masking for sensitive information
- GDPR, HIPAA, PCI-DSS, SOX, ISO 27001 compliance

### Data Management
- Unified storage for structured, semi-structured, and unstructured data
- ACID transactions via Apache Iceberg
- Schema evolution and time travel capabilities
- Snapshot-based data versioning

### Performance
- Distributed processing with Spark + YARN
- Trino for interactive analytics (7.5x faster than Hive)
- 173%-255% storage efficiency gains with Iceberg
- Parallel ingestion with multi-mapper Sqoop

---

## Quick Start

### Prerequisites
```bash
# System Requirements
- Docker 20.10+
- 4 nodes (1 master + 3 workers)
- 8GB RAM per node minimum
- 100GB disk per node
- CentOS 7 or compatible Linux
```

### 1. Clone Repository
```bash
git clone https://github.com/[username]/data-x-house.git
cd data-x-house
```

### 2. Build Docker Image
```bash
cd docker
docker build -t dxhouse-cls:latest -f Dockerfile .
```

### 3. Deploy Cluster
```bash
# On master node
./scripts/setup-cluster.sh master

# On worker nodes
./scripts/setup-cluster.sh worker
```

### 4. Verify Installation
```bash
hdfs dfsadmin -report
yarn node -list
hive -e "SHOW DATABASES;"
```

---

## System Requirements

### Hardware Configuration

| Node | Role | CPU | RAM | Disk | OS |
|------|------|-----|-----|------|-----|
| dx-master | Master | 5 Cores | 12 GB | 200 GB | CentOS 7 |
| dx-worker1 | Worker | 5 Cores | 8 GB | 100 GB | CentOS 7 |
| dx-worker2 | Worker | 5 Cores | 8 GB | 100 GB | CentOS 7 |
| dx-worker3 | Admin | 5 Cores | 18 GB | 200 GB | CentOS 7 |

---

## Performance Benchmarks

### TPC-H Benchmark Results (Scale Factor = 10)

#### Ingestion Throughput

| Table | Size (MB) | Mappers | Throughput (MB/s) | Rows/sec |
|-------|-----------|---------|-------------------|----------|
| customer | 233 | 4 | 3.6 | 22,388 |
| lineitem | 7,413 | 6 | 15.4 | 116,478 |
| orders | 1,659 | 6 | 7.4 | 66,666 |
| partsupp | 1,147 | 4 | 10.8 | 74,766 |

#### Storage Efficiency

| Table | Parquet (MB) | Iceberg (MB) | Efficiency Gain |
|-------|--------------|--------------|-----------------|
| customer | 233 | 124.9 | 186.6% |
| part | 232 | 94.4 | 245.8% |
| partsupp | 1,147 | 449.9 | 255.0% |
| supplier | 13.5 | 7.8 | 173.1% |

#### Query Performance (Hive vs. Trino)

| Query | Description | Hive (s) | Trino (s) | Speedup |
|-------|-------------|----------|-----------|---------|
| Q1 | Simple projection | 15.09 | 1.99 | 7.6x |
| Q2 | Filter & projection | 37.42 | 4.93 | 7.6x |
| Q3 | Aggregation | 215.18 | 28.35 | 7.6x |
| Q4 | Aggregation & sorting | 207.43 | 27.33 | 7.6x |
| Q5 | Join & aggregation | 1,206.74 | 159.20 | 7.6x |

---

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)**: Complete setup instructions
- **[Configuration Guide](docs/CONFIGURATION.md)**: Detailed configuration
- **[User Guide](docs/USER_GUIDE.md)**: How to use DX House
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

---

## Citation

If you use DX House in your research, please cite:

```bibtex
@article{mekled2024dxhouse,
  title={Data-X-House: A Novel Unified Data Management Architecture Based on DLAF},
  author={Mekled, Mahmoud Hamam},
  journal={Journal of Big Data},
  year={2025},
  publisher={Springer Nature},
  note={Under Review}
}
```

---

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

---

## Contact

**Mahmoud Hamam Mekled**  
MSc Candidate, Information Systems  
Cairo University, Egypt

---

**⭐ If you find this project useful, please star this repository!**

*© 2024-2025 Mahmoud Hamam Mekled. All rights reserved.*
