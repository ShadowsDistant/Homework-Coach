#!/bin/bash
# Quick start guide for Homework Coach

set -e

echo "🎓 Homework Coach - Quick Start"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI required"; exit 1; }

echo "✓ Python $(python3 --version)"
echo "✓ AWS CLI $(aws --version)"
echo ""

# Run tests
echo "Running unit tests..."
cd tests
python3 -m unittest test_algorithms.py -v 2>&1 | head -20
cd ..
echo ""

# Build Lambda package
echo "Building Lambda deployment package..."
cd lambda
chmod +x build.sh
./build.sh >/dev/null 2>&1
cd ..
echo "✓ Package ready: lambda/homework-coach-lambda.zip"
echo ""

# Show next steps
echo "📋 Next Steps:"
echo ""
echo "1. Set up AWS infrastructure:"
echo "   - Read: docs/DEPLOYMENT.md"
echo "   - Run: AWS CLI commands in DEPLOYMENT.md"
echo ""
echo "2. Deploy Lambda function:"
echo "   cd lambda && bash build.sh"
echo ""
echo "3. Import into Alexa Developer Console:"
echo "   - Create new skill"
echo "   - Import: homework-coach-skill.zip"
echo "   - Configure Lambda ARN endpoint"
echo ""
echo "4. Test on device:"
echo "   - Enable skill on Echo device"
echo "   - Say: 'Alexa, open Homework Coach'"
echo ""
echo "📚 Full documentation in docs/ directory"
echo ""
