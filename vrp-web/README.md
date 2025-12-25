# VRP Web Application

Full-stack Vehicle Routing Problem optimizer with web UI.

## Architecture

```
vrp-web/
├── backend/           # FastAPI (Python)
│   ├── main.py        # Entry point  
│   ├── api/
│   │   ├── matrix.py  # OSRM proxy
│   │   └── optimize.py# OR-Tools solver
│   └── schemas/       # Pydantic models
└── frontend/          # Next.js (TypeScript)
    └── src/
        ├── components/
        │   ├── map/   # Site placement
        │   ├── flow/  # React Flow ontology
        │   └── panel/ # Property editors
        └── lib/       # Store, API client
```

## Quick Start

### 1. Backend
```bash
cd vrp-web/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend
```bash
cd vrp-web/frontend
npm install
npm run dev
```

Open http://localhost:3000

## User Flow
1. 🏭 Add Depot/Customer sites on map
2. 📐 Generate Matrix (OSRM API)
3. 🚛 Add Vehicles
4. 📦 Add Shipments  
5. 🚀 Optimize
6. 📊 View Results
