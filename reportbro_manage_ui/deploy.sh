#!/bin/bash

# Script to build and deploy the ReportBro UI

set -e  # Exit on error

echo "🏗️  Building UI..."
yarn build

echo ""
echo "📦 Copying built files to static directory..."
rm -rf ../reportbro_designer_api/static/ui/*
cp -r dist/* ../reportbro_designer_api/static/ui/

echo ""
echo "✅ UI deployed successfully!"
echo "📍 Location: ../reportbro_designer_api/static/ui/"
echo ""
echo "🌐 Access the UI at:"
echo "   - Legacy: http://localhost:7651/ui"
echo "   - Company: http://localhost:7651/ui/{company}"
