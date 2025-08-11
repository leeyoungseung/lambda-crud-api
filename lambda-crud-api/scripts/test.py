#!/usr/bin/env python3
"""
Test runner script for Lambda CRUD API.
Provides comprehensive testing capabilities with different test suites.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Handles running different types of tests for the Lambda CRUD API."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the test runner.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.tests_dir = self.project_root / 'tests'
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """
        Run unit tests.
        
        Args:
            verbose: Enable verbose output
            coverage: Enable coverage reporting
            
        Returns:
            True if tests passed, False otherwise
        """
        print("🧪 Running unit tests...")
        
        cmd = [sys.executable, '-m', 'pytest']
        
        # Add test files
        test_files = [
            'test_validation.py',
            'test_dynamodb_client.py',
            'test_response_handler.py',
            'test_create_handler.py',
            'test_read_handler.py',
            'test_update_handler.py',
            'test_delete_handler.py'
        ]
        
        for test_file in test_files:
            test_path = self.tests_dir / test_file
            if test_path.exists():
                cmd.append(str(test_path))
        
        # Add options
        if verbose:
            cmd.append('-v')
        
        if coverage:
            cmd.extend(['--cov=shared', '--cov=lambdas', '--cov-report=html', '--cov-report=term'])
        
        return self._run_command(cmd)
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """
        Run integration tests.
        
        Args:
            verbose: Enable verbose output
            
        Returns:
            True if tests passed, False otherwise
        """
        print("🔗 Running integration tests...")
        
        cmd = [sys.executable, '-m', 'pytest', str(self.tests_dir / 'test_integration.py')]
        
        if verbose:
            cmd.append('-v')
        
        return self._run_command(cmd)
    
    def run_performance_tests(self, verbose: bool = False) -> bool:
        """
        Run performance tests using test data.
        
        Args:
            verbose: Enable verbose output
            
        Returns:
            True if tests passed, False otherwise
        """
        print("⚡ Running performance tests...")
        
        # Create a simple performance test
        performance_test = """
import pytest
import time
import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'tests'))
sys.path.append(str(project_root / 'shared'))

from test_data import get_performance_test_items
from validation import validate_item_data

def test_validation_performance():
    '''Test validation performance with large dataset.'''
    items = get_performance_test_items()
    
    start_time = time.time()
    
    for item in items:
        result = validate_item_data(item)
        assert result.is_valid
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\\nValidated {len(items)} items in {duration:.3f} seconds")
    print(f"Average: {duration/len(items)*1000:.2f} ms per item")
    
    # Performance assertion (should validate 100 items in under 1 second)
    assert duration < 1.0, f"Validation took too long: {duration:.3f}s"

if __name__ == "__main__":
    test_validation_performance()
"""
        
        # Write temporary performance test
        perf_test_path = self.tests_dir / 'temp_performance_test.py'
        with open(perf_test_path, 'w') as f:
            f.write(performance_test)
        
        try:
            cmd = [sys.executable, '-m', 'pytest', str(perf_test_path)]
            if verbose:
                cmd.append('-v')
            
            return self._run_command(cmd)
        finally:
            # Clean up temporary test file
            if perf_test_path.exists():
                perf_test_path.unlink()
    
    def run_all_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """
        Run all test suites.
        
        Args:
            verbose: Enable verbose output
            coverage: Enable coverage reporting
            
        Returns:
            True if all tests passed, False otherwise
        """
        print("🚀 Running all test suites...")
        
        success = True
        
        # Run unit tests
        if not self.run_unit_tests(verbose, coverage):
            success = False
        
        # Run integration tests
        if not self.run_integration_tests(verbose):
            success = False
        
        # Run performance tests
        if not self.run_performance_tests(verbose):
            success = False
        
        return success
    
    def run_specific_test(self, test_file: str, verbose: bool = False) -> bool:
        """
        Run a specific test file.
        
        Args:
            test_file: Name of the test file
            verbose: Enable verbose output
            
        Returns:
            True if tests passed, False otherwise
        """
        print(f"🎯 Running specific test: {test_file}")
        
        test_path = self.tests_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_path}")
            return False
        
        cmd = [sys.executable, '-m', 'pytest', str(test_path)]
        if verbose:
            cmd.append('-v')
        
        return self._run_command(cmd)
    
    def generate_test_data(self) -> bool:
        """Generate test data files."""
        print("📊 Generating test data...")
        
        try:
            # Import and run test data generator
            sys.path.append(str(self.tests_dir))
            from test_data import TestDataGenerator
            
            output_dir = self.project_root / 'test_data_output'
            TestDataGenerator.save_test_data_to_files(str(output_dir))
            
            print(f"✅ Test data generated in {output_dir}")
            return True
        except Exception as e:
            print(f"❌ Failed to generate test data: {e}")
            return False
    
    def lint_code(self) -> bool:
        """Run code linting."""
        print("🔍 Running code linting...")
        
        # Check if flake8 is available
        try:
            cmd = [sys.executable, '-m', 'flake8', 'shared/', 'lambdas/', 'tests/', '--max-line-length=100']
            return self._run_command(cmd)
        except FileNotFoundError:
            print("⚠️  flake8 not found, skipping linting")
            return True
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        print("📦 Checking dependencies...")
        
        required_packages = ['pytest', 'boto3', 'moto']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing required packages: {', '.join(missing_packages)}")
            print("Install them with: pip install " + ' '.join(missing_packages))
            return False
        
        print("✅ All required dependencies are installed")
        return True
    
    def _run_command(self, cmd: List[str]) -> bool:
        """
        Run a command and return success status.
        
        Args:
            cmd: Command to run
            
        Returns:
            True if command succeeded, False otherwise
        """
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed with exit code {e.returncode}")
            return False
        except FileNotFoundError:
            print(f"❌ Command not found: {cmd[0]}")
            return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run tests for Lambda CRUD API')
    parser.add_argument(
        '--type', '-t',
        choices=['unit', 'integration', 'performance', 'all'],
        default='all',
        help='Type of tests to run'
    )
    parser.add_argument(
        '--file', '-f',
        help='Run specific test file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Enable coverage reporting (unit tests only)'
    )
    parser.add_argument(
        '--generate-data',
        action='store_true',
        help='Generate test data files'
    )
    parser.add_argument(
        '--lint',
        action='store_true',
        help='Run code linting'
    )
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies'
    )
    
    args = parser.parse_args()
    
    print("🧪 Lambda CRUD API Test Runner")
    print("-" * 40)
    
    runner = TestRunner()
    success = True
    
    try:
        # Check dependencies first
        if args.check_deps or args.type != 'none':
            if not runner.check_dependencies():
                sys.exit(1)
        
        # Generate test data
        if args.generate_data:
            if not runner.generate_test_data():
                success = False
        
        # Run linting
        if args.lint:
            if not runner.lint_code():
                success = False
        
        # Run specific test file
        if args.file:
            if not runner.run_specific_test(args.file, args.verbose):
                success = False
        
        # Run test suites
        elif args.type == 'unit':
            if not runner.run_unit_tests(args.verbose, args.coverage):
                success = False
        elif args.type == 'integration':
            if not runner.run_integration_tests(args.verbose):
                success = False
        elif args.type == 'performance':
            if not runner.run_performance_tests(args.verbose):
                success = False
        elif args.type == 'all':
            if not runner.run_all_tests(args.verbose, args.coverage):
                success = False
        
        if success:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()