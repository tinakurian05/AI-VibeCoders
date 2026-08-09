# The Interview Agent 🎯

An AI-powered, adaptive technical interview platform that evaluates software engineers through dynamic, evidence-driven dialogue rather than static question sets.

---

## 📌 Overview

**The Interview Agent** is an intelligent technical assessment system designed to conduct natural, adaptive coding and architecture interviews. Unlike simple LLM wrappers that ask linear or hardcoded questions, The Interview Agent runs a **closed-loop adaptive decision engine**.

The system dynamically adjusts interview difficulty, topic depth, and questioning strategy in real time based on the candidate's background, past learning context, and demonstrated technical understanding during the conversation.

---
### 📁 Project Resources
##Demo Video & Documentation:** [Google Drive](https://drive.google.com/file/d/13GFePAXn--C65CJ7Hwte5XPx7V4wH_zf/view?usp=sharing)
## 🚀 Try the Live Demo

**[Launch AI Technical Interviewer](https://ai-vibecoders-1.onrender.com)**

The deployed application includes:

- 👤 Candidate profile selection
- 🧠 Curriculum-aware interview planning
- 🤖 AI-generated technical questions
- 🔄 Adaptive questioning based on candidate answers
- 📊 Answer analysis and knowledge tracking
- 🧠 Interview memory powered by Breeth
- ⚡ Groq-powered question generation

### Deployment

| Service | URL |
|---|---|
| Frontend | https://ai-vibecoders-1.onrender.com |
| Backend API |https://ai-vibecoders.onrender.com |
| Health Check | https://ai-vibecoders.onrender.com/health |
| Candidates API | https://ai-vibecoders.onrender.com/api/candidates |

## 🔄 Adaptive Interview Loop

The interview execution follows a strict 9-stage closed loop managed by the backend **Interview Orchestrator**:

```
                  +-----------------------------------+
                  |         Candidate Profile         |
                  |     (background facts & context)  |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |        Interview Planning         |
                  |   (question budget & target days) |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
                  |         Initial Question          |
                  |   (generated via Strategy/LLM)    |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------+-----------------+
  +-------------->|         Candidate Answer          |
  |               +-----------------+-----------------+
  |                                 |
  |                                 v
  |               +-----------------+-----------------+
  |               |          Memory Retrieval         |
  |               |   (episodic recall via Breeth)    |
  |               +-----------------+-----------------+
  |                                 |
  |                                 v
  |               +-----------------+-----------------+
  |               |          Answer Analysis          |
  |               |    (understanding & gap assessment|
  |               +-----------------+-----------------+
  |                                 |
  |                                 v
  |               +-----------------+-----------------+
  |               |    Evidence & Knowledge Update    |
  |               |   (4-layer state update)          |
  |               +-----------------+-----------------+
  |                                 |
  |                                 v
  |               +-----------------+-----------------+
  |               |         Strategy Decision         |
  |               | (CLARIFY / FOLLOW_UP / DEEPEN...) |
  |               +-----------------+-----------------+
  |                                 |
  |                                 v
  |               +-----------------+-----------------+
  |               |          Next Question          |
  +---------------|    (generated & stored in memory) |
                  +-----------------------------------+
```

---

## 🏗️ Architecture

The backend is built with **FastAPI** in Python, adhering to strict separation of concerns, clean 4-layer state isolation, failover LLM routing, and episodic memory persistence.

```
                               +-----------------------------+
                               |   FastAPI REST API Layer    |
                               |     (backend/main.py)       |
                               |  (backend/api/interview.py) |
                               +--------------+--------------+
                                              |
                                              v
                               +--------------+--------------+
                               |    Interview Orchestrator   |
                               | (interview_orchestrator.py) |
                               +------+-------+-------+------+
                                      |       |       |
           +--------------------------+       |       +---------------------------+
           |                                  |                                   |
           v                                  v                                   v
+----------+----------+            +----------+----------+             +----------+----------+
|   Session Manager   |            |   Answer Analyzer   |             |   Strategy Engine    |
| (session_manager.py)|            | (answer_analyzer.py)|             | (strategy_engine.py) |
+----------+----------+            +----------+----------+             +----------------------+
           |                                  |
           | 4-Layer State                    | LLM & Memory
           | Isolation                        v
           |                       +----------+----------+
           |                       | ModelRouter/LLMGateway |  --->  Groq Cloud API
           |                       +----------+----------+       (LLM Generation)
           |                                  |
           +---------------------> +----------+----------+
                                   |  InterviewMemoryService |  --->  Breeth REST API
                                   | (interview_memory.py)   |       (Episodic Memory)
                                   +-------------------------+
```

---

## ⚙️ Core Components

### 1. Candidate Profile Service (`backend/services/candidate_profile_service.py`)
Loads pre-interview background profiles from `backend/data/candidates.json`. It normalizes education, experience, completed curriculum days, skipped missions, and activity signals into an immutable `CandidateState` model. Candidate profiles provide initial context so the candidate does not start from a blank state.

### 2. Curriculum Service (`backend/services/curriculum_service.py`)
Parses `backend/data/curriculum.json` containing 31 structured curriculum days, modules, tools, and learning objectives. Provides deterministic lookup for topic metadata across the interview lifecycle.

### 3. Interview Planner (`backend/services/interview_planner.py`)
Generates a tailored `InterviewPlan` for each candidate based on their background experience. Allocates a deterministic question budget (e.g. 8–12 questions) and selects target curriculum days for assessment.

### 4. Session Manager (`backend/services/session_manager.py`)
Orchestrates **4 distinct state layers** with strict isolation:
1. **`CandidateState`**: Immutable pre-interview background facts from `candidates.json`.
2. **`InterviewState`**: Live interview progress tracking (`current_turn`, `question_count`, `interview_plan`, `conversation`, `covered_days`, `done`).
3. **`CandidateKnowledgeModel`**: Derived technical belief state tracking understanding levels (`UNKNOWN`, `LOW`, `MEDIUM`, `HIGH`) per topic and objective, updated **only** via evidence analysis.
4. **`EvidenceLedger`**: Append-only ledger of `EvidenceItem` records extracted from candidate responses.

### 5. Interview Orchestrator (`backend/services/interview_orchestrator.py`)
The central coordinator that executes the interview loop. It delegates tasks to specialized components:
- Calls `SessionManager` for state persistence and evidence updates.
- Calls `AnswerAnalyzer` (with `InterviewMemoryService`) to evaluate answers.
- Calls `StrategyEngine` to determine the next strategic action.
- Calls `QuestionGenerator` to produce the next question.
- Manages question metadata traceability (`question_id`, `objective_id`, `turn_number`) and budget enforcement.

### 6. Answer Analyzer (`backend/services/answer_analyzer.py`)
Evaluates candidate answers against target learning objectives and retrieved Breeth memories. Returns a structured `CandidateEvidenceAnalysis` containing understanding level (`LOW`, `MEDIUM`, `HIGH`), assessment type (`supports_understanding`, `indicates_gap`, `ambiguous`), confidence score, strengths, and gaps.

### 7. Strategy Engine (`backend/services/strategy_engine.py`)
A deterministic rules engine that evaluates the updated `CandidateKnowledgeModel`, `EvidenceLedger`, and latest analysis to decide the next pedagogical move:
- **Rule A (Ambiguous / Low Confidence)** $\rightarrow$ Action: `CLARIFY` (Difficulty: `EASY`)
- **Rule B (Misconception Detected)** $\rightarrow$ Action: `FOLLOW_UP` (Difficulty: `MEDIUM`)
- **Rule E (Weak Answer / Low Understanding)** $\rightarrow$ Action: `FOLLOW_UP` (Difficulty: `EASY`, probe fundamentals)
- **Rule C (Partial Understanding / Medium)** $\rightarrow$ Action: `FOLLOW_UP` (Difficulty: `MEDIUM`, address specific gap)
- **Rule D (Strong Answer / High Understanding)** $\rightarrow$ Action: `DEEPEN` (Difficulty: `HARD`, probe unexplored objectives) or `MOVE_TOPIC` (Difficulty: `MEDIUM`, transition to next planned day)
- **Completion Check** $\rightarrow$ Action: `END` (when budget is reached or constraints are satisfied)

### 8. Question Generator (`backend/services/question_generator.py`)
Constructs context-rich prompts using the candidate profile, strategy decision, recent conversation, and retrieved memories, delegating to the LLM layer to generate natural, targeted interview questions.

### 9. LLM Gateway & Model Router (`backend/services/llm_gateway.py`, `backend/services/model_router.py`, `backend/services/groq_client.py`)
Provides resilient LLM inference over **Groq Cloud API**:
- **`GroqClient`**: Low-level HTTP client executing completion calls to `https://api.groq.com/openai/v1/chat/completions`.
- **`LLMGateway`**: Normalizes response objects and categorizes errors into sanitized categories (`authentication error`, `rate limit`, `timeout`, `connection error`, `provider error`, `invalid request`).
- **`ModelRouter`**: Executes automatic failover between primary model (`openai/gpt-oss-120b`) and fallback model (`meta-llama/llama-3.3-70b-versatile`) if primary encounters rate limits, timeouts, or provider errors.

### 10. Interview Memory & Breeth Integration (`backend/services/interview_memory.py`, `backend/services/memory_service.py`)
Connects the interview loop to **Breeth REST API** (`POST /v1/episodes`, `POST /v1/search`) for episodic memory:
- **Retrieval**: Before answer analysis, `get_relevant_memories()` queries Breeth for past turns related to the current topic.
- **Storage**: After generating the next question, `store_turn()` persists the question, candidate answer, topic, and analysis metadata as an episode turn.
- **Graceful Degradation**: If Breeth is unconfigured or returns HTTP/network errors, the memory layer gracefully falls back to empty results (`[]` for search, `{"success": False}` for store), ensuring the core interview never crashes or halts.

---

## 💡 Concrete Adaptive Interview Example

Here is a verified example of adaptive behavior supported by the system:

1. **Initial Probe**: The interviewer asks a candidate about **Prompt Engineering Fundamentals** (Day 1).
2. **Scenario A (Weak Answer)**:
   - Candidate gives a vague or incorrect explanation.
   - `AnswerAnalyzer` assesses understanding as `LOW` (`assessment_type: indicates_gap`).
   - `SessionManager` updates knowledge state for Day 1 with `LOW` confidence and logs evidence.
   - `StrategyEngine` Rule E triggers $\rightarrow$ `StrategyDecision(action=FOLLOW_UP, difficulty=EASY, intent="probe_fundamental_gap")`.
   - `QuestionGenerator` produces a simplified follow-up probing basic prompt structure.
3. **Scenario B (Strong Answer)**:
   - Candidate gives a thorough response demonstrating strong mastery.
   - `AnswerAnalyzer` assesses understanding as `HIGH` (`assessment_type: supports_understanding`).
   - `SessionManager` updates knowledge state for Day 1 to `HIGH`.
   - `StrategyEngine` Rule D triggers $\rightarrow$ `StrategyDecision(action=DEEPEN, difficulty=HARD, intent="probe_unexplored_objective")` to probe advanced system design or `MOVE_TOPIC` to transition to the next curriculum day.

---

## 📡 API Documentation

### System Endpoints

#### 1. `GET /health`
Returns system operational status.
- **Response**: `200 OK`
  ```json
  {
    "status": "ok"
  }
  ```

#### 2. `POST /api/interview`
The primary endpoint handling interview session initialization and turn processing.

- **Session Initialization Request**:
  ```json
  {
    "sessionId": "session-sarah-101",
    "candidate": {
      "member": {
        "id": "CAND-001",
        "name": "Sarah Johnson",
        "jobRole": "Senior Data Engineer"
      }
    }
  }
  ```

- **Candidate Response Request**:
  ```json
  {
    "sessionId": "session-sarah-101",
    "message": "In RAG pipelines, chunking breaks large documents into semantic sections, while vector indexing allows fast similarity search using embeddings."
  }
  ```

- **Interview Response**:
  ```json
  {
    "reply": "That's a solid overview of RAG. When dealing with large-scale document collections, how do you select an optimal chunk size and overlap strategy to balance retrieval context with embedding accuracy?",
    "done": false,
    "feedback": null
  }
  ```

---

## 📂 Project Structure

```
AI-VibeCoders/
├── .env                       # Environment variables (API keys, base URLs - gitignored)
├── .env.example               # Template environment configuration
├── technical-spec.md          # Architectural technical specification
├── README.md                  # Project documentation
├── backend/                   # Python FastAPI Backend
│   ├── main.py                # FastAPI application entrypoint
│   ├── api/
│   │   └── interview.py       # FastAPI REST API router (/api/interview)
│   ├── data/
│   │   ├── candidates.json    # Canonical candidate background profiles
│   │   └── curriculum.json    # Canonical 31-day curriculum specification
│   ├── models/
│   │   ├── analyzer.py        # AnswerAnalyzer input/output models
│   │   ├── interview.py       # Core Pydantic models (CandidateState, KnowledgeModel, Ledger)
│   │   ├── question_generator.py # QuestionGenerator request/response models
│   │   └── strategy.py        # StrategyEngine models & enums
│   ├── services/
│   │   ├── answer_analyzer.py # LLM-based candidate answer analyzer
│   │   ├── candidate_profile_service.py # Candidate profile loader & state builder
│   │   ├── curriculum_service.py # Curriculum loader & lookup service
│   │   ├── groq_client.py     # Low-level Groq Cloud API REST client
│   │   ├── interview_memory.py# Application boundary for episodic memory
│   │   ├── interview_orchestrator.py # Core interview loop orchestrator
│   │   ├── interview_planner.py # Budget & topic planner
│   │   ├── llm_gateway.py     # LLM abstraction gateway with error taxonomy
│   │   ├── memory_service.py  # Low-level Breeth REST API client
│   │   ├── model_router.py    # Primary-to-fallback model failover router
│   │   ├── question_generator.py # Context-aware LLM question generator
│   │   ├── session_manager.py # 4-layer state manager
│   │   └── strategy_engine.py # Deterministic strategy rules engine
│   └── test_*.py              # Comprehensive test suites (154 passing unit & integration tests)
└── src/                       # Node.js Data Foundation Validation
    ├── validate.js            # Node validation script for state & serialization
    └── interview/             # JavaScript data foundation models & context loaders
```

---

## 🛠️ Setup & Running Instructions

### Prerequisites
- **Python 3.10+** (Python 3.14 recommended)
- **Node.js 18+** (for Node validation scripts)
- **Groq API Key** (for LLM inference)

### 1. Environment Configuration
Create a `.env` file in the project root based on `.env.example`:

```bash
GROQ_API_KEY=your_groq_api_key_here
BREETH_API_KEY=your_breeth_api_key_here
BREETH_BASE_URL=https://api.breeth.ai
```
*(Note: Never commit real API keys to git. `.env` is listed in `.gitignore`.)*

### 2. Backend Setup & Startup
Install backend dependencies and launch the server from the repository root:

```bash
# Navigate to project root
cd AI-VibeCoders

# Run FastAPI backend via Uvicorn
python -m uvicorn backend.main:app --reload --port 8001
```

The API will be live at `http://127.0.0.1:8001`.

### 3. Node Data Foundation Validation
To run the Node.js state serialization and source file integrity validation script:

```bash
node src/validate.js CAND-001
```

---

## 🧪 Testing & Verification

The project includes an extensive automated test suite covering all layers of the architecture.

### Verified Test Results
Running `pytest` across the backend test suite confirms **154 passing tests** with 0 failures:

```bash
cd backend
python -m pytest
```

```
============================== 154 passed in 1.47s ==============================
```

### Test Suite Categories
- **Unit & State Tests**: Validate `CandidateProfileService`, `CurriculumService`, `InterviewPlanner`, `SessionManager`, `CandidateKnowledgeModel`, and `EvidenceLedger`.
- **LLM & Router Tests**: Validate `GroqClient`, `LLMGateway`, and `ModelRouter` primary-to-fallback failover logic using mocked network calls.
- **Memory Tests**: Validate `MemoryService` REST payload formatting and `InterviewMemoryService` graceful degradation.
- **Integration Tests**: Validate `InterviewOrchestrator` end-to-end loop processing (`test_interview_orchestrator.py` and `test_step5_interview_loop.py`).
- **Live Connectivity Verification**: Dedicated scripts (`test_groq_connection.py`, `test_breeth_connectivity.py`) for live API key and endpoint verification against real Groq and Breeth services.

---

## ⚠️ Current Limitations

- **In-Memory Session Storage**: Active interview sessions are managed in-memory by `SessionManager`. Server restarts clear active session state.
- **Development Scope**: Designed as a hackathon prototype without multi-tenant JWT authentication or database ORM persistence.

---

## 🤖 AI-Assisted Development

This project was built using modern AI-assisted pair-programming workflows ("vibe coding") with strict human architectural oversight and automated test verification. Prompts, iterations, and design decisions are logged in `PROMPTS.md`.

---

## 🏆 Hackathon Highlights

- **Dynamic Closed-Loop Reasoning**: Replaces static interview scripts with real-time evidence extraction and strategic adaptation.
- **Resilient AI Infrastructure**: Built-in LLM failover routing (`openai/gpt-oss-120b` $\rightarrow$ `meta-llama/llama-3.3-70b-versatile`) and graceful Breeth memory degradation.
- **Deterministic State Isolation**: Clean separation between immutable background facts (`CandidateState`) and live technical belief states (`CandidateKnowledgeModel`).
- **100% Verified Test Coverage**: 154 passing automated tests ensuring mathematical, structural, and behavioral correctness.
