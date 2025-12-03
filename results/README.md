# DX House Experimental Results

This directory contains performance data from the TPC-H benchmark evaluation (Scale Factor = 10) conducted on a 4-node cluster.

## Files

### 1. ingestion-throughput.csv
**Description**: Batch ingestion performance using Apache Sqoop  
**Metrics**: Data size, mapper count, throughput (MB/s), rows per second  
**Tables**: 8 TPC-H tables (customer, lineitem, nation, orders, part, partsupp, region, supplier)

**Key Findings**:
- Throughput range: 0.04 - 15.4 MB/s
- Lineitem (largest table): 15.4 MB/s with 6 mappers
- Parallel processing with 1-6 mappers depending on table size

### 2. storage-efficiency.csv
**Description**: Storage compression comparison between Parquet and Iceberg formats  
**Metrics**: Row count, raw Parquet size, Iceberg size, efficiency gain percentage  
**Tables**: 4 representative tables

**Key Findings**:
- Efficiency gains: 173% - 255%
- Best compression: partsupp (255% gain)
- Average improvement: ~215%

### 3. query-latency.csv
**Description**: Query performance comparison between Hive and Trino engines  
**Metrics**: Query complexity, execution time (seconds), speedup factor  
**Queries**: 5 TPC-H queries (Q1-Q5) with varying complexity

**Key Findings**:
- Consistent speedup: 7.6x across all queries
- Simple queries: 15s → 2s (Hive → Trino)
- Complex joins: 1207s → 159s (20 min → 2.6 min)

## Cluster Configuration

**Hardware**:
- 4 nodes (1 master + 3 workers)
- 5 CPU cores per node
- 8-18 GB RAM per node
- 100-200 GB disk per node

**Software Stack**:
- Hadoop 3.3.6
- Hive 3.1.3
- Spark 3.4.2
- Trino 477
- Apache Iceberg 1.3.1
- Apache Sqoop 1.4.7

## Reproducibility

All experiments can be reproduced using:
1. TPC-H dbgen utility (Scale Factor = 10)
2. Docker-based cluster deployment (see INSTALLATION.md)
3. Airflow DAGs for automated pipeline execution
4. SQL queries in `../data/tpch/queries/`

## Citation

If you use this data, please cite:

```bibtex
@article{mekled2024dxhouse,
  title={Data-X-House: A Unified Lakehouse Architecture for On-Premise Big Data Platforms in Regulated Sectors},
  author={Mekled, Mahmoud Hamam and Hassanein, Ehab Ezzat and Mohy, Noha Nagy},
  journal={Journal of Big Data},
  year={2025},
  publisher={Springer Nature}
}
```

## Contact

For questions about the experimental setup or results:
- Mahmoud Hamam Mekled
- Cairo University, Egypt
- Email: [contact information]

---

**Last Updated**: 2025-01-03  
**Data Version**: 1.0  
**TPC-H Scale Factor**: 10
