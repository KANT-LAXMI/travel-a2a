# Vercel Deployment Script (PowerShell)
# ======================================
# Quick deployment script for Travel Buddy

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "🚀 Travel Buddy Deployment Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Check if DATABASE_URL is set
$DATABASE_URL = $env:DATABASE_URL
if (-not $DATABASE_URL) {
    Write-Host ""
    Write-Host "❌ DATABASE_URL not set!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please add to .env file:"
    Write-Host "DATABASE_URL=postgresql://user:password@host:port/dbname"
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "✅ DATABASE_URL is set" -ForegroundColor Green

# Test PostgreSQL connection
Write-Host ""
Write-Host "🧪 Testing PostgreSQL connection..." -ForegroundColor Yellow
python test_postgres_connection.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ PostgreSQL connection failed!" -ForegroundColor Red
    Write-Host "Fix the connection before deploying."
    exit 1
}

# Install frontend dependencies
Write-Host ""
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install

# Build frontend
Write-Host ""
Write-Host "🏗️  Building frontend..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed!" -ForegroundColor Red
    exit 1
}

Set-Location ..

# Deploy to Vercel
Write-Host ""
Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Choose deployment type:"
Write-Host "1) Preview deployment"
Write-Host "2) Production deployment"
$choice = Read-Host "Enter choice (1 or 2)"

if ($choice -eq "2") {
    vercel --prod
} else {
    vercel
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
