<div align="center">

```
   ▄████████    ▄███████▄    ▄████████ ▀████    ▐████▀ 
  ███    ███   ███    ███   ███    ███   ███▌   ████▀  
  ███    ███   ███    ███   ███    █▀     ███  ▐███    
  ███    ███   ███    ███  ▄███▄▄▄        ▀███▄███▀    
▀███████████ ▀█████████▀  ▀▀███▀▀▀        ████▀██▄     
  ███    ███   ███         ███    █▄      ▐███  ▀███    
  ███    ███   ███         ███    ███    ▄███     ███▄  
  ███    █▀   ▄████▀       ██████████  ████       ███▄ 
```

# APEX Middleware
### Ultra-Low Latency Robotic Middleware — ROS 2 Competitor

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-black?logo=python&logoColor=gold)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-black?logo=fastapi&logoColor=gold)]()
[![Status](https://img.shields.io/badge/Status-Alpha-gold)]()

> **APEX** is a next-generation robotic middleware built for ultra-low latency, AI orchestration, and luxury developer experience. Designed to surpass ROS 2 in simplicity, performance, and cognitive integration.

</div>

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    APEX RUNTIME CORE                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  AXON    │  │  PUB/SUB │  │ SERVICES │  │ACTIONS │  │
│  │  IDL     │  │ TRANSPORT│  │   RPC    │  │   &    │  │
│  │ (Binary) │  │ Shared   │  │          │  │TIMERS  │  │
│  └──────────┘  │ Memory + │  └──────────┘  └────────┘  │
│                │ Network  │                             │
│                └──────────┘                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │              AI ORCHESTRATION LAYER               │  │
│  │  GPT-4o │ Claude │ TTC │ Custom Model Providers   │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │           APEX DASHBOARD (Luxury UI)              │  │
│  │      Black · Gold · Silver · White Palette        │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Features

- **AXON Binary IDL** — Zero-copy binary serialization, no JSON overhead
- **Pub/Sub + RPC + Actions** — Full messaging primitives
- **AI Router** — Plug GPT, Claude, or any provider by API key
- **Robot Connector** — HTTP/WebSocket interface for any hardware
- **Luxury Dashboard** — Real-time node graph, topic monitor, AI console
- **ROS 2 Bridge** — Gradual migration support
- **Sub-millisecond local transport** — Shared memory ring buffers

## Quick Start

```bash
# Clone
git clone https://github.com/phoenixc13/apex-middleware.git
cd apex-middleware

# Install dependencies
pip install -r requirements.txt

# Configure your AI providers
cp config/providers.example.yaml config/providers.yaml
# Edit config/providers.yaml with your API keys

# Run APEX
python apex/main.py

# Open Dashboard
# http://localhost:8000
```

## Project Structure

```
apex-middleware/
├── apex/
│   ├── main.py              # Entry point
│   ├── runtime/
│   │   ├── broker.py        # Pub/Sub broker
│   │   ├── registry.py      # Node registry
│   │   ├── scheduler.py     # RT-aware scheduler
│   │   └── executor.py      # Callback executor
│   ├── axon/
│   │   ├── types.py         # Binary type system
│   │   ├── serializer.py    # Zero-copy serializer
│   │   └── schema.py        # Schema definitions
│   ├── transport/
│   │   ├── shm.py           # Shared memory
│   │   └── network.py       # UDP/WebSocket
│   ├── ai/
│   │   ├── router.py        # Multi-model AI router
│   │   ├── providers/
│   │   │   ├── openai.py    # GPT-4o provider
│   │   │   ├── anthropic.py # Claude provider
│   │   │   └── base.py      # Base provider class
│   │   └── tools/
│   │       ├── browser.py   # Browser control tool
│   │       └── robot.py     # Robot action tool
│   ├── robot/
│   │   └── connector.py     # Hardware connector
│   └── api/
│       └── routes.py        # REST + WebSocket API
├── dashboard/
│   ├── index.html           # Luxury dashboard
│   ├── css/style.css        # Gold/Black/Silver theme
│   └── js/app.js            # Real-time dashboard logic
├── config/
│   └── providers.example.yaml
├── requirements.txt
└── README.md
```

## AI Provider Configuration

```yaml
# config/providers.yaml
providers:
  build_ai:
    name: openai
    model: gpt-4o
    api_key: YOUR_OPENAI_KEY
    role: code_generation

  runtime_ai:
    name: anthropic
    model: claude-opus-4-5
    api_key: YOUR_ANTHROPIC_KEY
    role: task_planning

  robot_ai:
    name: openai
    model: gpt-4o-mini
    api_key: YOUR_OPENAI_KEY
    role: robot_commands
```

## License

MIT — Built by the APEX Team
