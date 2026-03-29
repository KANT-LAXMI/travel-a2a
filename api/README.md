# Vercel Serverless API

This directory contains the entry point for Vercel serverless deployment.

## Structure

- `index.py` - Main entry point that Vercel calls
- `requirements.txt` - Dependencies for the serverless function

## How It Works

Vercel detects `api/index.py` and creates a serverless function that:
1. Imports your Flask app from `backend/api/app.py`
2. Handles HTTP requests
3. Returns responses

## Local Testing

```bash
cd ..
python api/index.py
```

## Deployment

Vercel automatically deploys this when you run:
```bash
vercel --prod
```

## Environment Variables

All environment variables must be set in Vercel Dashboard or via CLI.
See `DEPLOYMENT.md` for the complete list.
