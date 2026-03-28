#!/bin/bash
# Start all agents in background and then start the API

echo "Starting all agents..."

# Start agents in background
python -m backend.agents.budget_agent &
python -m backend.agents.places_agent &
python -m backend.agents.map_agent &
python -m backend.agents.rag_agent &
python -m backend.agents.host_agent.entry &

# Wait for agents to start
sleep 10

# Start API server
echo "Starting API server..."
gunicorn -w 4 -b 0.0.0.0:$PORT backend.api.app:app
