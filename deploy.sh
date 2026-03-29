#!/bin/bash

# Vercel Deployment Script
# ========================
# Quick deployment script for Travel Buddy

echo "=================================="
echo "🚀 Travel Buddy Deployment Script"
echo "=================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo ""
    echo "❌ DATABASE_URL not set!"
    echo ""
    echo "Please add to .env file:"
    echo "DATABASE_URL=postgresql://user:password@host:port/dbname"
    echo ""
    exit 1
fi

echo ""
echo "✅ DATABASE_URL is set"

# Test PostgreSQL connection
echo ""
echo "🧪 Testing PostgreSQL connection..."
python test_postgres_connection.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ PostgreSQL connection failed!"
    echo "Fix the connection before deploying."
    exit 1
fi

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

# Build frontend
echo ""
echo "🏗️  Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

cd ..

# Deploy to Vercel
echo ""
echo "🚀 Deploying to Vercel..."
echo ""
echo "Choose deployment type:"
echo "1) Preview deployment"
echo "2) Production deployment"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "2" ]; then
    vercel --prod
else
    vercel
fi

echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo "=================================="
