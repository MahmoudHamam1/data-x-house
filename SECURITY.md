# Security Notice

## Credentials and Sensitive Data

This repository contains **placeholder values** for all sensitive information. Before deployment, you must replace all placeholders with actual credentials.

### Environment Variables Used

The following environment variables are used throughout the configuration files for security:

- `${HIVE_DB_PASSWORD}` - Hive database password
- `${DB_ROOT_PASSWORD}` - MySQL root password
- `${RANGER_ADMIN_PASSWORD}` - Ranger admin password
- `${RANGER_TAGSYNC_PASSWORD}` - Ranger TagSync password
- `${RANGER_USERSYNC_PASSWORD}` - Ranger UserSync password
- `${RANGER_KEYADMIN_PASSWORD}` - Ranger KeyAdmin password
- `${RANGER_UNIX_PASSWORD}` - Ranger Unix user password
- `${RANGER_DB_PASSWORD}` - Ranger database password
- `${AIRFLOW_JWT_SECRET}` - Airflow JWT secret key
- `${HUE_SECRET_KEY}` - Hue application secret key
- `${KMS_KEYSTORE_PASSWORD}` - Hadoop KMS keystore password

### Files Requiring Credential Configuration

**Airflow Scripts**:
- `config/airflow/scripts/ingestion/batch/*.sh`
- `config/airflow/scripts/ingestion/incremental/*.sh`
- `config/airflow/scripts/bin/conn_setup.sh`
- `config/airflow/dags/*.py`

**Before Running**:
1. Set all required environment variables with secure values
2. Never use default or weak passwords
3. Use strong, unique passwords for each service
4. Consider using a secrets management system

**Example Environment Setup**:
```bash
export HIVE_DB_PASSWORD="your_secure_hive_password"
export DB_ROOT_PASSWORD="your_secure_root_password"
export RANGER_ADMIN_PASSWORD="your_secure_ranger_admin_password"
export RANGER_TAGSYNC_PASSWORD="your_secure_ranger_tagsync_password"
export RANGER_USERSYNC_PASSWORD="your_secure_ranger_usersync_password"
export RANGER_KEYADMIN_PASSWORD="your_secure_ranger_keyadmin_password"
export RANGER_UNIX_PASSWORD="your_secure_ranger_unix_password"
export RANGER_DB_PASSWORD="your_secure_ranger_db_password"
export AIRFLOW_JWT_SECRET="your_secure_airflow_jwt_secret"
export HUE_SECRET_KEY="your_secure_hue_secret_key"
export KMS_KEYSTORE_PASSWORD="your_secure_kms_keystore_password"
```

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
- **Email**: [mahmoudhamam710@gmail.com](mailto:mahmoudhamam710@gmail.com)
- **GitHub**: Create a private security advisory
- **Academic**: [11422020425998@pg.cu.edu.eg](mailto:11422020425998@pg.cu.edu.eg)

**Do not** create public issues for security vulnerabilities.

---

**Last Updated**: December 1, 2025
**Version**: 1.0
