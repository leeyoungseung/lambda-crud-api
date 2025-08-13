# Python Virtual Environment Setup Guide

This guide explains how to set up and use Python virtual environments for the Lambda CRUD API project in remote environments.

## Why Use Virtual Environments?

- **Isolation**: Keeps project dependencies separate from system Python
- **Consistency**: Ensures same package versions across different environments
- **Remote Compatibility**: Works reliably in remote/cloud environments
- **Dependency Management**: Prevents conflicts between different projects

## Quick Setup

### 1. Create Virtual Environment

```bash
# Navigate to project directory
cd lambda-crud-api

# Create virtual environment
python3 -m venv venv

# Verify creation
ls -la venv/
```

### 2. Activate Virtual Environment

```bash
# Activate (Linux/macOS/WSL)
source venv/bin/activate

# Verify activation (should show venv path)
which python
echo $VIRTUAL_ENV
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installations
pip list
python -c "import boto3; print('✅ boto3 ready')"
```

### 4. Deactivate (when done)

```bash
# Deactivate virtual environment
deactivate
```

## Daily Workflow

### Starting Work

```bash
cd lambda-crud-api
source venv/bin/activate
```

### Running Deployments

```bash
# Always ensure venv is active before deployment
source venv/bin/activate
./scripts/deploy.sh
```

### Finishing Work

```bash
deactivate
```

## Troubleshooting

### Virtual Environment Not Found

```bash
# If venv directory doesn't exist, create it
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependencies Not Found

```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Permission Issues

```bash
# If permission denied, check directory ownership
ls -la venv/
sudo chown -R $USER:$USER venv/
```

### Python Version Issues

```bash
# Check Python version
python --version

# If wrong version, recreate venv with specific Python
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Remote Environment Considerations

### SSH Sessions

```bash
# Add to ~/.bashrc or ~/.zshrc for auto-activation
echo 'cd ~/lambda-crud-api && source venv/bin/activate' >> ~/.bashrc
```

### Docker Containers

```bash
# In Dockerfile
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt
```

### CI/CD Pipelines

```yaml
# GitHub Actions example
- name: Setup Python Virtual Environment
  run: |
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
```

## Best Practices

1. **Always activate venv before working**
2. **Keep requirements.txt updated**
3. **Don't commit venv/ directory to git**
4. **Use specific package versions in requirements.txt**
5. **Test in clean virtual environment before deployment**

## Commands Reference

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Check virtual environment status
echo $VIRTUAL_ENV

# List installed packages
pip list

# Generate requirements file
pip freeze > requirements.txt

# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv
```