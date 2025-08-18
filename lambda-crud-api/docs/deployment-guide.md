# Deployment Guide

This guide provides detailed instructions for deploying the Lambda CRUD API to AWS.

## Prerequisites

Before deploying, ensure you have the following tools installed and configured:

### Required Tools

1. **AWS CLI** (version 2.x recommended)
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   
   # Verify installation
   aws --version
   ```

2. **Terraform** (version 1.3.0 or later)
   ```bash
   # Download and install Terraform
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   
   # Verify installation
   terraform --version
   ```

3. **Python 3.12**
   ```bash
   # Install Python 3.12
   sudo apt update
   sudo apt install python3.12 python3.12-venv python3.12-pip
   
   # Verify installation
   python3.12 --version
   ```

4. **curl** (for API testing)
   ```bash
   # Install curl
   sudo apt install curl
   
   # Verify installation
   curl --version
   ```

### AWS Configuration

1. **Configure AWS Credentials**
   ```bash
   aws configure
   ```
   
   You'll be prompted to enter:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region name (e.g., `ap-northeast-1`)
   - Default output format (recommend `json`)

2. **Verify AWS Configuration**
   ```bash
   aws sts get-caller-identity
   ```
   
   This should return your AWS account information.

### Required AWS Permissions

Your AWS user/role needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:*",
        "lambda:*",
        "apigateway:*",
        "iam:*",
        "logs:*",
        "s3:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Note:** For production deployments, use more restrictive permissions following the principle of least privilege.

## Deployment Steps

### Step 1: Clone and Prepare the Project

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd lambda-crud-api

# Make deployment scripts executable
chmod +x scripts/deploy.sh
chmod +x scripts/test-api.sh
```

### Step 2: Configure Deployment Variables

Edit the `infrastructure/terraform/terraform.tfvars` file to customize your deployment:

```hcl
# Project configuration
project_name = "lambda-crud-api"
environment  = "dev"  # Change to "staging" or "prod" as needed
aws_region   = "ap-northeast-1"  # Change to your preferred region

# DynamoDB configuration
table_name = "items"

# Lambda configuration
lambda_runtime     = "python3.12"
lambda_timeout     = 30
lambda_memory_size = 256

# Logging configuration
log_retention_days = 14

# Additional tags
extra_tags = {
  Owner       = "your-team"
  Application = "crud-api"
  CostCenter  = "engineering"
}
```

### Step 3: Deploy the Infrastructure

#### Option 1: Automated Deployment (Recommended)

```bash
# Deploy to dev environment (default)
./scripts/deploy.sh

# Deploy to specific environment
./scripts/deploy.sh -e staging -r us-east-1

# Deploy without running tests (faster, but not recommended)
./scripts/deploy.sh --skip-tests
```

#### Option 2: Manual Deployment

```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Create workspace for environment
terraform workspace new dev  # or staging/prod

# Plan the deployment
terraform plan -var="environment=dev" -var="aws_region=ap-northeast-1"

# Apply the deployment
terraform apply -var="environment=dev" -var="aws_region=ap-northeast-1"
```

### Step 4: Verify Deployment

After successful deployment, Terraform will output important information:

```
Outputs:

dynamodb_table_name = "items-dev"
lambda_function_arns = {
  "create" = "arn:aws:lambda:ap-northeast-1:123456789012:function:crud-api-create-dev"
  "delete" = "arn:aws:lambda:ap-northeast-1:123456789012:function:crud-api-delete-dev"
  "read" = "arn:aws:lambda:ap-northeast-1:123456789012:function:crud-api-read-dev"
  "update" = "arn:aws:lambda:ap-northeast-1:123456789012:function:crud-api-update-dev"
}
lambda_function_names = {
  "create" = "crud-api-create-dev"
  "delete" = "crud-api-delete-dev"
  "read" = "crud-api-read-dev"
  "update" = "crud-api-update-dev"
}
rest_api_execution_arn = "arn:aws:execute-api:ap-northeast-1:123456789012:abc123def4"
rest_api_id = "abc123def4"
rest_api_invoke_url = "https://abc123def4.execute-api.ap-northeast-1.amazonaws.com/dev"
```

### Step 5: Test the API

Use the provided test script to verify all endpoints are working:

```bash
# Test the API using the invoke URL from Terraform outputs
./scripts/test-api.sh -u https://abc123def4.execute-api.ap-northeast-1.amazonaws.com/dev
```

## Environment-Specific Deployments

### Development Environment

```bash
# Deploy to dev
./scripts/deploy.sh -e dev

# Use relaxed settings for development
# - Shorter log retention
# - Lower memory allocation
# - More permissive error handling
```

### Staging Environment

```bash
# Deploy to staging
./scripts/deploy.sh -e staging

# Staging should mirror production settings
# - Same memory allocation as prod
# - Same timeout settings
# - Production-like data volumes for testing
```

### Production Environment

```bash
# Deploy to production
./scripts/deploy.sh -e prod -r us-east-1

# Production considerations:
# - Use appropriate AWS region for your users
# - Enable detailed monitoring
# - Set up proper backup strategies
# - Configure alerts and monitoring
```

## Multi-Region Deployment

To deploy to multiple regions:

```bash
# Deploy to primary region
./scripts/deploy.sh -e prod -r us-east-1

# Deploy to secondary region
./scripts/deploy.sh -e prod -r eu-west-1

# Deploy to Asia-Pacific region
./scripts/deploy.sh -e prod -r ap-northeast-1
```

## Monitoring and Logging

### CloudWatch Logs

After deployment, you can view logs in AWS CloudWatch:

1. **Lambda Function Logs:**
   - `/aws/lambda/crud-api-create-{environment}`
   - `/aws/lambda/crud-api-read-{environment}`
   - `/aws/lambda/crud-api-update-{environment}`
   - `/aws/lambda/crud-api-delete-{environment}`

2. **API Gateway Logs:**
   - `/aws/apigw/crud-rest-api-{environment}`

### Viewing Logs

```bash
# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/crud-api"

# Tail Lambda logs
aws logs tail /aws/lambda/crud-api-create-dev --follow

# View API Gateway logs
aws logs tail /aws/apigw/crud-rest-api-dev --follow
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Verify IAM permissions
   aws iam get-user
   ```

2. **Terraform State Issues**
   ```bash
   # List Terraform workspaces
   terraform workspace list
   
   # Switch to correct workspace
   terraform workspace select dev
   
   # Refresh state
   terraform refresh
   ```

3. **Lambda Function Errors**
   ```bash
   # Check Lambda function logs
   aws logs tail /aws/lambda/crud-api-create-dev --since 1h
   
   # Test Lambda function directly
   aws lambda invoke \
     --function-name crud-api-create-dev \
     --payload '{"httpMethod":"POST","body":"{}"}' \
     response.json
   ```

4. **API Gateway Issues**
   ```bash
   # Check API Gateway deployment
   aws apigateway get-deployments --rest-api-id YOUR_API_ID
   
   # Test API Gateway directly
   curl -v https://YOUR_API_ID.execute-api.REGION.amazonaws.com/STAGE/items
   ```

### Debug Mode

Enable debug mode for more verbose output:

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG
./scripts/deploy.sh

# Enable AWS CLI debug logging
aws --debug sts get-caller-identity
```

## Updating the Deployment

### Code Updates

When you update Lambda function code:

```bash
# Redeploy with updated code
./scripts/deploy.sh -e dev

# Terraform will detect changes and update only the affected resources
```

### Infrastructure Updates

When you modify Terraform configuration:

```bash
# Plan the changes
cd infrastructure/terraform
terraform plan -var="environment=dev"

# Apply the changes
terraform apply -var="environment=dev"
```

## Rollback Procedures

### Rolling Back Code Changes

```bash
# Revert to previous Git commit
git revert HEAD

# Redeploy
./scripts/deploy.sh -e dev
```

### Rolling Back Infrastructure Changes

```bash
# Use Terraform state to rollback
cd infrastructure/terraform

# Show previous state
terraform show

# Import previous configuration if needed
# This is complex and should be done carefully in production
```

## Cleanup and Destruction

### Destroying Infrastructure

```bash
# Destroy specific environment
./scripts/deploy.sh -e dev --destroy

# Manual destruction
cd infrastructure/terraform
terraform workspace select dev
terraform destroy -var="environment=dev" -var="aws_region=ap-northeast-1"
```

### Cleanup Checklist

Before destroying:

1. ✅ Backup any important data from DynamoDB
2. ✅ Export CloudWatch logs if needed
3. ✅ Verify no other resources depend on this infrastructure
4. ✅ Confirm with team members
5. ✅ Update DNS records if applicable

## Security Considerations

### Production Security

1. **API Gateway Security:**
   - Enable API keys for production
   - Set up rate limiting
   - Configure CORS properly
   - Use custom domain with SSL

2. **Lambda Security:**
   - Use least privilege IAM roles
   - Enable encryption at rest
   - Regularly update dependencies
   - Monitor for security vulnerabilities

3. **DynamoDB Security:**
   - Enable encryption at rest
   - Use VPC endpoints if needed
   - Set up proper backup strategies
   - Monitor access patterns

### Example Production Security Configuration

```hcl
# Add to terraform.tfvars for production
extra_security_config = {
  enable_api_key        = true
  enable_waf           = true
  enable_vpc_endpoint  = true
  backup_retention     = 30
}
```

## Cost Optimization

### Cost Monitoring

1. **Set up billing alerts**
2. **Monitor Lambda invocation costs**
3. **Optimize DynamoDB read/write capacity**
4. **Review CloudWatch log retention**

### Cost-Saving Tips

1. **Use appropriate Lambda memory sizes**
2. **Set reasonable log retention periods**
3. **Use DynamoDB on-demand pricing for variable workloads**
4. **Clean up unused resources regularly**

## Support and Maintenance

### Regular Maintenance Tasks

1. **Update Lambda runtime versions**
2. **Review and rotate IAM credentials**
3. **Monitor CloudWatch metrics**
4. **Update Terraform and AWS provider versions**
5. **Review and update security groups**

### Getting Help

1. **Check CloudWatch logs first**
2. **Review Terraform plan output**
3. **Use AWS CLI for debugging**
4. **Consult AWS documentation**
5. **Check project documentation and examples**