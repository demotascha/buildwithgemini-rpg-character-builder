# RPG Character Builder 🎲

A tabletop RPG companion agent built with Google Agent Development Kit (ADK), Gemini, and Vertex AI. The agent assists players and Game Masters with character creation and management, dice rolling and stat calculations, D&D 5e spell lookups, and visual concept generation.

---

## 🌟 Implemented Features & Architecture

The agent actually integrates and implements the following Google Cloud services, foundation models, and tools:

### 1. Cross-Session Long-Term Memory (Vertex AI Memory Bank)
- **PreloadMemoryTool & Memory Callbacks**: Long-term memory wired to Vertex AI Reasoning Engine Memory Bank (`context_spec.memory_bank_config`).
- Automatically extracts and recalls user preferences, campaign history, and dietary restrictions/allergies across sessions using `PreloadMemoryTool` and `add_session_to_memory`.

### 2. Character Persistence (Google Cloud Firestore)
- Backed by a serverless Firestore database in `us-central1`.
- Built-in database CRUD tools:
  - `list_characters`: Retrieve stored party and NPC character profiles.
  - `get_character`: Look up character sheets by unique ID or character name.
  - `save_character`: Create or update characters with stats (STR, DEX, CON, INT, WIS, CHA), race, class, HP, armor class, inventory, and notes.
  - `delete_character`: Remove retired characters from the database.

### 3. Rules, Dice & Calculations (Agent Engine Sandbox Code Executor & Tools)
- `roll_dice`: Simulates standard TRPG dice notation (e.g., `1d20+5`, `3d6`, `4d6kh3`) with detailed roll breakdowns and totals.
- `AgentEngineSandboxCodeExecutor`: Executes Python code securely in Vertex AI's managed sandbox environment for complex point-buy stat calculations, probability distributions, and modifier math.
- `lookup_dnd_spell`: Retrieves official D&D 5e SRD spell rules, casting time, range, components, duration, and spell descriptions.

### 4. Visual Media Generation & Cloud Storage (Imagen & Omni)
- `generate_item_image`: Generates high-fantasy equipment and character portrait illustrations using `gemini-3.1-flash-lite-image`. Saves results as ADK session artifacts and uploads them to a public Google Cloud Storage bucket (`rpg-portraits-qwiklabs-gcp-03-bd1aa8bc4539`).
- `generate_item_video`: Generates 3D showcase animations of legendary items using Google's Omni model (`gemini-omni-flash-preview`). Saves to ADK session artifacts and uploads `.mp4` video bytes to Cloud Storage for public streaming.

### 5. Real-World Tabletop Location Grounding (Google Maps API)
- `geocode_address`: Geocodes street addresses into latitude and longitude coordinates.
- `find_nearby_places`: Searches for local board game cafes, hobby stores, and tabletop meetups using the Google Places API (New).

### 6. Interactive UI & Protocol (A2UI & A2A)
- **A2UI (Agent to UI)**: Implements A2UI v0.8 schemas and Basic Catalog (`Card`, `Column`, `Row`, `Text`, `Divider`, `Image`, `Icon`) to render rich character sheets and visual cards in supported interfaces.
- **FastAPI Chat Proxy (`frontend/`)**: Communicates over the Agent-to-Agent (A2A) protocol with the deployed Agent Runtime, rendering plain text, A2UI cards, and images with an arcane-themed interface and quick-prompt suggestions.

---

## 🛠️ Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── agent.py              # Root agent definition, system instruction, and tools
│   └── a2ui_utils.py         # A2UI callback and card transformation utilities
├── frontend/
│   ├── main.py               # FastAPI proxy bridging A2A protocol to browser
│   ├── requirements.txt      # Frontend dependencies
│   └── static/
│       └── index.html        # Responsive dark RPG-themed chat interface
├── pyproject.toml            # ADK project dependencies and UV configuration
├── agents-cli-manifest.yaml  # Deployment manifest for agents-cli
└── README.md
```

---

## 🚀 Local Setup & Development

### Prerequisites
- Python 3.11+
- `uv` (recommended) or `pip`
- Google Cloud SDK (`gcloud`) authenticated with a project having Vertex AI, Firestore, and Cloud Storage APIs enabled:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  gcloud config set project <YOUR_PROJECT_ID>
  ```

### 1. Install Dependencies
```bash
# In the project root
uv sync
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
GOOGLE_MAPS_API_KEY=<YOUR_GOOGLE_MAPS_API_KEY>
MEMORY_BANK_ID=<YOUR_VERTEX_AI_MEMORY_BANK_ID>
```

### 3. Run the ADK Development Web Playground
Run the local ADK interactive playground with the Memory Bank service connected:
```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<YOUR_MEMORY_BANK_ID>
```

### 4. Run the Custom Frontend (Optional)
To run the included FastAPI chat frontend locally:
```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<REGION>/reasoningEngines/<REASONING_ENGINE_ID>"
export AGENT_DIRECTORY="app"
python main.py
```
Visit the local server in your browser to interact with the themed interface.
