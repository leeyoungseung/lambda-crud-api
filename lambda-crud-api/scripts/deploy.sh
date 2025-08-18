#!/bin/bash

# Lambda CRUD API Deployment Script
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform"

# Default values
ENVIRONMENT="dev"
AWS_REGION="ap-northeast-1"
SKIP_TESTS=false
DESTROY=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Lambda CRUD API infrastructure and functions.

OPTIONS:
    -e, --environment ENV    Environment to deploy (dev|staging|prod) [default: dev]
    -r, --region REGION      AWS region [default: ap-northeast-1]
    -t, --skip-tests         Skip running tests before deployment
    -d, --destroy           Destroy infrastructure instead of deploying
    -h, --help              Show this help message

EXAMPLES:
    $0                      # Deploy to dev environment
    $0 -e prod -r us-east-1 # Deploy to prod in us-east-1
    $0 -d                   # Destroy dev environment
    $0 --skip-tests         # Deploy without running tests

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -t|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -d|--destroy)
            DESTROY=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod."
    exit 1
fi

print_status "Starting deployment for environment: $ENVIRONMENT in region: $AWS_REGION"

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed and configured
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured or invalid."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        print_warning "Skipping tests as requested"
        return 0
    fi
    
    print_status "Running tests..."
    cd "$PROJECT_ROOT"
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    if [[ -f "requirements.txt" ]]; then
        print_status "Installing dependencies..."
        pip install -r requirements.txt
    fi
    
    # Install test dependencies
    pip install pytest pytest-cov moto[dynamodb] boto3
    
    # Run tests
    if [[ -d "tests" ]]; then
        print_status "Running unit tests..."
        python -m pytest tests/ -v --cov=shared --cov=lambdas --cov-report=term-missing
        
        if [[ $? -ne 0 ]]; then
            print_error "Tests failed. Deployment aborted."
            exit 1
        fi
        print_success "All tests passed"
    else
        print_warning "No tests directory found, skipping tests"
    fi
    
    deactivate
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure..."
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Create workspace if it doesn't exist
    if ! terraform workspace list | grep -q "$ENVIRONMENT"; then
        print_status "Creating Terraform workspace: $ENVIRONMENT"
        terraform workspace new "$ENVIRONMENT"
    else
        print_status "Selecting Terraform workspace: $ENVIRONMENT"
        terraform workspace select "$ENVIRONMENT"
    fi
    
    # Plan deployment
    print_status "Planning deployment..."
    terraform plan \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$AWS_REGION" \
        -out="tfplan"
    
    # Apply deployment
    print_status "Applying deployment..."
    terraform apply "tfplan"
    
    # Clean up plan file
    rm -f tfplan
    
    print_success "Infrastructure deployment completed"
    
    # Show outputs
    print_status "Deployment outputs:"
    terraform output
}

# Destroy infrastructure
destroy_infrastructure() {
    print_warning "This will destroy all infrastructure for environment: $ENVIRONMENT"
    read -p "Are you sure you want to continue? (yes/no): " -r
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Destruction cancelled"
        exit 0
    fi
    
    print_status "Destroying infrastructure..."
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    terraform init
    
    # Select workspace
    if terraform workspace list | grep -q "$ENVIRONMENT"; then
        terraform workspace select "$ENVIRONMENT"
    else
        print_error "Workspace $ENVIRONMENT does not exist"
        exit 1
    fi
    
    # Destroy infrastructure
    terraform destroy \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$AWS_REGION" \
        -auto-approve
    
    print_success "Infrastructure destroyed"
}

# Main execution
main() {
    check_prerequisites
    
    if [[ "$DESTROY" == "true" ]]; then
        destroy_infrastructure
    else
        run_tests
        deploy_infrastructure
        
        print_success "Deployment completed successfully!"
        print_status "API Gateway URL will be shown in the Terraform outputs above"
        print_status "You can test the API endpoints using the examples in the docs/ directory"
    fi
}

# Run main function
main