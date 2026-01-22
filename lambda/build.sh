#!/bin/bash
# Build and package the Lambda function for deployment

set -e

echo "Building Homework Coach Lambda package..."

# Navigate to lambda directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create build directory
BUILD_DIR="build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t "$BUILD_DIR"

# Copy source files
echo "Copying source files..."
cp lambda_function.py "$BUILD_DIR/"
cp -r handlers "$BUILD_DIR/"
cp -r helpers "$BUILD_DIR/"

# Create deployment zip
ZIP_FILE="homework-coach-lambda.zip"
echo "Creating deployment package: $ZIP_FILE"
cd "$BUILD_DIR"
zip -r "../$ZIP_FILE" . -q
cd ..

echo "✓ Deployment package created: $ZIP_FILE"
echo "Ready to upload to AWS Lambda!"
