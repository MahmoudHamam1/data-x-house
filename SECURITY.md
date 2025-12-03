# Security Notice

## Credentials and Sensitive Data

This repository contains **placeholder values** for all sensitive information. Before deployment, you must replace all placeholders with actual credentials.

### Placeholders Used

The following placeholders are used throughout the configuration files:

- `<HIVE_PASSWORD>` - Hive database password
- `<HADOOP_PASSWORD>` - Hadoop user password  
- `<ROOT_PASSWORD>` - MySQL root password
- `<RANGER_PASSWORD>` - Apache Ranger admin password

### Files Requiring Credential Configuration

**Airflow Scripts**:
- `config/airflow/scripts/ingestion/batch/*.sh`
- `config/airflow/scripts/ingestion/incremental/*.sh`
- `config/airflow/scripts/bin/conn_setup.sh`
- `config/airflow/dags/*.py`

**Before Running**:
1. Replace all `<HIVE_PASSWORD>` with your actual Hive password
2. Replace all `<HADOOP_PASSWORD>` with your actual Hadoop password
3. Replace all `<ROOT_PASSWORD>` with your actual MySQL root password
4. Replace all `<RANGER_PASSWORD>` with your actual Ranger admin password

### Security Best Practices

1. **Never commit real credentials** to version control
2. **Use environment variables** for sensitive data
3. **Enable encryption** at rest and in transit
4. **Change default passwords** immediately after installation
5. **Implement least privilege** access control
6. **Enable audit logging** for all services
7. **Regular security updates** for all components

### Reporting Security Issues

If you discover a security vulnerability, please report it to:
- Create a private security advisory on GitHub
- Or contact the repository maintainers directly

**Do not** create public issues for security vulnerabilities.

---

**Last Updated**: 2025-01-03  
**Version**: 1.0
