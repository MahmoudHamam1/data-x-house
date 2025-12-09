# Contributing to DX House

We welcome contributions to the DX House project! This document provides guidelines for contributing.

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use the issue template when creating new issues
3. Provide detailed information including:
   - Environment details (OS, Docker version)
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs and error messages

### Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our coding standards
4. **Test your changes** thoroughly
5. **Commit with clear messages**: Follow conventional commit format
6. **Submit a pull request**

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/MahmoudHamam1/data-x-house.git
   cd data-x-house
   ```

2. Review configuration files:
   ```bash
   # Configuration files use environment variables
   # Check config/ directory for service configurations
   ls config/
   ```

3. Build and test:
   ```bash
   cd docker
   docker build -t dxhouse-cls:latest -f Dockerfile .
   ./scripts/setup-cluster.sh master
   ```

## Coding Standards

### Configuration Files
- Use environment variables for sensitive data
- Follow existing naming conventions
- Document all configuration parameters

### Documentation
- Update relevant documentation for any changes
- Use clear, concise language
- Include examples where appropriate

### Docker Images
- Optimize for size and security
- Use multi-stage builds when appropriate
- Pin specific versions for dependencies

## Testing

### Before Submitting
- Test on clean environment
- Verify all services start correctly
- Run integration tests if available
- Check documentation accuracy

### Test Environment
- Minimum 4 nodes (1 master + 3 workers)
- 8GB RAM per node
- CentOS 7 or RHEL 7 compatible

## Code Review Process

1. All submissions require review
2. Maintainers will review within 48 hours
3. Address feedback promptly
4. Squash commits before merge

## Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Follow the code of conduct

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Contact

- **Primary Maintainer**: Mahmoud Hamam Mekled
- **Email**: [mahmoudhamam710@gmail.com](mailto:mahmoudhamam710@gmail.com)
- **Issues**: Use GitHub Issues for bug reports and feature requests

---

Thank you for contributing to DX House!