## TPC-H Benchmark Queries

This directory contains the SQL queries used for performance evaluation in the DX House implementation.

### Query Overview

| Query | Complexity | Description | Hive (s) | Trino (s) | Speedup |
|-------|------------|-------------|----------|-----------|---------|
| Q1 | Low | Simple projection with LIMIT | 15.09 | 1.99 | 7.6x |
| Q2 | Low-Medium | Filter & projection | 37.42 | 4.93 | 7.6x |
| Q3 | Medium | Aggregation with GROUP BY | 215.18 | 28.35 | 7.6x |
| Q4 | Medium-High | Aggregation & sorting | 207.43 | 27.33 | 7.6x |
| Q5 | High | Multi-table JOIN & aggregation | 1206.74 | 159.20 | 7.6x |

### Usage

**With Hive**:
```bash
hive -f queries/q1.sql
```

**With Trino**:
```bash
trino --catalog hive --schema default --file queries/q1.sql
```

### Dataset

- **Benchmark**: TPC-H
- **Scale Factor**: 10 (10 GB dataset)
- **Tables**: customer, lineitem, nation, orders, part, partsupp, region, supplier

### Generating TPC-H Data

```bash
# Download TPC-H dbgen
git clone https://github.com/electrum/tpch-dbgen.git
cd tpch-dbgen

# Compile
make

# Generate data (Scale Factor = 10)
./dbgen -s 10

# This creates .tbl files that can be loaded into the database
```

### Performance Notes

- All queries tested on 4-node cluster (1 master + 3 workers)
- Consistent 7.6x speedup with Trino vs Hive
- Results demonstrate query engine optimization benefits
- Iceberg table format used for all tables

---

**Last Updated**: 2025-01-03
