# 🚀 Deploy Everything to Render.com (100% FREE)

This guide deploys your ENTIRE application (frontend + backend + all A2A agents) to Render.com for FREE.

## What Gets Deployed:

1. ✅ **Frontend** (React) - Static site
2. ✅ **Backend API** (Flask) - Web service
3. ✅ **Host Agent** - Orchestrator
4. ✅ **Budget Agent** - Budget planning
5. ✅ **Places Agent** - Itinerary planning
6. ✅ **Map Agent** - Map generation
7. ✅ **RAG Agent** - Knowledge retrieval

**Total: 7 services, all FREE!**

---

## Step 1: Push to GitHub

```bash
git add .
git commit -m "Add Render deployment config"
git push origin main
```

---

## Step 2: Sign Up on Render

1. Go to **https://render.com**
2. Click **"Get Started for Free"**
3. Sign up with GitHub (easiest)
4. No credit card required!

---

## Step 3: Deploy Using Blueprint

1. In Render dashboard, click **"New +"** → **"Blueprint"**
2. Connect your GitHub repository
3. Select your repo from the list
4. Render will detect `render.yaml` automatically
5. Click **"Apply"**

Render will now create all 7 services automatically!

---

## Step 4: Add Environment Variables

After services are created, add these environment variables to each service:

### For ALL Agent Services (Host, Budget, Places, RAG):
```
AZURE_OPENAI_ENDPOINT=https://ria-azureopenai-dev-wus-001.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview
AZURE_OPENAI_API_KEY=FvORdZlkWrcYzTyFUjd8keIi2snZJJ6lHnoZoctKCHaPqQZdwkXaJQQJ99BFAC4f1cMXJ3w3AAABACOGEf4q
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### For Places Agent (additional):
```
SERPAPI_API_KEY=f57c329e024ddd4e45d10e98f2f75cb437b9ea8df7fdc7bf5d964c0174e788f7
```

### For Map Agent:
```
GOOGLE_API_KEY=AIzaSyD0IInjFVlOskQ5rOaZQjNHzp9zH6U7gOc
```

### For Backend API (travel-api):
```
DATABASE_URL=postgres://postgres.vculeoepillgzcycfozg:zwd12o9lKbO8Wiu8@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USER=ssingh@saxon.ai
EMAIL_PASSWORD=Love@papa01234
JWT_SECRET_KEY=QWERTY123456
JWT_REFRESH_SECRET_KEY=poiuyt09876
```

**Note:** HOST_AGENT_URL and CORS_ORIGINS are already set in render.yaml

---

## Step 5: Wait for Deployment

- Each service will build and deploy (takes 5-10 minutes)
- Watch the logs in Render dashboard
- All services should show "Live" status

---

## Step 6: Get Your URLs

After deployment, you'll have:

- **Frontend**: `https://travel-frontend.onrender.com` ← Your app URL!
- **API**: `https://travel-api.onrender.com`
- **Host Agent**: `https://travel-host-agent.onrender.com`
- **Budget Agent**: `https://travel-budget-agent.onrender.com`
- **Places Agent**: `https://travel-places-agent.onrender.com`
- **Map Agent**: `https://travel-map-agent.onrender.com`
- **RAG Agent**: `https://travel-rag-agent.onrender.com`

---

## Step 7: Update Agent Registry

The agents need to know each other's URLs. Update `backend/utilities/agent_registry.json`:

```json
{
  "agents": [
    {
      "name": "BudgetAgent",
      "url": "https://travel-budget-agent.onrender.com",
      "description": "Budget planning agent"
    },
    {
      "name": "PlacesAgent",
      "url": "https://travel-places-agent.onrender.com",
      "description": "Itinerary planning agent"
    },
    {
      "name": "MapAgent",
      "url": "https://travel-map-agent.onrender.com",
      "description": "Map generation agent"
    },
    {
      "name": "RAGAgent",
      "url": "https://travel-rag-agent.onrender.com",
      "description": "Knowledge retrieval agent"
    }
  ]
}
```

Then commit and push:
```bash
git add backend/utilities/agent_registry.json
git commit -m "Update agent URLs for Render"
git push
```

Render will auto-redeploy!

---

## Step 8: Test Your App

1. Go to `https://travel-frontend.onrender.com`
2. Sign up / Login
3. Try planning a trip!

**Note:** First request may take 30 seconds (free tier spins down after inactivity)

---

## 🎉 You're Done!

Your entire A2A multi-agent travel app is now running 100% FREE on Render!

---

## Free Tier Limits:

- ✅ 750 hours/month per service (enough for 1 service 24/7)
- ✅ Services spin down after 15 min inactivity
- ✅ First request after spin-down takes ~30 seconds
- ✅ No credit card required
- ✅ Unlimited bandwidth

---

## Troubleshooting:

### Services won't start?
- Check logs in Render dashboard
- Verify all environment variables are set
- Make sure requirements.txt has all dependencies

### Agents can't communicate?
- Update agent_registry.json with correct Render URLs
- Check HOST_AGENT_URL in backend API environment

### Frontend can't reach API?
- Check CORS_ORIGINS in backend API
- Verify VITE_API_URL in frontend/.env.production

---

## Alternative: Keep Frontend on Vercel

If you prefer Vercel for frontend:

1. Deploy only agents + API to Render
2. Keep frontend on Vercel
3. Update Vercel env: `VITE_API_URL=https://travel-api.onrender.com`
4. Update Render API env: `CORS_ORIGINS=https://your-app.vercel.app`

---

## Cost: $0/month 🎉

Everything runs free forever on Render!
