<div align="center">
  <img src="Images of TARS/Movie/1.jpeg" alt="TARS Banner" width="100%" />
</div>

# TARS Chatbot

Phase 4 adds reviewed coding jobs in the sidebar. See [coding setup and current runtime limitation](docs/PHASE_4_CODING.md): local preparation/review works; live Codex execution awaits sandbox provisioning repair.

> **Personal intelligence roadmap (2026-11-21):** Read the [codebase assessment and phased architecture plan](docs/TARS_ARCHITECTURE_PLAN.md) for the migration toward shared graph memory, model-independent personality, coding assistance, voice and phone handling. The six project context files start at [project overview](context/project-overview.md); actual implementation status is in the [progress tracker](context/progress-tracker.md). The feature descriptions below describe the legacy project and should be read alongside the audit's capability limitations.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev)

## Overview

TARS (Tactical Advanced Robot System) is an advanced AI chatbot inspired by the character from the film *Interstellar*. This project leverages modern Large Language Models (LLMs) and a Retrieval-Augmented Generation (RAG) architecture to provide a robust, context-aware conversational experience. It features a dual-interface design offering both a comprehensive Command Line Interface (CLI) and a modern React-based Web UI.

## Visual Interface

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="Images/image.png" alt="Main Interface" width="400px" />
        <br />
        <b>Main Chat Interface</b>
      </td>
      <td align="center">
        <img src="Images/image copy.png" alt="System Diagnostics" width="400px" />
        <br />
        <b>System Diagnostics</b>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img src="Images/image copy 2.png" alt="Data Analysis" width="400px" />
        <br />
        <b>Data Analysis View</b>
      </td>
      <td align="center">
        <img src="Images/image copy 3.png" alt="Interactive Mode" width="400px" />
        <br />
        <b>Interactive Mode</b>
      </td>
    </tr>
  </table>
</div>

## Key Features

*   **Multi-LLM Support**: Seamless integration with local models via LM Studio and Ollama, as well as cloud providers like OpenAI and Google Gemini. Includes automatic fallback mechanisms for high availability.
*   **Retrieval-Augmented Generation (RAG)**: specialized knowledge base powered by ChromaDB, enabling accurate responses on specific domains such as Physics, Astronomy, and Movie Lore.
*   **Personality Engine**: Configurable parameters for Humor, Honesty, and Discretion to simulate the distinct TARS personality.
*   **Voice Interaction**: Integrated speech-to-text and text-to-speech capabilities for hands-free operation.
*   **Modern Architecture**: Built on a FastAPI backend with WebSocket support for real-time streaming, coupled with a responsive React + Vite frontend.

## Architecture

The system utilizes a modular architecture:
*   **Backend**: Python 3.11+, FastAPI, WebSocket.
*   **Frontend**: React, Vite, TailwindCSS.
*   **Database**: ChromaDB for vector storage.
*   **AI/ML**: Integration with various LLM providers (Local & Cloud).

## Project Structure

A detailed look at the codebase organization:

```
TARS chatbot version 1/
├── src/
│   ├── core/           # Core application logic and state management
│   ├── ai/             # LLM handlers, RAG system, and embeddings
│   ├── personality/    # Personality traits and humor engine
│   ├── voice/          # Speech-to-Text and Text-to-Speech modules
│   └── interfaces/     # API endpoints and CLI implementation
├── frontend/           # React + Vite web application
├── data/               # Vector database (ChromaDB) and logs
├── Images/             # Project screenshots and assets
└── main.py             # Application entry point
```

## Phase 3 tools and projects

Open **Tools & projects** for public research, projects/tasks, permissions, activity and read-only ICS calendar snapshots. Chat supports `/research`, `/fetch`, `/projects`, `/tasks` and `/calendar`. Writes require concrete approval. See [Phase 3 usage and limits](docs/PHASE_3_TOOLS.md). Import your actual `.ics` file to populate the calendar; no live account connection or calendar editing is enabled.

## Phase 2 personal memory

Local memory now stores complete conversations and sourced owner facts, with correction, forgetting, relationship inspection and retrieval across models. Read [memory usage and limits](docs/PHASE_2_MEMORY.md). Legacy JSON is snapshotted and imported without rewriting originals. External PostgreSQL/Neo4j deployment and live semantic-quality checks remain pending.

## Phase 1 private setup

Start with [Phase 1 setup](docs/PHASE_1_SETUP.md). The API now requires `OWNER_TOKEN` and browser device pairing. It defaults to loopback access and local-only inference (`ALLOW_CLOUD=false`). Existing run instructions below need these settings. Automated tests use fake models; live provider access must be verified locally.

## Installation

### Prerequisites
*   Python 3.11 or higher
*   Node.js & npm (for Frontend)
*   [LM Studio](https://lmstudio.ai/) (Optional, for local LLM inference)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Anbu-Malligarjun-Sri/tars-chatbot-python.git
    cd "TARS chatbot version 1"
    ```

2.  **Install Backend Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Frontend Dependencies:**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

## Configuration

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```

2.  Configure the `.env` file with your specific settings. Common variables include:

    ```ini
    # LLM Settings
    LLM_PROVIDER=lm_studio
    LM_STUDIO_BASE_URL=http://localhost:1234/v1
    
    # API Keys (if using cloud providers)
    OPENAI_API_KEY=your_key_here
    GEMINI_API_KEY=your_key_here
    ```

### Customization

You can adjust TARS's personality traits directly in the `.env` file or via CLI commands during a session.

**Environment Variables:**
```ini
# Personality Settings (0.0 to 1.0)
TARS_HUMOR_LEVEL=0.6
TARS_HONESTY_LEVEL=0.9
```

**CLI Commands:**
*   `/humor [0-100]`: Set humor percentage (e.g., `/humor 75`).
*   `/honesty [0-100]`: Set honesty percentage.


## Usage

### Running the Application (Full Stack)

To run both the backend API and the frontend interface:

**Backend (Terminal 1):**
```bash
python -m src.interfaces.api
```

**Frontend (Terminal 2):**
```bash
cd frontend && npm run dev
```

Access the Web UI at `http://localhost:8081`.

### CLI Mode

For a text-based experience directly in your terminal:

```bash
python main.py chat
```

To enable voice interaction:
```bash
python main.py chat --voice
```

## API Documentation

The backend provides several key endpoints:
*   `POST /api/chat`: Send a message and receive a response (supports streaming).
*   `GET /api/history`: Retrieve conversation history.
*   `GET /api/rag/stats`: Get statistics on the RAG knowledge base.

## Troubleshooting

Common issues and solutions:

*   **LLM Connection Error**: Ensure LM Studio is running and the server is started on port `1234` (or your configured port).
*   **Audio Not Working**: Check that your microphone is set as the default input device in system settings.
*   **Frontend Connection Refused**: Make sure the backend API is running (`python -m src.interfaces.api`) before starting the frontend.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
