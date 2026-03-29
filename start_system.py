"""
System Startup Script
=====================
Starts all agents and the Flask backend in sequence
Activates virtual environment before starting services
"""

import subprocess
import time
import sys
import os
import signal
from typing import List, Dict
from pathlib import Path

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Detect virtual environment
def get_venv_python():
    """Get the Python executable from venv"""
    venv_paths = [
        'venv/Scripts/python.exe',  # Windows
        'venv/bin/python',           # Linux/Mac
        '.venv/Scripts/python.exe',  # Windows (.venv)
        '.venv/bin/python',          # Linux/Mac (.venv)
    ]
    
    for venv_path in venv_paths:
        if os.path.exists(venv_path):
            return venv_path
    
    # Fallback to system python
    return 'python'

# Get Python executable
PYTHON_EXE = get_venv_python()

# Agent configurations
# IMPORTANT: Child agents must start BEFORE Host Agent
# Host Agent discovers child agents during initialization
AGENTS = [
    {
        'name': 'Budget Agent',
        'command': [PYTHON_EXE, '-m', 'backend.agents.budget_agent'],
        'port': 10001,
        'wait_time': 2,
        'icon': '💰'
    },
    {
        'name': 'Places Agent',
        'command': [PYTHON_EXE, '-m', 'backend.agents.places_agent'],
        'port': 10002,
        'wait_time': 2,
        'icon': '📍'
    },
    {
        'name': 'Map Agent',
        'command': [PYTHON_EXE, '-m', 'backend.agents.map_agent'],
        'port': 10003,
        'wait_time': 2,
        'icon': '🗺️'
    },
    {
        'name': 'RAG Agent',
        'command': [PYTHON_EXE, '-m', 'backend.agents.rag_agent'],
        'port': 10004,
        'wait_time': 10,  # RAG Agent needs more time to load embedding model
        'icon': '📚'
    },
    {
        'name': 'Host Agent',
        'command': [PYTHON_EXE, '-m', 'backend.agents.host_agent.entry'],
        'port': 10000,
        'wait_time': 3,
        'icon': '🎯'
    }
]

# Flask backend configuration
BACKEND = {
    'name': 'Flask Backend',
    'command': [PYTHON_EXE, '-m', 'backend'],
    'port': 5000,
    'wait_time': 2,
    'icon': '🌐'
}

# Store process references
processes: List[subprocess.Popen] = []


def print_banner():
    """Print startup banner"""
    print("\n" + "="*70)
    print(f"{Colors.BOLD}{Colors.CYAN}✈️  ANYWHERE APP - SYSTEM STARTUP{Colors.END}")
    print("="*70)
    print(f"{Colors.YELLOW}Python: {PYTHON_EXE}{Colors.END}")
    print("="*70 + "\n")


def print_status(icon: str, name: str, message: str, color: str = Colors.GREEN):
    """Print formatted status message"""
    print(f"{icon}  {color}{Colors.BOLD}{name}{Colors.END}: {message}")


def start_agent(agent: Dict) -> subprocess.Popen:
    """
    Start an agent process
    
    Args:
        agent: Agent configuration dictionary
        
    Returns:
        Process object
    """
    print_status(
        agent['icon'],
        agent['name'],
        f"Starting on port {agent['port']}...",
        Colors.YELLOW
    )
    
    try:
        # Don't capture output - let agents print directly for debugging
        process = subprocess.Popen(
            agent['command']
        )
        
        # Wait for startup
        time.sleep(agent['wait_time'])
        
        # Check if process is still running
        if process.poll() is None:
            print_status(
                agent['icon'],
                agent['name'],
                f"✅ Running on port {agent['port']}",
                Colors.GREEN
            )
            return process
        else:
            print_status(
                agent['icon'],
                agent['name'],
                f"❌ Failed to start (check output above)",
                Colors.RED
            )
            return None
            
    except Exception as e:
        print_status(
            agent['icon'],
            agent['name'],
            f"❌ Error: {str(e)}",
            Colors.RED
        )
        import traceback
        print(f"{Colors.RED}{traceback.format_exc()}{Colors.END}")
        return None


def start_backend() -> subprocess.Popen:
    """Start Flask backend"""
    print_status(
        BACKEND['icon'],
        BACKEND['name'],
        f"Starting on port {BACKEND['port']}...",
        Colors.YELLOW
    )
    
    try:
        # Don't capture output for Flask - let it print directly
        process = subprocess.Popen(
            BACKEND['command']
        )
        
        time.sleep(BACKEND['wait_time'])
        
        if process.poll() is None:
            print_status(
                BACKEND['icon'],
                BACKEND['name'],
                f"✅ Running on port {BACKEND['port']}",
                Colors.GREEN
            )
            return process
        else:
            print_status(
                BACKEND['icon'],
                BACKEND['name'],
                f"❌ Failed to start (check output above)",
                Colors.RED
            )
            return None
            
    except Exception as e:
        print_status(
            BACKEND['icon'],
            BACKEND['name'],
            f"❌ Error: {str(e)}",
            Colors.RED
        )
        import traceback
        print(f"{Colors.RED}{traceback.format_exc()}{Colors.END}")
        return None


def cleanup():
    """Terminate all processes"""
    print(f"\n{Colors.YELLOW}🛑 Shutting down all services...{Colors.END}\n")
    
    for process in processes:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
    
    print(f"{Colors.GREEN}✅ All services stopped{Colors.END}\n")


def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    cleanup()
    sys.exit(0)


def main():
    """Main startup sequence"""
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Print banner
    print_banner()
    
    # Start all agents in sequence
    print(f"{Colors.BOLD}Starting AI Agents...{Colors.END}\n")
    
    for agent in AGENTS:
        process = start_agent(agent)
        if process:
            processes.append(process)
        else:
            print(f"\n{Colors.RED}❌ Failed to start {agent['name']}. Aborting...{Colors.END}\n")
            cleanup()
            sys.exit(1)
        
        print()  # Empty line for readability
    
    # Start Flask backend
    print(f"{Colors.BOLD}Starting Backend Server...{Colors.END}\n")
    backend_process = start_backend()
    
    if backend_process:
        processes.append(backend_process)
    else:
        print(f"\n{Colors.RED}❌ Failed to start Flask backend. Aborting...{Colors.END}\n")
        cleanup()
        sys.exit(1)
    
    # Print success summary
    print("\n" + "="*70)
    print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL SERVICES STARTED SUCCESSFULLY{Colors.END}")
    print("="*70)
    print(f"\n{Colors.CYAN}📍 Access Points:{Colors.END}")
    print(f"   🌐 Backend API:  http://localhost:5000")
    print(f"   🎯 Host Agent:   http://localhost:10000")
    print(f"   💰 Budget Agent: http://localhost:10001")
    print(f"   📍 Places Agent: http://localhost:10002 (with Wikipedia MCP)")
    print(f"   🗺️  Map Agent:    http://localhost:10003")
    print(f"   📚 RAG Agent:    http://localhost:10004")
    print(f"\n{Colors.YELLOW}Press Ctrl+C to stop all services{Colors.END}\n")
    print("="*70 + "\n")
    
    # Keep script running and monitor processes
    try:
        while True:
            time.sleep(1)
            
            # Check if any process has died
            for i, process in enumerate(processes):
                if process and process.poll() is not None:
                    if i < len(AGENTS):
                        agent = AGENTS[i]
                        print(f"\n{Colors.RED}❌ {agent['name']} stopped unexpectedly{Colors.END}")
                    else:
                        print(f"\n{Colors.RED}❌ Flask backend stopped unexpectedly{Colors.END}")
                    
                    cleanup()
                    sys.exit(1)
                    
    except KeyboardInterrupt:
        cleanup()


if __name__ == '__main__':
    main()
