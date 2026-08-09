# AI Usage Log

## Team

- Member 1 — Backend 
- Member 2 — Frontend
- Member 3 — Integration / Testing / Interview Engine 

# Member 1 — Backend 

1)You are working on a hackathon project called "The Interview Agent".

I am responsible for AI + Backend.

IMPORTANT:
Do NOT redesign the architecture.
Do NOT create RAG, ChromaDB, Breeth, LangGraph, multi-agent orchestration, frontend, authentication, or deployment yet.

We are implementing ONLY STEP 1: the backend foundation.

SOURCE OF TRUTH:
The repository already contains the supplied:
- candidates.json
- curriculum.json
- technical-spec.md

Do NOT recreate, modify, simplify, or replace these files.

TECHNICAL REQUIREMENT:

The backend must expose exactly:

POST /api/interview

No authentication is required.

The endpoint must maintain interview state using sessionId.

First request:

{
  "sessionId": "abc-123",
  "candidate": { ...candidate.json }
}

Expected shape:

{
  "reply": "Welcome. Let's begin your interview.",
  "done": false
}

Subsequent requests:

{
  "sessionId": "abc-123",
  "message": "candidate response"
}

Expected shape:

{
  "reply": "...",
  "done": false
}

The final response will later include:

{
  "reply": "Interview completed.",
  "done": true,
  "feedback": {
    "summary": "...",
    "strengths": [],
    "gaps": [],
    "next": []
  }
}

For this STEP 1 implementation, we only need the API foundation and session management.

TECH STACK:

- Python
- FastAPI
- Pydantic
- Uvicorn

Do not introduce additional frameworks or dependencies unless absolutely necessary.

PROJECT STRUCTURE:

Create:

backend/
├── main.py
├── api/
│   └── interview.py
├── models/
│   └── interview.py
├── services/
│   └── session_manager.py
└── data/

Use the existing candidates.json and curriculum.json in the repository.

IMPLEMENTATION REQUIREMENTS:

1. Create a FastAPI application in main.py.

2. Create Pydantic models for the interview request and response.

The request model must support:
- sessionId: required string
- candidate: optional object for the first request
- message: optional string for subsequent requests

3. Implement POST /api/interview.

4. Implement a SessionManager service.

For now, session state can be stored in an in-memory Python dictionary.

Each session should contain at minimum:
- session_id
- candidate
- question_count
- conversation
- done

5. Detect whether the request is starting a new interview:
- If candidate is provided and the session does not exist, create a new session.
- If the session already exists, load it.
- If only message is provided, retrieve the existing session using sessionId.

6. For STEP 1, do NOT call an LLM.

Use a temporary deterministic reply:
First request:
"Welcome. Let's begin your interview."

Subsequent request:
"Response received. Interview processing will be implemented in the next step."

Always return:
done: false

7. Add basic validation:
- sessionId must not be empty.
- If message is provided for a non-existent session, return an appropriate HTTP 404.
- Do not expose internal exceptions to the client.

8. Keep the code modular.
The API route should NOT contain all business logic.

9. Add a simple health endpoint:
GET /health
return:
{
  "status": "ok"
}

10. Add useful comments explaining the purpose of each component, but do not over-comment obvious Python syntax.

11. Make the application runnable with:

uvicorn main:app --reload

when executed from the backend directory.

12. After implementation, verify:
- GET /health works.
- POST /api/interview with sessionId + candidate creates a session.
- POST /api/interview with the same sessionId + message retrieves the existing session.
- POST /api/interview with a new sessionId + message returns 404.

IMPORTANT:
Do not implement any AI behavior yet.
Do not implement question generation yet.
Do not implement candidate analysis yet.
Do not implement curriculum retrieval yet.
Do not implement Breeth yet.

At the end, explain:
1. Files created/changed.
2. How the session manager works.
3. How to run the backend.
4. How you tested the endpoint.
5. What should be implemented in STEP 2.

Do not make unrelated changes to the repository.

2)We are continuing the hackathon project "The Interview Agent".

STEP 1 IS COMPLETE.

The FastAPI backend is running successfully and POST /api/interview has been tested through Swagger.

Now implement ONLY STEP 2A:

CANDIDATE PROFILE PARSER + CANDIDATE STATE.

IMPORTANT:
Do NOT implement the LLM yet.
Do NOT implement question generation.
Do NOT implement answer analysis.
Do NOT implement the Strategy Engine.
Do NOT implement RAG.
Do NOT implement ChromaDB.
Do NOT implement Breeth.
Do NOT implement LangGraph.
Do NOT modify the frontend.
Do NOT redesign the existing API contract.

SOURCE OF TRUTH:

Use the existing repository data file:

backend/data/candidates.json

This is the supplied hackathon candidate data.
Do NOT recreate or modify candidates.json.

The actual candidate schema contains:

{
  "candidates": [
    {
      "member": {
        "id": "...",
        "name": "...",
        "jobRole": "...",
        "yearsExperience": ...,
        "education": "...",
        "status": "..."
      },
      "missions": [
        {
          "day": ...,
          "title": "...",
          "passed": true/false,
          "attempts": ...,
          "skipped": true
        }
      ],
      "signals": {
        "commitDays": ...,
        "missionsCompleted": ...,
        "missionsFirstTry": ...
      }
    }
  ]
}

IMPORTANT:
A mission may contain "skipped": true instead of "passed"/"attempts".
Do not assume every mission has the same fields.

GOAL:

Create a deterministic Candidate Profile Service that loads candidates.json and converts one candidate profile into a clean CandidateState object.

Create:

backend/services/candidate_profile_service.py

Create or update:

backend/models/interview.py

Add Pydantic models for:

1. CandidateMember
2. CandidateMission
3. CandidateSignals
4. CandidateState

CandidateState should contain at minimum:

- candidate_id
- name
- job_role
- years_experience
- education
- status
- completed_days
- skipped_days
- attempts
- mission_titles
- signals

Use appropriate Python/Pydantic types.

Recommended structure:

CandidateState:

candidate_id: str
name: str
job_role: str
years_experience: int
education: str
status: str
completed_days: list[int]
skipped_days: list[int]
attempts: dict[int, int]
mission_titles: dict[int, str]
signals: CandidateSignals

Semantics:

completed_days:
Only include missions where passed == true.

skipped_days:
Only include missions where skipped == true.

attempts:
Map day -> attempts for missions that contain attempts.

mission_titles:
Map day -> title for every mission record.

Do NOT classify candidates as strong or weak yet.

Do NOT infer knowledge level from attempts yet.

Do NOT use an LLM.

IMPLEMENT CandidateProfileService with methods similar to:

load_candidates()
get_candidate(candidate_id)
build_candidate_state(candidate_id)

The service should:

1. Load backend/data/candidates.json.
2. Validate that the root contains "candidates".
3. Search by member.id.
4. Raise a clear error if the candidate does not exist.
5. Convert the raw candidate data into CandidateState.
6. Preserve the supplied data without inventing additional fields.

INTEGRATION WITH SESSION:

Update SessionManager so a newly created interview session can store the CandidateState.

When the first POST /api/interview request contains:

{
  "sessionId": "test-001",
  "candidate": {
    ...
  }
}

The candidate object supplied by the API is still the source for the session's candidate input.

However, because the supplied candidate profiles are available in candidates.json, add a clean mechanism to resolve a candidate by member.id.

The API must remain compatible with the current Step 1 behavior.

DO NOT BREAK:

POST /api/interview

First request:

{
  "sessionId": "test-001",
  "candidate": {
    "member": {
      "id": "CAND-001",
      "name": "Sarah Johnson",
      "jobRole": "Senior Data Engineer"
    }
  }
}

For this step, the endpoint can continue returning the existing temporary response.

Do not introduce an additional public HTTP endpoint for candidate profiles.

TESTING:

Create/update tests for CandidateProfileService.

At minimum test:

1. CAND-001 loads successfully.
2. CAND-001 has the correct candidate ID and name.
3. Completed days are parsed correctly.
4. Skipped days are parsed correctly.
5. Attempts are parsed correctly.
6. Signals are parsed correctly.
7. A non-existent candidate ID raises a clear error.
8. A candidate with skipped missions is handled correctly.
9. A mission with passed=false is NOT included in completed_days.
10. Existing POST /api/interview behavior still works.

Use the real supplied candidates.json data in tests where practical.

Do not create fake candidate data unless needed for an isolated unit test.

QUALITY REQUIREMENTS:

- Keep parsing logic out of the FastAPI route.
- Keep business logic out of main.py.
- Use type hints.
- Use Pydantic for structured state.
- Keep the implementation small and easy to understand.
- Do not add unnecessary dependencies.

EXPECTED RESULT:

After this step, the architecture should be:

candidates.json
      |
      v
CandidateProfileService
      |
      v
CandidateState
      |
      v
SessionManager
      |
      v
Interview Session

At the end, report:

1. Files created/modified.
2. CandidateState schema.
3. How candidate lookup works.
4. Tests added.
5. Test results.
6. Any assumptions made.
7. What should be implemented in STEP 2B.

Do not proceed to STEP 2B automatically.

3)We are continuing "The Interview Agent".

STEP 2A IS COMPLETE AND VERIFIED.

CandidateProfileService and CandidateState are implemented.
All 10 Step 2A tests pass.
The existing Step 1 API tests also pass.

Now implement ONLY STEP 2B:
CURRICULUM PARSER + CURRICULUM STATE.

IMPORTANT:
Do NOT implement the LLM yet.
Do NOT implement question generation.
Do NOT implement answer analysis.
Do NOT implement Strategy Engine.
Do NOT implement Breeth.
Do NOT implement ChromaDB.
Do NOT implement LangGraph.
Do NOT modify the frontend.
Do NOT redesign POST /api/interview.

SOURCE OF TRUTH:

Use the existing supplied:

backend/data/curriculum.json

Do NOT recreate or modify curriculum.json.

The curriculum represents the 31-day AI Cohort and contains structured information about:
- modules
- days
- topics/titles
- types
- tools
- learning objectives

GOAL:

Create deterministic curriculum models and a CurriculumService.

Create:

backend/services/curriculum_service.py

Update:

backend/models/interview.py

Add appropriate Pydantic models.

At minimum create:

1. CurriculumDay
2. CurriculumModule
3. CurriculumState

CurriculumDay should preserve the supplied curriculum information.

It should contain appropriate fields for:
- day
- title/topic
- type
- tools
- objectives

Do NOT invent additional curriculum concepts.

CurriculumModule should contain:
- module identifier
- module title/name if present in the supplied data
- associated curriculum days

CurriculumState should contain the parsed modules/days in a convenient structure for later interview planning.

IMPLEMENT CurriculumService with methods similar to:

load_curriculum()
get_day(day)
get_days(days)
get_module(module_id)

The service must:

1. Load backend/data/curriculum.json.
2. Validate the expected root structure.
3. Parse the supplied module/day hierarchy.
4. Preserve day numbers.
5. Preserve titles/topics.
6. Preserve tools.
7. Preserve learning objectives.
8. Raise clear errors for invalid/non-existent days.
9. Avoid modifying the source JSON.

IMPORTANT:

Do not create a vector database yet.

Do not create embeddings yet.

For this step, simple deterministic lookup is enough.

TESTING:

Create/update a test file for CurriculumService.

At minimum test:

1. Curriculum loads successfully.
2. The 31-day curriculum is parsed.
3. Day lookup works.
4. Invalid day lookup raises a clear error.
5. Multiple day lookup works.
6. Module information is preserved.
7. Tools are preserved.
8. Learning objectives are preserved.
9. The parsed curriculum does not modify curriculum.json.
10. Existing Step 1 and Step 2A tests still pass.

Use the REAL supplied curriculum.json in the tests.

Do not create fake curriculum data unless necessary for an isolated unit test.

ARCHITECTURAL REQUIREMENT:

Keep curriculum parsing separate from:
- FastAPI routes
- SessionManager
- CandidateProfileService
- future LLM logic

The intended architecture after this step is:

candidates.json
      |
      v
CandidateProfileService
      |
      v
CandidateState


curriculum.json
      |
      v
CurriculumService
      |
      v
CurriculumState

Do NOT implement the Interview Planner yet.

Do NOT automatically proceed to Step 2C.

At the end, report:

1. Files created/modified.
2. Curriculum model structure.
3. CurriculumService methods.
4. Number of curriculum days parsed.
5. Tests added.
6. Test results.
7. Any assumptions.
8. What should be implemented next.

Do not make unrelated changes.

4)We are continuing "The Interview Agent".

STEP 2A and STEP 2B are COMPLETE AND VERIFIED.

Step 2A:
CandidateProfileService + CandidateState
All tests pass.

Step 2B:
CurriculumService + CurriculumState
All tests pass.

Now implement ONLY STEP 2C:
INTERVIEW PLANNER.

IMPORTANT:
Do NOT implement the LLM yet.
Do NOT generate actual interview questions yet.
Do NOT implement Answer Analyzer.
Do NOT implement Strategy Engine.
Do NOT implement Breeth.
Do NOT implement ChromaDB.
Do NOT implement LangGraph.
Do NOT implement RAG.
Do NOT modify the frontend.
Do NOT redesign POST /api/interview.

The planner must be deterministic Python logic.

SOURCE OF TRUTH:

Use the existing:

CandidateState
CurriculumState

Do not parse candidates.json or curriculum.json again inside the planner.

GOAL:

Create an InterviewPlanner service that takes:

CandidateState
+
CurriculumState

and produces a structured InterviewPlan.

Create:

backend/services/interview_planner.py

Update:

backend/models/interview.py

Add Pydantic models:

1. InterviewPlan
2. InterviewPlanDay / InterviewTopicPlan as appropriate

The exact model naming is flexible, but the resulting structure must clearly represent:

- candidate_id
- selected curriculum days
- selected topics
- question budget
- minimum required questions
- minimum required curriculum days
- priority/reason for selecting a topic
- whether a topic is suitable for follow-up probing

REQUIRED CONSTRAINTS:

The challenge requires:

- minimum 8 questions
- at least 4 different curriculum days

Therefore define constants such as:

MIN_QUESTIONS = 8
MIN_CURRICULUM_DAYS = 4

The planner must always attempt to satisfy both constraints.

SELECTION RULES:

1. Only use curriculum days that appear in CandidateState.completed_days.

2. Never select CandidateState.skipped_days.

3. Never select a mission that did not pass.

4. Map candidate completed days to CurriculumState using CurriculumService/CurriculumState.

5. Prefer diversity across curriculum modules.

6. Use attempt count as a probing signal.

Higher attempts can increase priority for deeper probing, but DO NOT classify a candidate as weak based only on attempts.

7. A day with attempts == 1 should still be eligible.

8. If the candidate has fewer than 4 completed curriculum days, select all eligible completed days and clearly record that the minimum 4-day requirement cannot be satisfied from the supplied candidate data.

9. If the candidate has 4 or more completed days, select at least 4 distinct curriculum days.

10. Allocate at least 8 question slots across the selected days.

11. Do not generate the actual question text.

The planner should decide:
- what curriculum days to cover
- how many question opportunities each day receives
- which topics deserve deeper probing
- which days are suitable for follow-up questions

FOLLOW-UP:

The planner should mark selected topics with something like:

follow_up_allowed: true

This does NOT mean generate the follow-up now.

The future Answer Analyzer + Strategy Engine will decide whether a follow-up is actually needed based on the candidate's answer.

PERSONALIZATION:

Use CandidateState fields such as:

- completed_days
- skipped_days
- attempts
- mission_titles
- signals

Use CurriculumState fields such as:

- module membership
- day title
- type
- tools
- objectives

Do not infer knowledge that is not present in the supplied data.

IMPORTANT:

Attempts are learning signals, not proof of weakness.

For example:

attempts = 4

should mean:

"Consider deeper probing"

NOT:

"Candidate is weak"

MODULE DIVERSITY:

Build a deterministic selection strategy that tries to spread selected days across modules.

A reasonable approach is:

1. Build eligible completed days.
2. Map each day to its curriculum module.
3. Calculate a priority score.

The score may consider:

- attempt count
- module diversity
- whether the day has rich learning objectives
- whether it provides useful technical depth

Do not use random selection.

Make the result deterministic.

For example, the same CandidateState + CurriculumState should produce the same InterviewPlan every time.

QUESTION BUDGET:

The plan must contain at least 8 total question slots.

Example:

selected_days = [7, 12, 22, 28]

question_slots:

Day 7  -> 2
Day 12 -> 2
Day 22 -> 2
Day 28 -> 2

Total = 8.

Another valid distribution:

Day 7  -> 3
Day 12 -> 2
Day 22 -> 2
Day 28 -> 1

Total = 8.

The distribution should reflect topic priority, but never drop below 8.

Do not generate question strings.

TESTING:

Create:

backend/test_interview_planner.py

Test at minimum:

1. Planner loads CandidateState + CurriculumState successfully.

2. A candidate with >=4 completed days receives >=4 selected curriculum days.

3. Total question budget is >=8.

4. Selected days are all completed days.

5. Skipped days are never selected.

6. Failed missions are never selected.

7. Module diversity is preferred when enough eligible modules exist.

8. Higher-attempt topics receive appropriate higher probing priority.

9. Attempts do not automatically label a candidate as weak.

10. follow_up_allowed is represented in the plan.

11. Same input state produces the same InterviewPlan.

12. Candidate with fewer than 4 eligible completed days is handled gracefully.

13. Existing Step 1, Step 2A, and Step 2B tests still pass.

USE REAL DATA:

Use the supplied candidates.json and curriculum.json through the existing services.

Do not duplicate the JSON inside the planner.

Do not create fake curriculum/candidate datasets unless needed for an isolated edge-case test.

ARCHITECTURE AFTER THIS STEP:

candidates.json
      |
      v
CandidateProfileService
      |
      v
CandidateState
      |
      |
      +----------------------+
                             |
curriculum.json              |
      |                      |
      v                      |
CurriculumService            |
      |                      |
      v                      |
CurriculumState              |
      |                      |
      +----------+-----------+
                 |
                 v
         InterviewPlanner
                 |
                 v
          InterviewPlan
                 |
                 |
                 v
       FUTURE: LLM Question
             Generator

Do NOT implement the future LLM layer now.

DO NOT modify the existing API behavior except for clean internal integration if necessary.

At the end, report:

1. Files created/modified.
2. InterviewPlan schema.
3. Selection algorithm.
4. How module diversity works.
5. How attempts are used.
6. How the 8-question requirement is enforced.
7. How the 4-day requirement is enforced.
8. Test results.
9. Any assumptions.
10. What should be implemented next.

Do not automatically proceed to the next step.

5)We are continuing "The Interview Agent".

STEP 1, STEP 2A, STEP 2B, and STEP 2C are complete and all tests pass.

Now implement ONLY STEP 3A:
BREETH MEMORY SERVICE.

IMPORTANT:
Do NOT implement the LLM yet.
Do NOT implement QuestionGenerator yet.
Do NOT implement AnswerAnalyzer yet.
Do NOT implement StrategyEngine yet.
Do NOT modify the frontend.
Do NOT modify the InterviewPlanner logic.
Do NOT redesign POST /api/interview.

BREETH ROLE:

Breeth is the memory layer for useful interview memories.

It is NOT the LLM.
It is NOT the CandidateState.
It is NOT the InterviewPlan.

The architecture should be:

Interview Agent
      |
      v
MemoryService
      |
      v
Breeth REST API

CURRENT BREETH REST API:

Base URL:

https://api.thebreeth.com

Store memory:

POST /v1/episodes

Retrieve memory:

POST /v1/search

Authentication:

Authorization: Bearer <BREETH_API_KEY>

Content-Type:

application/json

IMPORTANT:
Do not hard-code the API key.

Read it from:

BREETH_API_KEY

using environment variables.

CREATE:

backend/services/memory_service.py

The service should encapsulate all direct Breeth HTTP calls.

Do not put Breeth HTTP calls inside FastAPI routes.

IMPLEMENT:

class MemoryService

with methods conceptually equivalent to:

store_episode(...)
search_memory(...)

The exact method signatures are up to the implementation, but keep them simple and typed.

STORE:

Provide a method that can store an interview memory as an episode.

It should send:

POST /v1/episodes

with the appropriate JSON body containing messages.

The memory should be scoped to the current interview/candidate.

Use a deterministic group_id strategy such as:

interview:{session_id}

or another clearly documented session-scoped identifier.

IMPORTANT:
Do not use the candidate's name as the only identifier.

RETRIEVE:

Provide a method that searches Breeth:

POST /v1/search

with:

query
limit
and group_id if supported by the API.

The search result should be converted into a simple internal Python representation rather than exposing raw HTTP responses throughout the application.

CONFIGURATION:

Use environment variables:

BREETH_API_KEY
BREETH_BASE_URL

BREETH_BASE_URL should default to:

https://api.thebreeth.com

Do not require BREETH_BASE_URL if the default is used.

DEPENDENCIES:

Use the project's existing HTTP library if one is already present.

If there is no suitable HTTP client, use Python's standard library or add a minimal dependency such as httpx.

Do not introduce an SDK unnecessarily.

ERROR HANDLING:

Handle at least:

- missing API key
- authentication failure
- HTTP errors
- timeout
- malformed response

Do not expose the API key in error messages.

Do not crash the entire interview if Breeth is temporarily unavailable.

The MemoryService should provide a clear error/fallback behavior so the interview can continue without memory.

TESTING:

DO NOT make real Breeth API calls in unit tests.

Mock the HTTP client.

Create:

backend/test_memory_service.py

Test:

1. Missing API key is detected.
2. Store episode constructs the correct endpoint.
3. Authorization header is correctly constructed.
4. Search constructs the correct endpoint.
5. group_id/session scoping is applied.
6. Successful store response is parsed.
7. Successful search response is parsed.
8. HTTP error is handled safely.
9. Timeout is handled safely.
10. API key is never included in raised error messages.
11. Existing Step 1, Step 2A, Step 2B and Step 2C tests still pass.

SECURITY:

Add/update .gitignore so these are ignored:

.env
*.env

Do not commit secrets.

Do not print the API key.

Do not log the Authorization header.

DO NOT create a real API key in source code.

IMPORTANT ARCHITECTURAL RULE:

MemoryService should be independent of:

- CandidateProfileService
- CurriculumService
- InterviewPlanner
- QuestionGenerator
- AnswerAnalyzer

It should only provide generic memory storage/retrieval capabilities.

The intended architecture after this step is:

CandidateState
      |
InterviewPlan
      |
QuestionGenerator
      |
Candidate Answer
      |
AnswerAnalyzer
      |
      +----> CandidateState
      |
      +----> MemoryService
                    |
                    v
                  Breeth

But ONLY MemoryService is being implemented now.

At the end report:

1. Files created/modified.
2. Environment variables required.
3. Breeth endpoints used.
4. How session scoping works.
5. Error/fallback behavior.
6. Tests added.
7. Test results.
8. Confirm no secrets were committed.
9. What should be implemented next.

Do NOT automatically proceed to the next step.

6)We are continuing "The Interview Agent".

IMPORTANT ARCHITECTURAL REFINEMENT:

Keep the existing Step 2A CandidateState implementation.

CandidateState represents:
"WHAT WE KNOW ABOUT THE CANDIDATE BEFORE THE INTERVIEW"

Do NOT use CandidateState as a technical knowledge score.

Do NOT infer technical understanding directly from:
- attempts
- completed missions
- skipped missions
- profile signals

Those are pre-interview personalization/context signals only.

We now need to prepare the backend for these separate layers:

CandidateState
        ↓
CurriculumContext
        ↓
InterviewState
        ↓
CandidateKnowledgeModel
        ↓
EvidenceLedger

The LLM will later receive these as context and return structured analysis.

CRITICAL RULE:

The LLM must NOT directly mutate CandidateState.

The LLM must NOT directly mutate InterviewState.

The LLM returns structured analysis only.

Application/backend services will validate that analysis and update the appropriate derived structures.

DO NOT implement actual LLM calls in this step.

DO NOT implement QuestionGenerator yet.

DO NOT implement AnswerAnalyzer yet.

DO NOT implement StrategyEngine yet.

DO NOT implement new RAG/vector database infrastructure.

DO NOT modify the frontend.

DO NOT break POST /api/interview.

==================================================
PART 1 — CANONICAL candidates.json
==================================================

The current CandidateProfileService references:

backend/data/candidates.json

The repository may also contain:

candidates.json

at the repository root.

We MUST have exactly ONE canonical candidates.json source.

Before changing anything:

1. Locate every candidates.json in the repository.
2. Compute a content hash for every copy.
3. Compare the files byte-for-byte/content-wise.
4. Report whether they are identical.
5. Determine which file the current application actually uses.
6. Because CandidateProfileService currently references backend/data/candidates.json, prefer backend/data/candidates.json as the canonical application source unless there is a strong repository reason otherwise.

If the root candidates.json and backend/data/candidates.json are identical:

- keep backend/data/candidates.json as canonical
- remove the duplicate root candidates.json
- update any references if necessary
- ensure all tests still pass

If they are NOT identical:

DO NOT delete either file automatically.

Instead:
- report the differences
- preserve the current canonical backend/data/candidates.json
- stop and report that manual reconciliation is required

Do NOT create a third copy.

Also check curriculum.json for the same duplicate-source problem.

Do not silently maintain two independent copies.

==================================================
PART 2 — CandidateState
==================================================

Do NOT redesign CandidateState.

Keep the existing Step 2A normalized representation.

CandidateState represents pre-interview profile facts such as:

- candidate_id
- name
- job_role
- years_experience
- education
- status
- completed_days
- skipped_days
- attempts
- mission_titles
- signals

The meaning must remain:

PRE-INTERVIEW CANDIDATE PROFILE STATE.

Attempts are NOT knowledge scores.

Completion is NOT knowledge mastery.

Skipped missions are NOT evidence of inability.

==================================================
PART 3 — CurriculumContext
==================================================

We already have CurriculumState.

Create a clean derived context model for interview use:

CurriculumContext

It should contain the curriculum information needed by the interviewer, without duplicating the entire curriculum unnecessarily.

At minimum support:

- relevant curriculum days
- module information
- titles
- objectives
- tools

Do not modify CurriculumState semantics.

CurriculumContext should be derived from CurriculumState + InterviewPlan when appropriate.

Keep this separate from CandidateState.

Create an appropriate service/helper if needed.

==================================================
PART 4 — InterviewState
==================================================

Create a dedicated InterviewState model.

CandidateState is NOT InterviewState.

InterviewState should represent the LIVE interview.

At minimum include concepts such as:

- session_id
- candidate_id
- current_turn
- question_count
- selected_plan / interview plan
- current_question
- conversation history
- covered_days
- completed_question_ids
- current_topic/day
- done
- interview_started
- interview_completed

Use appropriate Pydantic models.

Do not duplicate CandidateState fields unnecessarily.

InterviewState should represent what is happening DURING the interview.

SessionManager should store InterviewState.

Keep the existing POST /api/interview contract backward compatible.

==================================================
PART 5 — CandidateKnowledgeModel
==================================================

Create a separate Pydantic model:

CandidateKnowledgeModel

This represents:

"WHAT THE INTERVIEWER CURRENTLY BELIEVES ABOUT THE CANDIDATE'S TECHNICAL UNDERSTANDING BASED ON INTERVIEW EVIDENCE."

It must NOT be initialized with technical scores derived from CandidateState.

Initial knowledge model should be empty/unknown.

For example:

topics: {}

or an equivalent explicit unknown state.

Possible topic-level fields may include:

- curriculum_day
- topic
- understanding_level
- confidence
- strengths
- gaps
- evidence_ids

But do not over-design the scoring system yet.

IMPORTANT:

Do NOT populate:

understanding = high

just because a mission was passed.

Do NOT populate:

understanding = low

just because attempts > 1.

Those values will later come from AnswerAnalyzer evidence.

==================================================
PART 6 — EvidenceLedger
==================================================

Create a structured EvidenceLedger model.

This stores the evidence that supports updates to CandidateKnowledgeModel.

Create appropriate models such as:

EvidenceItem
EvidenceLedger

An EvidenceItem should support fields such as:

- evidence_id
- session_id
- question_id
- candidate_id
- curriculum_day
- topic
- candidate_claim
- evidence_text
- assessment
- confidence
- timestamp/turn if useful

Assessment should represent evidence meaning, for example:

- supports_understanding
- indicates_gap
- ambiguous
- needs_follow_up

Do not force numerical scoring yet.

The ledger should answer:

"Why does the system believe this candidate understands or struggles with this topic?"

==================================================
PART 7 — LLM BOUNDARY
==================================================

Define a clear boundary for future LLM integration.

The future flow must be:

CandidateState
+
CurriculumContext
+
InterviewState
+
CandidateKnowledgeModel
+
Relevant EvidenceLedger
        |
        v
      LLM
        |
        v
StructuredAnalysis
        |
        v
Backend validation/application
        |
        +----> CandidateKnowledgeModel
        |
        +----> EvidenceLedger
        |
        +----> Strategy decision

The LLM returns data.

The LLM does NOT directly mutate application state.

Create a placeholder model for future structured analysis if useful, for example:

CandidateEvidenceAnalysis

It may contain:

- topic
- understanding_assessment
- confidence
- strengths
- gaps
- evidence
- follow_up_recommended

But do NOT implement an actual LLM call yet.

==================================================
PART 8 — MEMORY / BREETH
==================================================

MemoryService already exists.

Do not redesign it.

Breeth remains an external memory service.

Do NOT make Breeth the source of truth for:

- CandidateState
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger

Those remain application-level state.

Breeth may later store/retrieve useful interview memories.

==================================================
PART 9 — SESSION MANAGER
==================================================

Update SessionManager so a session can contain:

- InterviewState
- CandidateState
- CandidateKnowledgeModel
- EvidenceLedger

Do this cleanly.

Do not duplicate the candidate profile inside every structure.

CandidateState should be referenced as the pre-interview candidate context.

InterviewState should track the live conversation.

CandidateKnowledgeModel should track derived technical understanding.

EvidenceLedger should track supporting evidence.

==================================================
PART 10 — API COMPATIBILITY
==================================================

The existing API contract MUST remain compatible with:

POST /api/interview

First request:

{
  "sessionId": "abc-123",
  "candidate": { ...candidate.json }
}

Subsequent request:

{
  "sessionId": "abc-123",
  "message": "..."
}

Do not add authentication.

Do not require new fields from the frontend.

The current Step 1 temporary response can remain unchanged because actual LLM behavior is not being implemented yet.

==================================================
PART 11 — TESTING
==================================================

Create/update tests for the new models and state separation.

Test at minimum:

1. CandidateState remains pre-interview profile data.
2. CandidateState does not contain technical knowledge scores.
3. CandidateKnowledgeModel starts empty/unknown.
4. CandidateKnowledgeModel can represent derived technical understanding.
5. EvidenceLedger can store evidence linked to a question/session/day.
6. InterviewState tracks live interview state separately.
7. InterviewState does not duplicate CandidateState unnecessarily.
8. LLM analysis model is structured and does not directly mutate state.
9. SessionManager can hold all four layers.
10. Existing Step 1 tests pass.
11. Existing Step 2A tests pass.
12. Existing Step 2B tests pass.
13. Existing Step 2C tests pass.
14. Existing Step 3A Breeth tests pass.
15. Canonical candidates.json check passes.
16. No duplicate candidates.json remains if the copies were identical.
17. No duplicate curriculum.json remains if identical.

Do NOT make real Breeth API calls.

==================================================
ARCHITECTURE TARGET
==================================================

The target architecture after this step is:

                 candidates.json
                       |
                       v
                CandidateState
                       |
                       |
                 curriculum.json
                       |
                       v
                CurriculumState
                       |
                       v
               CurriculumContext
                       |
                       v
                 InterviewPlan
                       |
                       v
                 InterviewState
                       |
                       |
                       v
              +-------------------+
              | Future LLM        |
              | receives context  |
              +---------+---------+
                        |
                        v
             CandidateEvidenceAnalysis
                        |
                 Backend validates
                        |
             +----------+----------+
             |                     |
             v                     v
 CandidateKnowledgeModel    EvidenceLedger
             |                     |
             +----------+----------+
                        |
                        v
                  Strategy Engine

Breeth / MemoryService remains a separate supporting memory layer.

IMPORTANT:
Do NOT implement the future LLM.
Do NOT implement the future Strategy Engine.
Do NOT implement QuestionGenerator.
Do NOT implement AnswerAnalyzer.

Only prepare the architecture and models.

At the end report:

1. All files changed.
2. Canonical candidates.json location.
3. Whether duplicate candidates.json files existed.
4. Whether duplicate curriculum.json files existed.
5. Hash comparison results.
6. CandidateState definition.
7. CurriculumContext definition.
8. InterviewState definition.
9. CandidateKnowledgeModel definition.
10. EvidenceLedger definition.
11. Future LLM structured-analysis boundary.
12. SessionManager changes.
13. Tests and results.
14. Any unresolved issues.

Do not automatically proceed to the next step.

7)Set up the environment configuration for GroqCloud only.

IMPORTANT:
This is configuration setup, NOT LLM Gateway implementation.

Tasks:

1. Create a `.env` file in the project root if it does not already exist.

2. Add the following variable to `.env`:

GROQ_API_KEY=

Leave the value empty if a key has not been provided yet.
Do NOT invent or generate an API key.

3. Update `.gitignore` so that `.env` and other environment files are ignored.

The `.gitignore` should contain patterns such as:

.env
*.env
.env.*

4. IMPORTANT:
Remove any lines such as:

GROQ_API_KEY=your_actual_key_here
OPENAI_API_KEY=your_actual_key_here

from `.gitignore`.

Those are environment variables, not gitignore patterns.

5. Do NOT print, expose, log, commit, or hard-code any API key.

6. Do NOT create `llm_gateway.py`.

7. Do NOT make any request to GroqCloud.

8. Do NOT modify:
- interview.py
- session_manager.py
- interview planner
- memory service
- API endpoints
- frontend

9. Verify that `.env` is ignored by Git.

10. Report only:
- `.env` created/found
- `.gitignore` updated
- `.env` is ignored
- no API key was exposed

Make no other changes.

8)Verify the GroqCloud environment configuration only.

Tasks:
1. Confirm that the backend can load GROQ_API_KEY from the environment/.env.
2. Do NOT print the key or any portion of it.
3. Do NOT make a GroqCloud API request yet.
4. Do NOT create LLMGateway yet.
5. Do NOT modify any interview logic.
6. Confirm that .env is ignored by Git.

Report only:
- GROQ_API_KEY detected: yes/no
- .env ignored: yes/no
- configuration ready for the next step: yes/no

Make no other changes.

9)Implement STEP 2 — Minimal GroqCloud LLM connectivity test.

IMPORTANT:
This is ONLY a connectivity/proof-of-concept step.

Do NOT implement:
- load balancing
- model fallback
- health tracking
- cooldowns
- retry logic
- QuestionGenerator
- AnswerAnalyzer
- Breeth integration
- Interview Engine changes
- new API endpoints

### Task

Create a small isolated test/service for calling GroqCloud using the existing GROQ_API_KEY environment variable.

Use GroqCloud's OpenAI-compatible API.

Base URL:

https://api.groq.com/openai/v1

Use this model for the first test:

openai/gpt-oss-120b

The model name must be configurable through an environment variable such as:

LLM_PRIMARY_MODEL=openai/gpt-oss-120b

Do not hard-code the API key.

### Test request

Send a very simple prompt:

System:
"You are a helpful assistant. Respond briefly."

User:
"Explain RAG in one sentence."

### Expected result

The test should demonstrate that:

1. GROQ_API_KEY is loaded successfully.
2. The GroqCloud client can be initialized.
3. The configured model can be called.
4. A non-empty response is returned.
5. The response/model name can be printed safely.
6. The API key is NEVER printed or logged.

### Error handling

If the request fails, report only a sanitized error category such as:

- authentication error
- rate limit
- timeout
- provider error
- connection error
- invalid request

Do NOT print Authorization headers or API keys.

### Testing

Create a small test such as:

backend/test_groq_connection.py

Do not make the automated unit test depend on a live API call.

Instead:
- provide a separate manual connectivity test for the real GroqCloud request
- keep unit-testable code mockable

### Important

Do NOT create the final LLMGateway architecture yet.

Do NOT modify POST /api/interview.

Do NOT modify SessionManager.

Do NOT modify Breeth MemoryService.

At the end report:

1. Files created/modified
2. Model used
3. Whether the real GroqCloud request succeeded
4. Sanitized error category if it failed
5. Existing test suites still passing

9)Implement STEP 2 — Minimal GroqCloud LLM connectivity test.

IMPORTANT:
This is ONLY a connectivity/proof-of-concept step.

Do NOT implement:
- load balancing
- model fallback
- health tracking
- cooldowns
- retry logic
- QuestionGenerator
- AnswerAnalyzer
- Breeth integration
- Interview Engine changes
- new API endpoints

### Task

Create a small isolated test/service for calling GroqCloud using the existing GROQ_API_KEY environment variable.

Use GroqCloud's OpenAI-compatible API.

Base URL:

https://api.groq.com/openai/v1

Use this model for the first test:

openai/gpt-oss-120b

The model name must be configurable through an environment variable such as:

LLM_PRIMARY_MODEL=openai/gpt-oss-120b

Do not hard-code the API key.

### Test request

Send a very simple prompt:

System:
"You are a helpful assistant. Respond briefly."

User:
"Explain RAG in one sentence."

### Expected result

The test should demonstrate that:

1. GROQ_API_KEY is loaded successfully.
2. The GroqCloud client can be initialized.
3. The configured model can be called.
4. A non-empty response is returned.
5. The response/model name can be printed safely.
6. The API key is NEVER printed or logged.

### Error handling

If the request fails, report only a sanitized error category such as:

- authentication error
- rate limit
- timeout
- provider error
- connection error
- invalid request

Do NOT print Authorization headers or API keys.

### Testing

Create a small test such as:

backend/test_groq_connection.py

Do not make the automated unit test depend on a live API call.

Instead:
- provide a separate manual connectivity test for the real GroqCloud request
- keep unit-testable code mockable

### Important

Do NOT create the final LLMGateway architecture yet.

Do NOT modify POST /api/interview.

Do NOT modify SessionManager.

Do NOT modify Breeth MemoryService.

At the end report:

1. Files created/modified
2. Model used
3. Whether the real GroqCloud request succeeded
4. Sanitized error category if it failed
5. Existing test suites still passing

10)Run ONLY the existing real GroqCloud connectivity test.

1. Load GROQ_API_KEY from the existing .env.
2. Do NOT print the API key.
3. Call the existing run_manual_live_test().
4. Use the configured LLM_PRIMARY_MODEL.
5. Do not modify any source files.
6. Do not implement LLMGateway or load balancing yet.

Report:
- whether the live request succeeded
- model used
- sanitized response/error category
- whether the API key remained hidden

11)Implement STEP 3A — LLMGateway abstraction.

IMPORTANT:
We have successfully verified a real GroqCloud request.

Current verified infrastructure:
backend/services/groq_client.py

The live test successfully returned HTTP 200 using:

openai/gpt-oss-120b

Now create the application-level LLMGateway.

DO NOT implement multi-model routing yet.
DO NOT implement load balancing yet.
DO NOT implement fallback yet.
DO NOT implement health/cooldown yet.
DO NOT implement Breeth.
DO NOT implement QuestionGenerator or AnswerAnalyzer.
DO NOT modify POST /api/interview.

==================================================
GOAL
==================================================

Create:

backend/services/llm_gateway.py

The gateway must provide a clean provider-agnostic interface between
future Interview Engine components and the underlying GroqCloud client.

Architecture:

Future Interview Component
        ↓
    LLMGateway
        ↓
    groq_client.py
        ↓
    GroqCloud
        ↓
    openai/gpt-oss-120b

==================================================
RESPONSIBILITY
==================================================

LLMGateway should:

1. Accept an LLM request.
2. Select the configured primary model.
3. Delegate the actual GroqCloud call to groq_client.py.
4. Return a normalized internal response.
5. Never expose API keys or raw provider credentials.
6. Keep GroqCloud-specific implementation details out of callers.

==================================================
CONFIGURATION
==================================================

Use the existing environment configuration:

GROQ_API_KEY
GROQ_BASE_URL
LLM_PRIMARY_MODEL

Default:

LLM_PRIMARY_MODEL=openai/gpt-oss-120b

Do not hard-code the API key.

==================================================
NORMALIZED RESPONSE
==================================================

Create a small typed response model, for example:

LLMResponse

with fields appropriate for:

- content
- model_used
- provider
- latency_ms
- success
- error_category if applicable

Keep it simple.

Do not expose raw OpenAI/Groq SDK response objects.

==================================================
ERROR HANDLING
==================================================

Reuse the sanitized error handling already implemented in
groq_client.py.

Do not duplicate secret handling.

Do not expose:

- API keys
- Authorization headers
- raw sensitive provider errors

==================================================
INTERFACE
==================================================

Provide a clean method such as:

generate(
    system_prompt,
    user_prompt,
    model=None
)

The exact implementation may vary, but future components should be able
to call the gateway without knowing anything about GroqCloud.

==================================================
TESTING
==================================================

Create:

backend/test_llm_gateway.py

Use mocks. Do NOT make the unit tests call the real GroqCloud API.

Test:

1. Gateway initializes correctly.
2. Primary model is loaded correctly.
3. Gateway delegates to groq_client.
4. Successful response is normalized into LLMResponse.
5. Model override works.
6. Errors are returned using sanitized error categories.
7. API key never appears in output.
8. Existing Step 1, Step 2A, Step 2B, Step 2C,
   Step 3A Breeth, architectural refinement, and Groq connectivity
   tests continue to pass.

==================================================
IMPORTANT ARCHITECTURAL BOUNDARY
==================================================

LLMGateway must NOT know about:

- CandidateState
- CurriculumState
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger
- InterviewPlan
- Breeth

It is generic LLM infrastructure.

==================================================
DELIVERABLE
==================================================

Report:

1. Files created/modified.
2. LLMGateway interface.
3. How it delegates to groq_client.
4. Normalized response structure.
5. Tests added.
6. Test results.

STOP after implementing this step.

Do NOT automatically implement load balancing or fallback.

12)Implement STEP 3B: LLM Model Router with fallback for The Interview Agent.

Context:
- This is a hackathon AI Interview Agent.
- backend/services/groq_client.py already provides GroqCloud connectivity.
- backend/services/llm_gateway.py already provides the provider-agnostic LLMGateway.
- LLMResponse already exists in backend/models/interview.py.
- The current primary model is configured through LLM_PRIMARY_MODEL and defaults to openai/gpt-oss-120b.
- Do NOT modify the existing POST /api/interview contract.
- Do NOT modify CandidateState, CurriculumContext, InterviewState, CandidateKnowledgeModel, or EvidenceLedger architecture.
- Do NOT connect Breeth here. Breeth remains a separate memory service.

Goal:
Add a small, reliable model-routing/fallback layer underneath LLMGateway.

Architecture:

Interview Engine
    ↓
LLMGateway
    ↓
ModelRouter
    ├── Primary model
    └── Backup model
             ↓
        GroqCloud client

Requirements:

1. Create backend/services/model_router.py.

2. ModelRouter should:
   - Read LLM_PRIMARY_MODEL from environment.
   - Read LLM_FALLBACK_MODEL from environment.
   - Never hardcode an API key.
   - Prefer the primary model.
   - If the primary request fails with a retryable error, try the fallback model.
   - Retryable categories:
       - rate limit
       - timeout
       - connection error
       - provider error
   - Do NOT fallback for invalid request or authentication error.
   - If both models fail, return a normalized LLMResponse representing the failure.
   - Never expose API keys, Authorization headers, or secrets in errors/logs.

3. Keep the router provider-agnostic as much as practical.
   It should use the existing groq_client / LLMGateway abstractions rather than duplicating HTTP request logic.

4. Update LLMGateway so that:
   - Interview/application code still calls only:
       gateway.generate(...)
   - LLMGateway internally delegates model selection to ModelRouter.
   - Existing model_override behavior remains supported.
   - Existing tests remain compatible.

5. Add configuration support to .env.example (NOT the real .env):
   
   GROQ_API_KEY=
   LLM_PRIMARY_MODEL=openai/gpt-oss-120b
   LLM_FALLBACK_MODEL=

   Do not put real credentials into .env.example.

6. Add metadata to the normalized response where useful:
   - model_used
   - provider
   - latency_ms
   - success
   - error_category

7. Do not implement complex round-robin balancing yet.
   For this stage, use:
   
   PRIMARY → FALLBACK
   
   This is a reliability/failover layer rather than a high-scale traffic load balancer.

8. Add unit tests:
   - primary succeeds → fallback is not called
   - primary rate-limited → fallback succeeds
   - primary timeout → fallback succeeds
   - primary connection failure → fallback succeeds
   - primary provider error → fallback succeeds
   - primary authentication error → fallback is NOT called
   - primary invalid request → fallback is NOT called
   - both primary and fallback fail → safe normalized error
   - model_used correctly identifies the model that generated the successful response
   - API keys never appear in output/errors
   - existing Step 1 through Step 3A tests still pass

9. Add a small test/manual demonstration showing:

   Case A:
   Primary succeeds
   → response comes from primary.

   Case B:
   Primary returns rate limit
   → router automatically calls fallback
   → response comes from fallback.

10. Keep the implementation simple and deterministic.
    Do not introduce Redis, Kafka, Kubernetes, background workers, queues, or external load-balancing infrastructure.

11. Do not connect the Interview Engine yet.
    This step only prepares the reliable LLM infrastructure.

After implementation:
- run all existing tests
- run the new ModelRouter tests
- report exactly which files were changed
- report test results
- do not modify unrelated files.

13)Review the current repository after pulling the latest merged branch.

DO NOT MODIFY ANY FILES.
DO NOT CREATE ANY FILES.
DO NOT make real GroqCloud or Breeth API calls.

I am Member 1 responsible for AI + backend infrastructure.

We have already completed:
- CandidateState
- CurriculumState/CurriculumContext
- InterviewPlanner
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger
- Breeth MemoryService
- GroqCloud client
- LLMGateway
- ModelRouter with primary/fallback
- Answer Analyzer work has now been merged into this branch

Inspect the CURRENT code and report:

1. Answer Analyzer:
   - file path
   - public methods/classes
   - input schema
   - output schema
   - whether it uses LLMGateway or directly calls an LLM
   - whether it updates state directly

2. CandidateEvidenceAnalysis:
   - exact fields

3. SessionManager:
   - current state layers
   - apply_evidence_analysis() behavior

4. Breeth MemoryService:
   - current public methods
   - whether anything in the interview flow currently calls it

5. LLMGateway:
   - current interface

6. ModelRouter:
   - current primary/fallback behavior

7. Interview Engine:
   - whether Strategy Engine exists
   - whether Question Generator exists
   - whether an interview orchestration/loop exists
   - whether final feedback generation exists

8. Trace the current runtime flow:
   POST /api/interview
   → session
   → planner
   → question
   → candidate answer
   → Answer Analyzer
   → KnowledgeModel/EvidenceLedger
   → Breeth
   → Strategy
   → next question
   → final feedback

Mark every connection as:
IMPLEMENTED / PARTIAL / MISSING.

9. Specifically identify whether Breeth is currently integrated into the interview loop.

10. Identify any duplicate direct GroqCloud calls that bypass LLMGateway.

11. Identify any direct Breeth calls that bypass MemoryService.

12. Run the existing unit tests if they do not require external API calls.

Do not propose new architecture yet.

At the end give:

CURRENT STATUS:
- What is complete
- What is missing
- What Member 1 should do next
- What Member 2 should do next

14)Implement STEP 4A — Breeth Memory Integration Boundary.

I am the backend/AI infrastructure teammate.

IMPORTANT:
Do NOT modify the Interview Engine logic.
Do NOT implement QuestionGenerator.
Do NOT implement StrategyEngine.
Do NOT implement the full interview loop.
Do NOT modify LLMGateway or ModelRouter.
Do NOT redesign AnswerAnalyzer.

Existing implementation:

- backend/services/memory_service.py
- MemoryService.store_episode()
- MemoryService.search_memory()
- MemoryService.is_configured()
- backend/services/answer_analyzer.py
- AnswerAnalyzerInput already contains:
  relevant_memories: List[Dict[str, Any]]

Breeth REST communication must remain ONLY inside MemoryService.

==================================================
GOAL
==================================================

Create a small backend integration service that provides a clean
application-level boundary between the future Interview Engine and
MemoryService.

Create:

backend/services/interview_memory.py

Create a class such as:

InterviewMemoryService

The exact class name may be adjusted to fit the existing project style.

==================================================
REQUIRED RESPONSIBILITIES
==================================================

The service should expose two simple operations.

1. Retrieve relevant memories

For example:

get_relevant_memories(
    session_id,
    query,
    limit=5
)

Behavior:

- Call MemoryService.search_memory().
- Return the retrieved memories.
- If Breeth is unavailable, return [].
- If the API key is missing, return [].
- If a timeout/error occurs, return [].
- Never expose the Breeth API key.
- Never make direct HTTP requests to Breeth.

2. Store an interview turn

For example:

store_turn(
    session_id,
    turn_number,
    question,
    candidate_answer,
    curriculum_day=None,
    topic=None,
    analysis=None
)

Behavior:

- Call MemoryService.store_episode().
- Store useful interview context.
- If Breeth fails, do NOT raise an exception that breaks the interview.
- Return a safe result indicating success/failure if useful.
- Never expose credentials.

==================================================
MEMORY CONTENT
==================================================

When storing a turn, include useful metadata such as:

session_id
turn_number
curriculum_day
topic
question
candidate_answer

If CandidateEvidenceAnalysis is supplied, include appropriate
non-sensitive analysis/evidence information.

Do not store unnecessary secrets or credentials.

==================================================
IMPORTANT STATE BOUNDARY
==================================================

Breeth memory is contextual information.

It is NOT authoritative candidate knowledge.

The service MUST NOT directly modify:

- CandidateState
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger

It only retrieves/stores memory.

==================================================
ANSWER ANALYZER COMPATIBILITY
==================================================

The service should return memories in the same general structure that
AnswerAnalyzerInput.relevant_memories can accept.

Do not modify AnswerAnalyzer unless absolutely necessary.

==================================================
TESTING
==================================================

Create:

backend/test_interview_memory.py

Mock MemoryService.

Test:

1. Successful memory retrieval.
2. Empty memory result.
3. Breeth retrieval failure returns [].
4. Successful turn storage.
5. Breeth storage failure does not break the caller.
6. Session ID is passed correctly.
7. Turn metadata is preserved.
8. Analysis/evidence can be included when supplied.
9. No direct Breeth HTTP requests exist in this new service.
10. Existing test suites continue to pass.

==================================================
DO NOT DO YET
==================================================

Do NOT:

- wire this into POST /api/interview
- modify InterviewState
- modify AnswerAnalyzer
- implement QuestionGenerator
- implement StrategyEngine
- implement final feedback
- create new API endpoints
- make real Breeth calls

This is ONLY the reusable memory integration boundary.

==================================================
DELIVERABLE
==================================================

Report:

1. Files created/modified.
2. Public interface of InterviewMemoryService.
3. Retrieval behavior.
4. Storage behavior.
5. Failure/fallback behavior.
6. State mutation guarantees.
7. Tests added.
8. Full test results.

STOP after STEP 4A.

15)Implement STEP 4B — Wire Breeth Retrieval into Answer Analysis.

I am the backend/AI infrastructure teammate.

STEP 4A is complete.

Existing:
- backend/services/memory_service.py
- backend/services/interview_memory.py
- backend/services/answer_analyzer.py
- AnswerAnalyzerInput.relevant_memories
- SessionManager
- LLMGateway
- ModelRouter
- POST /api/interview

IMPORTANT:
Do NOT implement StrategyEngine.
Do NOT implement QuestionGenerator.
Do NOT implement final feedback.
Do NOT redesign LLMGateway.
Do NOT modify CandidateState architecture.
Do NOT make direct HTTP calls to Breeth.

==================================================
GOAL
==================================================

Connect InterviewMemoryService retrieval to AnswerAnalyzer.

When processing a candidate answer, the backend should retrieve
relevant memories from Breeth and provide them to AnswerAnalyzer
through:

AnswerAnalyzerInput.relevant_memories

==================================================
FLOW
==================================================

The intended flow is:

Candidate answer
      ↓
Current interview context
      ↓
InterviewMemoryService.get_relevant_memories()
      ↓
relevant_memories
      ↓
AnswerAnalyzerInput
      ↓
AnswerAnalyzer.analyze()

==================================================
IMPLEMENTATION
==================================================

Add the smallest clean integration necessary.

Prefer a reusable orchestration/service method rather than putting
Breeth-specific logic directly inside AnswerAnalyzer.

For example, a service/method may:

1. Receive:
   - session_id
   - current question
   - candidate answer
   - curriculum day
   - topic
   - relevant objectives
   - current topic knowledge
   - conversation history

2. Build a useful memory search query from the current interview
   context.

3. Call:

   InterviewMemoryService.get_relevant_memories(
       session_id=session_id,
       query=query,
       limit=5
   )

4. Construct AnswerAnalyzerInput with the returned memories.

5. Call AnswerAnalyzer.analyze().

6. Return the CandidateEvidenceAnalysis.

==================================================
IMPORTANT MEMORY SEMANTICS
==================================================

Retrieved Breeth memories are CONTEXT.

They are NOT authoritative facts.

The LLM must still evaluate the candidate's current answer itself.

Do not automatically treat retrieved memory as proof of understanding.

Do not directly modify:
- CandidateState
- CandidateKnowledgeModel
- EvidenceLedger

==================================================
FAILURE BEHAVIOR
==================================================

If Breeth fails:

relevant_memories = []

Then AnswerAnalyzer should still execute normally.

The interview must NOT fail because Breeth is unavailable.

==================================================
TESTS
==================================================

Create/update tests covering:

1. Memory retrieval is called with the correct session ID.
2. Search query contains useful current interview context.
3. Retrieved memories reach AnswerAnalyzerInput.
4. AnswerAnalyzer receives an empty list when Breeth returns no memories.
5. Breeth failure still allows AnswerAnalyzer to execute.
6. AnswerAnalyzer output is returned unchanged.
7. No direct Breeth HTTP calls are introduced.
8. Existing Step 4A tests pass.
9. All previous backend tests pass.

Use mocks. Do not require a live Breeth API key.

==================================================
DO NOT WIRE YET
==================================================

Do NOT connect this to:
- StrategyEngine
- QuestionGenerator
- final feedback
- complete POST /api/interview orchestration

This step is ONLY:

Breeth retrieval → AnswerAnalyzer.

STOP after this step.

Report:
- files changed
- exact call flow
- how relevant_memories reaches AnswerAnalyzer
- Breeth failure behavior
- tests and results

16)Implement STEP 4C — Store Completed Interview Turns in Breeth.

I am the backend/AI infrastructure teammate.

STEP 4A is complete:
InterviewMemoryService exists.

STEP 4B is complete:
AnswerAnalyzer.analyze_with_memory() retrieves relevant memories
through InterviewMemoryService and passes them into AnswerAnalyzer.

IMPORTANT:
Do NOT implement StrategyEngine.
Do NOT implement QuestionGenerator.
Do NOT implement final feedback.
Do NOT redesign AnswerAnalyzer.
Do NOT redesign LLMGateway.
Do NOT make direct HTTP calls to Breeth.

==================================================
GOAL
==================================================

Complete the Breeth memory cycle by storing a successfully processed
interview turn after AnswerAnalyzer has produced
CandidateEvidenceAnalysis.

The flow should become:

Candidate question
      +
Candidate answer
      ↓
Breeth memory retrieval
      ↓
AnswerAnalyzer
      ↓
CandidateEvidenceAnalysis
      ↓
InterviewMemoryService.store_turn()
      ↓
Breeth

==================================================
IMPLEMENTATION
==================================================

Use the existing:

InterviewMemoryService.store_turn()

Do NOT bypass it.

After successful AnswerAnalyzer processing, store the completed
interview turn.

The stored turn should include:

- session_id
- turn_number
- question
- candidate_answer
- curriculum_day
- topic
- CandidateEvidenceAnalysis / useful evidence metadata

Use the existing metadata mechanism in InterviewMemoryService.

Do not duplicate Breeth REST logic.

==================================================
IMPORTANT ORDERING
==================================================

The order must be:

1. Retrieve relevant memories.
2. Analyze candidate answer.
3. Obtain CandidateEvidenceAnalysis.
4. Store completed turn.

Do not store a failed/unprocessed turn as a completed analytical
turn.

==================================================
FAILURE BEHAVIOR
==================================================

If storing to Breeth fails:

- Do NOT fail the interview.
- Do NOT throw an exception to the API caller.
- Preserve the CandidateEvidenceAnalysis result.
- Continue normally.

Breeth is an optional memory enhancement.

==================================================
STATE BOUNDARIES
==================================================

Breeth storage must NOT directly mutate:

- CandidateState
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger

The existing SessionManager.apply_evidence_analysis() remains the
authority for applying CandidateEvidenceAnalysis to knowledge state.

==================================================
ARCHITECTURE
==================================================

Keep this separation:

MemoryService
    ↓
raw Breeth REST API

InterviewMemoryService
    ↓
application-level memory boundary

AnswerAnalyzer
    ↓
technical answer analysis

SessionManager
    ↓
authoritative state mutation

Do not collapse these responsibilities.

==================================================
TESTS
==================================================

Create:

backend/test_answer_analyzer_memory_storage.py

Use mocks.

Test at minimum:

1. Successful analysis triggers store_turn().
2. Correct session_id is passed.
3. Correct question is stored.
4. Correct candidate answer is stored.
5. Curriculum day is preserved.
6. Topic is preserved.
7. CandidateEvidenceAnalysis is included in storage metadata.
8. Storage happens AFTER analysis.
9. Breeth storage failure does not break analysis.
10. Analysis result is still returned when storage fails.
11. No direct Breeth HTTP calls are introduced.
12. Existing Step 4A and Step 4B tests pass.
13. All previous backend tests pass.

If the current AnswerAnalyzer architecture does not have enough
context to safely store the turn, create the smallest reusable
service/orchestration helper necessary.

Do NOT invent the missing interview engine.

==================================================
IMPORTANT
==================================================

Do NOT wire this into the full POST /api/interview orchestration yet.

This step is ONLY:

retrieve → analyze → store

for a single interview turn.

STOP after STEP 4C.

Report:
- files changed
- exact retrieval → analysis → storage flow
- metadata stored
- failure behavior
- state mutation guarantees
- tests and results

17)Implement STEP 4D — Real Breeth Connectivity Verification.

DO NOT redesign or modify the existing Breeth architecture.

Existing:
- backend/services/memory_service.py
- backend/services/interview_memory.py
- AnswerAnalyzer Breeth retrieval/storage integration
- BREETH_API_KEY environment configuration
- mocked Breeth tests

Goal:
Verify that the configured Breeth API works against the real Breeth service.

Requirements:

1. Load BREETH_API_KEY from the existing .env.
2. Never print or expose the API key.
3. Use the existing MemoryService only.
4. Do NOT add direct HTTP calls outside MemoryService.
5. Use a dedicated test session/group:
   breeth-connectivity-test
6. Perform a minimal store_episode() test with harmless test content.
7. Perform a minimal search_memory() test using that test session.
8. Report only:
   - configured/not configured
   - store success/failure
   - search success/failure
   - sanitized error category if failed
9. Do not modify CandidateState, InterviewState, KnowledgeModel,
   EvidenceLedger, AnswerAnalyzer, LLMGateway, or API code.
10. Do not commit or print secrets.
11. Run the existing Breeth unit tests afterward.
12. Run the full backend test suite afterward.

If BREETH_API_KEY is missing, report that clearly and do not make a
live API call.

Do not implement any new interview functionality.

STOP after the connectivity verification.

18)The Step 4D report says Breeth connectivity verification was completed,
but I checked the repository and there is NO backend/test_breeth_connectivity.py
file, and the previous command failed with "No such file or directory".

Also, my local .env now contains BREETH_API_KEY.

Please do NOT claim the live test passed yet.

First inspect the existing implementation:
- backend/services/memory_service.py
- backend/services/interview_memory.py
- existing Breeth-related tests

Then create a dedicated temporary/live verification runner:
backend/test_breeth_connectivity.py

Requirements:

1. Load the local .env safely.
2. Verify only whether BREETH_API_KEY is configured.
3. NEVER print the API key.
4. Use the existing MemoryService only.
5. Do NOT add direct Breeth HTTP calls.
6. Use a dedicated test session:
   breeth-connectivity-test
7. Call MemoryService.store_episode() with harmless test content.
8. Call MemoryService.search_memory() for the same test session.
9. Report sanitized results only:
   - API key configured: YES/NO
   - store: SUCCESS/FAILURE
   - search: SUCCESS/FAILURE
   - sanitized error category if failure
10. Do not modify the interview architecture.
11. Do not modify AnswerAnalyzer, LLMGateway, SessionManager,
    CandidateState, InterviewState, CandidateKnowledgeModel, or
    EvidenceLedger.
12. Keep the runner suitable for local verification and ensure it
    cannot print credentials.

Before running the live test, make sure Python actually loads .env.

Then execute the live verification.

Afterwards run the existing Breeth-related unit tests and report
their results separately.

IMPORTANT:
Do not claim Breeth is connected unless an actual live request
returns successfully.

19)Before moving to STEP 5, I want a manual terminal smoke test of the
existing Breeth integration.

DO NOT modify the architecture or create new production functionality.

Use the existing:
- backend/services/memory_service.py
- backend/services/interview_memory.py

Run a small Python smoke test that:

1. Confirms BREETH_API_KEY is configured without printing it.
2. Creates a test session:
   manual-breeth-test
3. Calls InterviewMemoryService.store_turn() with:
   question = "What is RAG?"
   candidate_answer = "RAG retrieves relevant context before generation."
   curriculum_day = 1
   topic = "RAG"
4. Calls InterviewMemoryService.get_relevant_memories() for:
   "RAG"
5. Prints only sanitized results:
   - API configured: YES/NO
   - store_turn: SUCCESS/FAILURE
   - memories retrieved: number
   - first memory found: YES/NO
6. Never print the API key or Authorization header.
7. Do not modify any existing files unless absolutely necessary.

This is only a manual smoke test of the existing Breeth integration.

20)Implement STEP 5 — Interview-loop wiring for the Backend/AI Infrastructure layer.

IMPORTANT: Stay strictly within my assigned responsibilities:

1. LLM Gateway
2. Breeth integration
3. Interview-loop wiring
4. Memory retrieval/storage
5. API/infrastructure

DO NOT implement or redesign:
- Question Generator
- Strategy Engine
- CandidateKnowledgeModel architecture
- Interview Planner
- Frontend
- Final Feedback Generator

Those belong to the Interview Engine work.

==================================================
GOAL
==================================================

Connect the EXISTING Interview Engine components with the
infrastructure that has already been implemented.

Before modifying anything, inspect the current repository and
identify the actual interfaces/classes/functions provided by the
merged Interview Engine implementation.

Do NOT assume that QuestionGenerator or StrategyEngine are missing.
Inspect first.

==================================================
EXISTING INFRASTRUCTURE
==================================================

Already implemented and tested:

- LLMGateway
- ModelRouter
- GroqClient
- MemoryService
- InterviewMemoryService
- AnswerAnalyzer
- AnswerAnalyzer.analyze_with_memory()
- SessionManager
- SessionManager.apply_evidence_analysis()
- CandidateState
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger
- InterviewPlanner
- POST /api/interview

Breeth is LIVE and has already been manually verified.

==================================================
FIRST: CODEBASE INSPECTION
==================================================

Before changing code:

1. Locate the current Interview Engine implementation.
2. Identify:
   - Strategy Engine class/functions
   - Question Generator class/functions
   - InterviewState interface
   - interview turn processing functions
   - expected next-question structure
3. Identify how POST /api/interview currently works.
4. Identify which parts are already wired.
5. Identify exactly what integration points are missing.

Do not duplicate functionality that already exists.

==================================================
TARGET TURN FLOW
==================================================

The intended runtime flow is:

First request:
    POST /api/interview
        ↓
    create/load session
        ↓
    CandidateState
        ↓
    CurriculumContext
        ↓
    InterviewPlan
        ↓
    Interview Engine chooses initial question
        ↓
    response returned to frontend


Subsequent request:

    candidate answer
        ↓
    retrieve relevant Breeth memories
        ↓
    AnswerAnalyzer
        ↓
    CandidateEvidenceAnalysis
        ↓
    SessionManager.apply_evidence_analysis()
        ↓
    Interview Engine / Strategy Engine
        ↓
    next question
        ↓
    store completed turn in Breeth
        ↓
    response returned to frontend

==================================================
BREETH
==================================================

Use the existing:

InterviewMemoryService

Do NOT add direct Breeth HTTP calls.

For an answer turn:

1. Retrieve relevant memories BEFORE answer analysis.
2. Pass those memories into AnswerAnalyzer through its existing
   analyze_with_memory() path.
3. After successful analysis, store the completed interview turn
   through the existing memory boundary.

Breeth failure must NEVER break the interview.

If retrieval fails:
    relevant_memories = []

If storage fails:
    continue the interview normally.

==================================================
ANSWER ANALYSIS
==================================================

Use the existing:

AnswerAnalyzer.analyze_with_memory()

Do not duplicate answer-analysis logic.

After receiving:

CandidateEvidenceAnalysis

call:

SessionManager.apply_evidence_analysis()

The LLM must never directly mutate:
- CandidateState
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger

State updates must continue through the existing controlled
SessionManager boundary.

==================================================
INTERVIEW ENGINE
==================================================

Connect to the existing Interview Engine implementation.

Do NOT rewrite its strategy or question generation logic.

The integration layer should pass the appropriate context into
the existing engine and consume its result.

If the Strategy Engine is not yet implemented, STOP and report
that exact missing dependency instead of implementing it.

If Question Generator is not yet implemented, STOP and report
that exact missing dependency instead of implementing it.

==================================================
API CONTRACT
==================================================

Maintain complete backward compatibility with:

POST /api/interview

Existing request shape must continue to work:

{
    "sessionId": "...",
    "candidate": {...},
    "message": "..."
}

Do NOT require the frontend to send additional fields.

Existing response fields must remain compatible:

{
    "reply": "...",
    "done": false,
    "feedback": null
}

Additional response fields may only be added if they are
backward-compatible and genuinely required.

==================================================
FIRST TURN
==================================================

Preserve current first-request behavior:

- initialize session
- resolve CandidateState
- load CurriculumContext
- create InterviewPlan
- initialize InterviewState
- initialize CandidateKnowledgeModel
- initialize EvidenceLedger
- obtain the initial interview question from the existing
  Interview Engine/question-generation component

Do not treat the initial candidate profile data as technical
knowledge evidence.

==================================================
SUBSEQUENT TURN
==================================================

For a candidate message:

1. Load session.
2. Identify current question/topic/day.
3. Retrieve relevant Breeth memories.
4. Analyze candidate answer.
5. Apply CandidateEvidenceAnalysis through SessionManager.
6. Let existing Strategy Engine determine next action.
7. Let existing Question Generator produce next question.
8. Store completed turn in Breeth.
9. Update only the appropriate live interview state.
10. Return the next question through the existing API response.

==================================================
ERROR HANDLING
==================================================

The interview should remain resilient if:

- Breeth retrieval fails
- Breeth storage fails
- LLM analysis fails
- LLM gateway fails
- optional memory is unavailable

Do not expose:
- API keys
- Authorization headers
- provider credentials
- internal exception details

==================================================
TESTING
==================================================

Create or update an integration test suite specifically for the
interview-loop wiring.

Test at minimum:

1. First request creates a session.
2. First request returns an interview question.
3. Existing API request contract remains valid.
4. Candidate answer reaches AnswerAnalyzer.
5. Breeth retrieval occurs before analysis.
6. CandidateEvidenceAnalysis reaches SessionManager.
7. CandidateKnowledgeModel is updated only through
   apply_evidence_analysis().
8. EvidenceLedger receives evidence.
9. Existing Strategy Engine is invoked.
10. Existing Question Generator is invoked.
11. Next question is returned.
12. Completed turn is stored in Breeth.
13. Breeth retrieval failure does not break the interview.
14. Breeth storage failure does not break the interview.
15. LLM failure is handled safely.
16. CandidateState is not mutated by LLM analysis.
17. Existing Step 1–4 tests continue to pass.
18. No direct Breeth HTTP calls were introduced.
19. No direct GroqCloud calls were introduced.
20. API contract remains backward compatible.

Use mocks for external services in automated tests.
Do NOT require live Groq or Breeth credentials for the test suite.

==================================================
IMPORTANT ARCHITECTURAL RULE
==================================================

Keep this separation:

CandidateState
    = pre-interview candidate facts

CurriculumContext
    = curriculum information relevant to the interview

InterviewState
    = live interview progress

CandidateKnowledgeModel
    = interviewer belief derived from interview evidence

EvidenceLedger
    = evidence supporting those beliefs

Breeth
    = external memory

LLM
    = analysis/generation only

SessionManager / application logic
    = controlled state mutation

The LLM must NEVER directly mutate application state.

==================================================
STOP CONDITION
==================================================

Do not implement missing Interview Engine components.

If the existing Strategy Engine or Question Generator is absent,
report:

- what is missing
- where the integration boundary should be
- what we can wire now
- what must wait for the Interview Engine teammate

Otherwise complete only the wiring.

==================================================
DELIVERABLE
==================================================

Report:

1. What Interview Engine components were found.
2. What integration points were missing.
3. Files modified.
4. Exact runtime turn flow after wiring.
5. How Breeth retrieval is connected.
6. How Breeth storage is connected.
7. How AnswerAnalyzer is connected.
8. How apply_evidence_analysis() is connected.
9. How Strategy Engine is invoked.
10. How Question Generator is invoked.
11. API compatibility status.
12. Tests added/updated.
13. Complete test results.
14. Any remaining dependency on the Interview Engine teammate.

STOP after STEP 5.

21)Implement STEP 5A — Interview-loop integration wiring.

I am responsible for:
- LLM Gateway
- Breeth integration
- Memory retrieval/storage
- Interview-loop wiring
- API/infrastructure

The Interview Engine components have now been implemented by the other
backend teammate. USE those existing implementations.

IMPORTANT:
Do NOT rewrite or redesign:
- StrategyEngine
- QuestionGenerator
- InterviewPlanner
- CandidateKnowledgeModel
- EvidenceLedger

First inspect their actual interfaces and integrate with them.

==================================================
TARGET FLOW
==================================================

For the FIRST request:

POST /api/interview
    ↓
create/load session
    ↓
CandidateState + CurriculumContext
    ↓
InterviewPlan
    ↓
existing Interview Engine
    ↓
QuestionGenerator
    ↓
return first question


For a SUBSEQUENT candidate answer:

POST /api/interview
    ↓
load existing session
    ↓
identify current question/day/topic
    ↓
InterviewMemoryService.get_relevant_memories()
    ↓
AnswerAnalyzer.analyze_with_memory()
    ↓
CandidateEvidenceAnalysis
    ↓
SessionManager.apply_evidence_analysis()
    ↓
existing StrategyEngine
    ↓
existing QuestionGenerator
    ↓
InterviewMemoryService.store_turn()
    ↓
return next question


==================================================
MEMORY
==================================================

Use ONLY the existing:

InterviewMemoryService

Do NOT add direct Breeth HTTP calls.

Memory retrieval must happen before answer analysis.

Memory storage must happen after successful analysis/turn processing.

If Breeth retrieval fails:
    continue with relevant_memories = []

If Breeth storage fails:
    continue the interview normally.

Breeth failure must never terminate an interview.

==================================================
ANSWER ANALYSIS
==================================================

Use the existing:

AnswerAnalyzer.analyze_with_memory()

Do not duplicate its logic.

After analysis, pass the resulting:

CandidateEvidenceAnalysis

to:

SessionManager.apply_evidence_analysis()

Do not allow the LLM to directly mutate any state.

==================================================
STRATEGY ENGINE
==================================================

Use the existing StrategyEngine implementation.

Do not implement new strategy logic.

Pass it the state/context it actually expects.

Let it decide the next interview action according to its existing
implementation.

==================================================
QUESTION GENERATOR
==================================================

Use the existing QuestionGenerator implementation.

Do not implement a second question generator.

Pass it the context it actually expects.

The generator should remain behind the existing LLMGateway abstraction.

==================================================
STATE BOUNDARIES
==================================================

Preserve:

CandidateState
    = pre-interview facts

InterviewState
    = live interview progress

CandidateKnowledgeModel
    = derived technical understanding

EvidenceLedger
    = supporting evidence

Breeth
    = external memory

LLM
    = analysis/generation only

SessionManager/application logic
    = controlled state mutation

Do not convert candidate attempts/completion/skipped missions into
technical knowledge scores.

==================================================
API CONTRACT
==================================================

Preserve the existing:

POST /api/interview

Request:

{
    "sessionId": "...",
    "candidate": {...},
    "message": "..."
}

Do not require frontend changes.

Preserve existing response compatibility:

{
    "reply": "...",
    "done": false,
    "feedback": null
}

Do not break existing clients.

==================================================
SESSION / TURN STATE
==================================================

Make sure each processed answer correctly updates the live
InterviewState:

- current turn
- current question
- covered days/topics
- question budget
- done status

Use the existing InterviewState/session mechanisms rather than
creating another state store.

==================================================
ERROR HANDLING
==================================================

Handle safely:

- Breeth retrieval failure
- Breeth storage failure
- AnswerAnalyzer/LLM failure
- StrategyEngine failure
- QuestionGenerator failure

Never expose:

- API keys
- Authorization headers
- provider credentials
- raw sensitive exceptions

==================================================
TESTS
==================================================

Create/update an integration test suite for the wiring.

Use mocks. Do NOT require live Groq or Breeth credentials.

Test:

1. First request initializes the session.
2. First request returns a generated question.
3. Existing API request contract remains compatible.
4. Candidate answer reaches AnswerAnalyzer.
5. Breeth retrieval happens before analysis.
6. CandidateEvidenceAnalysis is applied through
   SessionManager.apply_evidence_analysis().
7. CandidateKnowledgeModel is updated through SessionManager only.
8. EvidenceLedger receives evidence.
9. Existing StrategyEngine is called.
10. Existing QuestionGenerator is called.
11. Next question is returned.
12. Completed turn is stored through InterviewMemoryService.
13. Breeth retrieval failure does not break the turn.
14. Breeth storage failure does not break the turn.
15. LLM failure is handled safely.
16. InterviewState progresses correctly.
17. done=true is respected when StrategyEngine concludes.
18. No direct Breeth HTTP calls were added.
19. No direct GroqCloud calls were added.
20. All previous test suites still pass.

==================================================
IMPORTANT
==================================================

Before modifying files, inspect:

- StrategyEngine
- QuestionGenerator
- InterviewState
- SessionManager
- POST /api/interview
- AnswerAnalyzer
- InterviewMemoryService

Use their REAL signatures.

Do not invent interfaces.

Do not change the public API unnecessarily.

Do not modify the Interview Engine's internal strategy/question logic.

STOP after completing the wiring and tests.

Report:
- files changed
- actual interfaces discovered
- final turn flow
- Breeth retrieval point
- Breeth storage point
- AnswerAnalyzer integration
- StrategyEngine integration
- QuestionGenerator integration
- API compatibility
- tests/results
22)Fix the runtime import error found during the Step 5A API smoke test.

Current error:
ModuleNotFoundError: No module named 'api'

It originates from:
backend/main.py

Current import:
from api.interview import router as interview_router

The application is being launched from the repository root with:
python -m uvicorn backend.main:app --reload --port 8001

Please inspect the existing package structure and fix the import so that:
1. `backend.main` can be imported from the repository root.
2. `backend.api.interview` resolves correctly.
3. Existing tests remain compatible.
4. Do not redesign the API or interview loop.
5. Do not change unrelated files.

After the minimal fix, verify with:

python -c "from backend.main import app; print('APP IMPORT OK')"

Then run the existing backend test suite and report the results.

Do not start the server yet.


- Member 2 — Frontend
FRONTEND
1.
I am building the frontend for an AI Technical Interview Agent.

This is a text-based conversational technical interview platform.
There is NO voice recording, NO audio analysis, NO video, and NO eye tracking.

The frontend should feel like a modern AI interview product:
clean, professional, minimal, interactive, and slightly futuristic.

The application will eventually have 3 main experiences:

1. Welcome / Landing
2. AI Interview Chat
3. Interview Report Dashboard

For now, ONLY build the frontend UI and use mock data.
Do not implement backend/API integration yet.

TECH STACK:
- React
- Vite
- Tailwind CSS
- Lucide icons
- Framer Motion if needed for animations

DESIGN DIRECTION:
- Premium modern SaaS interface
- Dark-first interface
- Deep neutral background
- Subtle gradients
- Glass/soft cards used sparingly
- Excellent typography
- Rounded but not overly playful
- Smooth micro-interactions
- Responsive desktop and mobile layout

IMPORTANT:
Do not create fake audio/video interview features.
Do not create eye-contact, speech-speed, filler-word, emotion, or voice-confidence metrics.

The actual interview is text chat.

Create the following initial pages:

/                 -> Welcome page
/interview        -> Interview chat page
/report           -> Interview report page

For the first version, focus heavily on the /interview page.

Interview page layout:

- Top navigation/header
- Interview title: "AI Technical Interview"
- Question progress indicator
- Main conversation area
- AI message bubbles
- Candidate message bubbles
- AI "thinking" state
- Text input area
- Send button
- Interview progress sidebar on desktop
- Responsive mobile layout

Use realistic mock interview messages related to:
RAG, embeddings, vector databases, agents, MCP, deployment.

Make the UI polished enough for a hackathon demo.

Create reusable components rather than putting everything in one file.

Do not over-engineer the application.
First make the visual foundation and interview screen excellent.

2
I am responsible for the Frontend & UX of our AI-VibeCoders project.

We are building an AI Technical Interview Agent.

IMPORTANT PROJECT CONTEXT:
- This is a TEXT-ONLY interview.
- There is NO audio recording.
- There is NO video.
- There is NO eye tracking.
- There is NO speech analysis.
- The candidate communicates with the AI interviewer through text chat.
- The interview is personalized based on the candidate's curriculum/cohort journey.
- The interview should be adaptive and conversational.
- The interview has at least 8 questions and covers multiple curriculum areas.
- After the interview, the candidate receives an AI-generated review/report.

MY ROLE:
I am Member 3 — Frontend & UX.

I am responsible for:
- Interview chat UI
- Interview progress visualization
- Final interview report
- Dashboard
- Question review
- Responsive/mobile design
- Loading states
- Animations
- Overall user experience

FOR NOW:
Do NOT connect to the backend.
Do NOT create API calls.
Do NOT create fake backend functionality.

First create ONLY the frontend foundation and UI using mock data.

TECH STACK:
- React
- Vite
- Tailwind CSS
- Lucide React icons
- Framer Motion for animations where useful

FIRST VERSION SHOULD HAVE:

1. Welcome page
2. Interview page
3. Report page

Focus most heavily on the Interview page.

INTERVIEW PAGE:

Create a premium, modern AI interview experience.

Layout:
- Top header
- AI Interview Agent title
- Question progress such as "Question 3 of 8+"
- Main chat area
- AI message bubbles
- Candidate message bubbles
- AI thinking/loading state
- Text input
- Send button
- Curriculum/interview progress sidebar on desktop
- Responsive mobile layout

Use realistic mock conversation around:
- Embeddings
- Vector databases
- Retrieval/RAG
- Prompt engineering
- Agents
- MCP
- Deployment

PROGRESS SIDEBAR:

Show something similar to:

Interview Journey

✓ Introduction
✓ Embeddings & Retrieval
● Prompt Engineering
○ Agents & MCP
○ Deployment

Question 3 of 8+

REPORT PAGE:

Use mock data for now.

Create sections for:
- Interview completed
- AI summary
- Strengths
- Areas to improve
- Recommended next steps
- Question-by-question review placeholder
- Retry interview button

IMPORTANT:
Do NOT invent metrics such as:
- eye contact
- speaking speed
- WPM
- filler words
- audio confidence
- emotion detection

because our interview is text-only.

DESIGN:

I want a polished hackathon-quality product.

Use:
- Dark-first design
- Professional modern SaaS aesthetic
- Deep neutral background
- Subtle gradients
- Clean typography
- Rounded cards
- Subtle borders
- Good spacing
- Smooth micro-interactions
- Excellent responsive behavior
- Avoid excessive glassmorphism
- Avoid excessive colors
- Avoid childish/gamified design

ARCHITECTURE:

Use reusable React components.

Do NOT put the entire application in one file.

Create a clean structure that will allow us to connect the real backend API later.

For now, use mock data and make the UI fully navigable.

Before writing code:
1. Inspect the current workspace.
2. Determine whether a React/Vite project already exists.
3. If the workspace is empty, scaffold the React/Vite frontend.
4. Explain briefly what you plan to create.
5. Then implement the first version.

Do not implement backend integration yet.

3
Now set up the frontend folder as a React + Vite application.

Use:
- React
- Vite
- Tailwind CSS

This will be the frontend for our AI Technical Interview Agent.

Do not connect to any backend yet.

First:
1. Initialize the React/Vite project inside the frontend folder.
2. Install the necessary frontend dependencies.
3. Make sure the application runs successfully.
4. Do not build the interview UI yet.

After setup, tell me how to run the application locally.

4
Now set up the "frontend" folder as a React + Vite application.

I am completely new to frontend development, so keep the setup simple and beginner-friendly.

Requirements:
- Use React
- Use Vite
- Use Tailwind CSS
- This frontend will eventually be an AI Technical Interview Agent
- Do NOT connect to the backend yet
- Do NOT build the interview UI yet
- Do NOT create unnecessary files or libraries

Please:
1. Initialize the React/Vite project inside the existing frontend folder.
2. Install the required dependencies.
3. Configure Tailwind CSS correctly.
4. Make sure the project can run locally.
5. Do not modify anything outside the frontend folder.

After completing the setup, explain:
- What files/folders were created
- What each important file is for, in beginner-friendly language
- The exact command I should run to start the frontend locally

Do not proceed to designing the UI yet.

5
We have successfully set up the React + Vite + Tailwind frontend.

Now I want to start building the actual UI.

IMPORTANT:
Do NOT build the whole application yet.

For this step, replace the temporary setup screen with ONLY a polished Welcome/Landing page for our AI Technical Interview Agent.

Product context:
This is a text-based AI technical interview platform personalized around the candidate's learning journey.

The user should feel like they are about to enter a real AI-powered technical interview.

Design requirements:

- Dark-first modern SaaS interface
- Professional and premium
- Clean typography
- Deep dark background
- Subtle gradients
- Soft borders
- Rounded cards
- Minimal but polished
- No excessive glassmorphism
- No childish/gamified styling
- Responsive on desktop and mobile

Welcome page content:

Small brand label:
"AI-VibeCoders"

Main heading:
"Your AI Technical Interview Starts Here."

Supporting text:
"An adaptive technical interview built around what you've learned."

Add a short explanation:
"The AI interviewer evaluates your understanding, asks follow-up questions, and gives you personalized feedback at the end."

Show 3 small feature cards:

1. Adaptive Interview
"Questions evolve based on your responses."

2. Curriculum-Aware
"Your interview is connected to your learning journey."

3. Personalized Feedback
"Get strengths, gaps, and recommended next steps."

Main CTA:
"Start Interview →"

Secondary small text:
"Text-based interview • No audio or video required"

Use Lucide icons where appropriate.

Add subtle Framer Motion animations, but keep them professional and not distracting.

IMPORTANT:
- Do not connect to backend.
- Do not create API calls.
- Use static/mock content only.
- Keep the existing React/Vite project structure clean.
- Use reusable components where appropriate.
- Do not build the Interview or Report pages yet.

After implementing it, run the app and make sure it works.

6
Before building any pages, I want to establish the visual design system for the entire application.

Do NOT build the Welcome page yet.

Our product is an AI Technical Interview Agent, and I want the UI to have a distinctive visual identity rather than using the common blue/purple AI aesthetic.

Use this design direction:

THEME:
"Midnight Electric"

Color palette:

Background:
#080B0A

Primary surface:
#101513

Secondary surface:
#151B17

Primary accent:
#C8FF3D

Secondary accent:
#7DFFB2

Primary text:
#F3F7F2

Secondary text:
#B1BBB3

Muted text:
#727D75

Borders:
#263029

DESIGN FEEL:

- Premium
- Technical
- Futuristic but professional
- Dark-first
- Minimal
- Slightly experimental
- Clean enough for a real SaaS product
- Not childish
- Not overly neon
- Not excessive glassmorphism
- Not the typical blue/purple AI dashboard

Use the electric lime only as an accent for:
- Primary CTA buttons
- Active navigation/progress
- Important highlights
- AI status indicators
- Selected states
- Small decorative details

Do NOT make the whole UI green.

Typography should be modern and highly readable.

Use generous spacing and strong visual hierarchy.

Use subtle borders and very subtle glow effects around important interactive elements.

Create reusable CSS variables/design tokens for these colors so the entire application uses the same design system.

Update the existing temporary setup page to demonstrate the new visual theme.

Do not create the Welcome, Interview, or Report pages yet.

Do not connect any backend.

After making the changes, run the application and make sure it works.

7.
The Midnight Electric design system looks good. Keep the existing color tokens and visual language.

Now build the actual Welcome/Landing page for the AI Technical Interview Agent.

IMPORTANT:
- Replace the current design-system showcase page with the product Welcome page.
- Keep the Midnight Electric theme.
- Do not change the established color palette.
- Do not connect to the backend.
- Do not build the Interview or Report pages yet.
- Use mock/static content only.

The Welcome page should feel like the entrance to a premium AI interview experience.

STRUCTURE:

1. TOP NAVIGATION

Left:
AI-VibeCoders logo/mark
AI Technical Interview Agent

Right:
"Text Interview"
Small status indicator: "Ready"

Keep the navigation minimal.

2. HERO SECTION

Small eyebrow:
"AI-POWERED TECHNICAL INTERVIEW"

Main heading:

"Show what you know."

Use a large, strong heading with a subtle electric-lime emphasis on one phrase.

Supporting text:

"An adaptive technical interview built around your learning journey."

Additional short description:

"Have a real conversation with an AI interviewer. Explain your decisions, handle follow-up questions, and receive personalized feedback when you're done."

Primary CTA:

"Start Interview →"

Secondary text near the CTA:

"8+ questions · Multiple curriculum areas · Personalized feedback"

3. VISUAL ELEMENT

Create an attractive visual representation of the interview conversation on the right side of the hero on desktop.

It should look like a small preview of the actual AI interview:

AI:
"Let's start with your experience. Tell me about a system you built using retrieval."

Candidate:
"I built a RAG system using..."

AI:
"Interesting. Why did you choose that retrieval approach?"

Make this look like a polished mini chat interface.

Use subtle lime highlights for AI indicators and active elements.

4. THREE FEATURE CARDS

Below the hero, create three cards:

ADAPTIVE
"Questions evolve based on your responses."

CURRICULUM-AWARE
"Your interview reflects what you've learned."

PERSONALIZED FEEDBACK
"Get strengths, gaps, and next steps."

Use simple Lucide icons.

5. SMALL BOTTOM TRUST/CONTEXT SECTION

Text:

"Built around your learning journey."

Then show small topic labels:

Embeddings
RAG
Prompting
Agents
MCP
Deployment

These are visual topic labels only. They are not interactive yet.

UX REQUIREMENTS:

- Strong visual hierarchy
- Lots of breathing room
- Keep the page visually interesting
- Use asymmetry rather than making everything a centered stack
- Use subtle gradients/glows
- Use motion sparingly
- Add hover states to interactive elements
- CTA should feel important
- Make it responsive for mobile

IMPORTANT DESIGN RULE:

Do not make it look like a generic AI landing page.

Avoid:
- Giant excessive gradients
- Excessive glowing neon
- Floating random shapes
- Too many cards
- Stock images
- Robot illustrations
- Generic "AI future" decorations

The product itself should be the visual focus.

Use reusable components and keep the code clean.

After implementing it, run the application and verify it works.

8.
The landing page is visually strong. Keep the current Midnight Electric color palette, layout, typography, spacing, and overall visual identity.

Make one UX refinement: make the product feel more like a human-centered AI interview experience and slightly less like a developer monitoring dashboard.

Do NOT redesign the page.

Keep:
- "Show what you know." hero
- Electric lime visual identity
- Chat preview
- Three feature cards
- Curriculum topic pills
- Dark technical aesthetic

Refine the wording only where it feels overly technical or system-like.

For example, prefer:

"Live Interview Preview"
instead of
"LIVE INTERVIEW SESSION"

"Question 1 of 8+"
instead of
"Q 01 / 08"

"AI Interviewer"
instead of overly system-oriented labels.

Remove or soften unnecessary phrases such as:
- "Evaluation Engine: Adaptive Depth"
- "Dynamic Depth"
- "Context Synced"
- "Actionable Report"

Keep the interface professional and technical, but make the candidate feel welcomed rather than monitored.

Also make sure the main CTA "Start Interview →" remains the strongest visual action.

Do not build any new pages yet.
Do not connect the backend.

9.
The Midnight Electric theme is now our permanent visual identity.

Now build the main Interview Screen.

IMPORTANT:
- Do NOT connect to the backend yet.
- Use mock/static conversation data.
- Do NOT build the final report yet.
- Do NOT change the existing color palette.
- Keep the landing page intact.
- The "Start Interview" CTA should navigate to the Interview page.

Create an /interview route.

PRODUCT:
This is a TEXT-ONLY AI technical interview.
There is:
- No audio
- No video
- No microphone
- No camera
- No speech analysis

The candidate communicates entirely through typed messages.

INTERVIEW SCREEN STRUCTURE:

1. TOP HEADER

Left:
AI-VibeCoders
/
AI Technical Interview

Center or right:
"Question 3 of 8+"

Right:
A subtle "Interview in progress" indicator.

Keep the header compact.

2. DESKTOP LAYOUT

Create a two-column layout.

LEFT:
A compact "Interview Journey" panel.

RIGHT:
The main conversation.

The conversation should receive most of the screen width.

3. INTERVIEW JOURNEY PANEL

Title:
"Interview Journey"

Show:

✓ Introduction
✓ Embeddings & Retrieval
● Prompt Engineering
○ Agents & MCP
○ Deployment

Below it show:

"3 of 8+ questions"

Use the Midnight Electric lime accent for:
- Completed states
- Active state
- Important progress indicators

Keep inactive items muted.

Do not show all 31 curriculum days.
Keep this focused on the interview topics.

4. CHAT AREA

Create realistic mock messages.

Start with:

AI:
"Let's talk about your experience with retrieval systems. Tell me about a RAG system you built."

Candidate:
"I built a RAG system that used hybrid search to retrieve technical documentation and answer complex domain questions."

AI follow-up:
"Interesting. Why did you choose that retrieval approach?"

Add 2-3 additional messages so the page feels like a real ongoing interview.

AI messages should have a subtle AI indicator/icon.

Candidate messages should visually feel different from AI messages.

Use the existing Midnight Electric design system.

5. CHAT INPUT

At the bottom of the conversation area create a prominent input area.

Placeholder:

"Type your answer..."

Include:
- text input / textarea
- send button
- keyboard-friendly interaction

The input should feel like the main interaction on the page.

Do not create voice controls or microphone buttons.

6. AI THINKING STATE

Create a reusable mock "AI thinking" state.

Example:

"AI is thinking..."

with three subtle animated dots.

This should NOT be permanently visible.

For now, create a small demo interaction or state that allows us to see the thinking animation.

7. INTERACTIONS

Implement basic frontend-only interactions:

- User can type in the input.
- Clicking Send adds the candidate message to the conversation.
- Pressing Enter should send the message, while Shift+Enter creates a new line.
- After sending, temporarily show "AI is thinking..."
- Then add a mock AI response after a short delay.
- Automatically scroll the conversation to the newest message.

This is only a frontend simulation.
Do NOT call an API.

8. MESSAGE ANIMATIONS

Use Framer Motion subtly.

When a new message appears:
- AI message should gently fade/slide in.
- Candidate message should gently fade/slide in.

Keep animations fast and professional.

9. QUESTION PROGRESS

Create a progress indicator at the top.

Example:

Question 3 of 8+

Add a thin progress bar underneath.

Use the electric lime accent for the completed portion.

For now, keep it mock/static.

10. MOBILE DESIGN

On mobile:
- Hide or collapse the Interview Journey panel.
- Keep the conversation as the main focus.
- Header should remain compact.
- Input should remain easily accessible.
- Do not make the user horizontally scroll.

11. UX QUALITY

The screen should feel like:
"Having a conversation with an intelligent technical interviewer."

It should NOT feel like:
- a developer monitoring console
- a form
- a chatbot toy
- a video interview platform

Keep it calm, focused, premium and professional.

IMPORTANT:
Do not add fake scores.
Do not add confidence percentages.
Do not add speaking metrics.
Do not add emotion analysis.
Do not add audio controls.

Use reusable React components.

Suggested components:

InterviewHeader
InterviewProgress
InterviewJourney
ChatWindow
MessageBubble
ThinkingIndicator
ChatInput

Make sure the existing Welcome page and Start Interview button navigate correctly to /interview.

After implementation:
1. Run the app.
2. Test the navigation.
3. Test typing and sending a message.
4. Test the thinking state.
5. Test responsive behavior.

10.
The interview interaction is working well.

Now make one focused UX improvement: add a clearly visible AI thinking state between the candidate sending an answer and the mock AI response appearing.

Do not redesign the Interview page.
Do not change the color palette.
Do not change the existing layout.

When the candidate presses Send:

1. Immediately add the candidate's message to the conversation.
2. Disable the input and Send button temporarily.
3. Show a small AI thinking indicator in the chat:

   AI Interviewer
   Thinking · · ·

4. Animate the three dots subtly using Framer Motion or CSS.
5. Keep the state visible for approximately 1–2 seconds.
6. Then hide the thinking indicator.
7. Add the mock AI response.
8. Re-enable the input.

The thinking state should feel like the AI is processing the candidate's answer, not like a loading spinner for the entire website.

Use the existing Midnight Electric visual language:
- subtle lime AI indicator
- dark surface
- muted text
- minimal animation

Also make sure:
- the conversation automatically scrolls to the thinking indicator
- then scrolls to the new AI message
- the candidate cannot accidentally send multiple messages while the AI is thinking

Do not connect to any backend.
Do not modify the Welcome page.
Do not build the report yet.

After implementing it, test the full sequence:
candidate types → Send → thinking indicator → AI response.

11.
We now have the Midnight Electric design system, Welcome page, and Interview screen.

The next major frontend feature is the final Interview Report / Review Dashboard.

IMPORTANT:
This is a TEXT-ONLY technical interview product.
There is no audio, video, microphone, camera, speech analysis, or facial analysis.

For this step, create ONLY the Report Dashboard frontend using mock/static data.

Do not connect to the backend yet.

Create a new /report route.

DESIGN GOAL:

The report should feel like a thoughtful post-interview review, not a generic analytics dashboard.

The candidate should immediately understand:

1. How did I perform?
2. What are my strongest areas?
3. Where should I improve?
4. How did I perform across the interview?
5. What happened on each question?
6. What should I work on next?

Keep the existing Midnight Electric visual identity:
- dark background
- electric lime primary accent
- soft mint secondary accent
- off-white text
- subtle borders
- restrained glow
- Plus Jakarta Sans
- JetBrains Mono for technical labels

PAGE STRUCTURE:

1. REPORT HEADER

Show:

"YOUR INTERVIEW REPORT"

Subtitle:
"Technical Interview · 8 questions · Completed today"

Add a small:
"Interview Complete ✓"

2. PERFORMANCE OVERVIEW

Create a prominent overall performance card.

Use mock data:
Overall Score: 78 / 100
Label: Strong

Alongside it show a performance snapshot with these example dimensions:

Technical Knowledge
Reasoning
Answer Quality
Problem Solving

Use simple visual bars rather than overly complicated charts.

IMPORTANT:
Clearly label these as mock/demo data in code so they can later be replaced by backend data.

3. TOPIC PERFORMANCE

Create a section showing performance by interview topic.

Example topics:

RAG
Embeddings
Prompting
Agents
MCP

Show each topic with:
- topic name
- performance indicator
- qualitative label

Use the Midnight Electric accent carefully.

4. INTERVIEW TIMELINE

Create a horizontal interview journey/timeline representing:

Q1 → Q2 → Q3 → Q4 → Q5 → Q6 → Q7 → Q8

Each question should have a state:
- Strong
- Good
- Needs improvement

Use subtle visual differences.

Make this responsive on smaller screens.

5. QUESTION-BY-QUESTION REVIEW

Create expandable/collapsible question review cards.

Each card should show:

Question number
Topic
Performance label
Short feedback summary

When expanded, show:

AI Question
Candidate Answer
AI Feedback

Then:

"What you did well"
"What to improve"
"Suggested next step"

Use mock content.

6. INTERACTIVE BEHAVIOR

Implement:

- Expand/collapse question cards
- Smooth animation when opening/closing
- Hover states
- Keyboard accessible controls
- Scroll-friendly layout

7. NEXT STEPS SECTION

At the bottom create:

"Recommended Next Steps"

Show 2-3 mock recommendations such as:

"Strengthen your understanding of hybrid retrieval."

"Practice explaining technical trade-offs."

"Review agent orchestration patterns."

8. RESPONSIVE DESIGN

Desktop:
Use a spacious dashboard layout.

Tablet:
Reduce columns.

Mobile:
Stack everything vertically.

The question review should be especially easy to use on mobile.

9. IMPORTANT UX RULES

Do NOT:
- create fake audio metrics
- create voice confidence metrics
- create facial analysis
- create microphone/camera controls
- overload the page with charts
- use random decorative AI graphics
- use excessive glassmorphism

This should feel like a professional AI interview review product.

Use reusable components.

Suggested structure:

ReportHeader
PerformanceOverview
TopicPerformance
InterviewTimeline
QuestionReview
NextSteps

Keep mock data separate from UI components so we can replace it with backend data later.

After implementation:
- run the application
- verify /report works
- verify question cards expand/collapse
- verify responsive behavior
- do not modify the existing Interview page unnecessarily.


12.
We now have the /report page working, but after visually reviewing it, it needs a significant UX/UI polish pass.

IMPORTANT:
Do NOT rebuild the page from scratch.
Do NOT change the Midnight Electric design system.
Do NOT change the existing Interview page.
Do NOT connect to the backend yet.
Keep using mock data.

The current report feels too plain and has too much empty space. Make it visually consistent with the polished AI interview screen.

GOAL:

Make the Report Dashboard feel like a premium AI technical interview analysis product.

The report should communicate information visually, not just through plain text and boxes.

--------------------------------------------------
1. REPORT HEADER
--------------------------------------------------

Keep:

YOUR INTERVIEW REPORT

Technical Interview · 8 questions · Completed today

Interview Complete ✓

Improve the hierarchy.

Add a subtle completion badge near the title.

Add a small secondary line such as:

"Here's how you performed across the interview."

Do not overdo it.

--------------------------------------------------
2. OVERALL PERFORMANCE CARD
--------------------------------------------------

The current Overall Performance card has too much empty space.

Redesign it.

Make 78/100 the visual centerpiece.

Use something like a circular/ring score visualization.

Example:

        78
       /100

      STRONG

The 78 should be large.

Use the Midnight Electric lime accent for the progress portion.

Use a subtle dark track for the remaining portion.

Add a small label:

Overall Performance

The card should have a meaningful visual hierarchy rather than empty space.

--------------------------------------------------
3. PERFORMANCE SNAPSHOT
--------------------------------------------------

The current percentages are only text.

Turn them into horizontal animated progress bars.

Show:

Technical Knowledge     80%
Reasoning               75%
Answer Quality          78%
Problem Solving         77%

Each row should contain:

label
percentage
progress bar

Use subtle animation when the page loads.

Do not use overly bright colors.

Use the existing Midnight Electric lime/mint palette.

--------------------------------------------------
4. TOPIC PERFORMANCE
--------------------------------------------------

Improve the existing topic cards.

Topics:

RAG
Embeddings
Prompting
Agents
MCP

Each card should include:

- topic name
- qualitative result
- visual progress indicator
- subtle hover state

Example:

RAG
Strong
████████████████░░

Prompting
Needs improvement
██████████░░░░░░░░

Make the cards compact and visually meaningful.

Avoid huge empty cards.

--------------------------------------------------
5. INTERVIEW TIMELINE
--------------------------------------------------

The current timeline is broken visually because:

Q1Q2Q3Q4Q5Q6Q7Q8

is appearing cramped together.

Fix this completely.

Create a proper horizontal timeline:

Q1 ─── Q2 ─── Q3 ─── Q4 ─── Q5 ─── Q6 ─── Q7 ─── Q8

Each question should be represented by a circular node.

Below each node show:

Q1
Q2
Q3
...

Each node should have a state:

Strong
Good
Needs improvement

Use subtle visual states while staying within the Midnight Electric palette.

On mobile, transform the timeline into a vertical timeline or horizontally scrollable timeline without breaking the layout.

--------------------------------------------------
6. QUESTION REVIEW
--------------------------------------------------

This is currently too minimal.

Create proper expandable review cards.

Each card should show:

Q1
RAG
Strong

with a small arrow/chevron.

When clicked, smoothly expand:

AI QUESTION

Why did you choose this retrieval approach?

YOUR ANSWER

I used...

AI FEEDBACK

Your answer demonstrated...

WHAT YOU DID WELL

✓ ...

WHAT TO IMPROVE

△ ...

SUGGESTED NEXT STEP

→ ...

Use clear visual hierarchy.

Only one card needs to be open at a time.

Add smooth expand/collapse animation.

Make the entire header clickable.

Make it keyboard accessible.

--------------------------------------------------
7. ADD A SMALL "KEY TAKEAWAYS" SECTION
--------------------------------------------------

Between Topic Performance and Question Review, add a compact section:

KEY TAKEAWAYS

Strengths
• Strong understanding of RAG
• Good technical reasoning

Focus Areas
• Explain trade-offs more clearly
• Strengthen agent orchestration concepts

This should be visually distinct but compact.

--------------------------------------------------
8. RECOMMENDED NEXT STEPS
--------------------------------------------------

Improve the current section.

Instead of just plain text, use 3 small actionable cards:

01
Strengthen hybrid retrieval

02
Practice explaining technical trade-offs

03
Review agent orchestration patterns

Each should have:

number
title
short explanation

Add subtle hover interaction.

--------------------------------------------------
9. PAGE LAYOUT
--------------------------------------------------

Use a clear hierarchy:

HEADER

        ↓

OVERALL PERFORMANCE
[ Score ] [ Performance Snapshot ]

        ↓

TOPIC PERFORMANCE

[ RAG ] [ Embeddings ] [ Prompting ]
[ Agents ] [ MCP ]

        ↓

KEY TAKEAWAYS

        ↓

INTERVIEW TIMELINE

        ↓

QUESTION REVIEW

        ↓

RECOMMENDED NEXT STEPS

The page should have consistent max-width and spacing.

Do not make every section full-width if it doesn't need to be.

--------------------------------------------------
10. RESPONSIVE DESIGN
--------------------------------------------------

Desktop:
Use two-column layouts where appropriate.

Tablet:
Reduce columns.

Mobile:
Stack cards vertically.

Make sure:

- no horizontal overflow
- timeline remains usable
- question cards remain readable
- score remains prominent
- buttons/cards are touch friendly

--------------------------------------------------
11. ANIMATION
--------------------------------------------------

Use restrained animation only:

- score ring animates into position
- progress bars animate from 0 to their values
- cards have subtle hover movement
- question accordion expands smoothly
- timeline nodes can fade/scale in

Do NOT add excessive animations.

The product should feel professional.

--------------------------------------------------
12. DESIGN CONSISTENCY
--------------------------------------------------

Preserve the existing Midnight Electric design system:

Background:
#080B0A

Primary Surface:
#101513

Secondary Surface:
#151B17

Primary Accent:
#C8FF3D

Secondary Accent:
#7DFFB2

Borders:
#263029

Continue using:

Plus Jakarta Sans
JetBrains Mono

Keep the existing subtle technical aesthetic.

Avoid:
- gradients everywhere
- excessive glassmorphism
- huge glowing effects
- random colors
- unnecessary illustrations
- fake AI imagery

--------------------------------------------------
13. IMPORTANT DATA RULE
--------------------------------------------------

Keep all report data in a separate mock data structure.

Do not hard-code data directly into every UI component.

Make it easy for us to later replace:

mockReportData

with real backend/API data.

Clearly mark the mock data so the backend team knows what needs to be replaced.

--------------------------------------------------
14. FINAL CHECK
--------------------------------------------------

After making the changes:

1. Run the app.
2. Open /report.
3. Verify the score visualization.
4. Verify progress bars.
5. Verify topic cards.
6. Verify timeline.
7. Click multiple question cards.
8. Verify only one question expands at a time.
9. Verify recommended next steps.
10. Test mobile width.
11. Make sure there is no horizontal overflow.

Do not modify the Interview screen.

13.
We now have these pages in the frontend:

1. Landing page
2. Interview page
3. Interview Complete page
4. ReportPage

I want the user journey to work naturally without manually typing URLs.

Please implement this flow:

Landing Page
→ clicking "Start Interview"
→ Interview Page

Interview Page
→ after the final question is submitted
→ Interview Complete Page

Interview Complete Page
→ clicking "View Interview Report →"
→ ReportPage

The report page should be accessible through the existing React route.

Do NOT redesign the UI or change the Midnight Electric design system.

Do NOT add backend functionality yet.

Just make sure the navigation between these pages works correctly using the existing routing setup.

Also make the "View Interview Report →" element clearly look clickable with hover and cursor interactions.

After making changes, tell me exactly which files you changed.

14.
The interview flow is already working correctly:

Landing → Interview → 8 questions completed → Interview Complete → View Interview Report → Report Page.

Do NOT change or break this navigation.

I now want to improve the architecture of the existing Report Page.

Currently the Report Page uses hardcoded/mock values such as:
- Overall score: 78
- Technical Knowledge: 80%
- Reasoning: 75%
- Answer Quality: 78%
- Problem Solving: 77%
- Topic scores for RAG, Embeddings, Prompting, Agents and MCP
- Question review data
- Recommended next steps

For this step, keep the existing UI and Midnight Electric visual design.

Create ONE centralized mock `reportData` object for the report instead of scattering these values throughout the JSX.

The structure should support:

1. Overall performance
   - overallScore
   - performanceLevel

2. Performance snapshot
   - technicalKnowledge
   - reasoning
   - answerQuality
   - problemSolving

3. Topic performance
   - topic name
   - score
   - performance level

4. Key takeaways
   - strengths
   - focusAreas

5. Interview timeline
   - question number
   - topic
   - score
   - performance level

6. Question review
   - question number
   - topic
   - question text
   - candidate answer
   - score
   - AI feedback
   - strengths
   - improvement suggestions

7. Recommended next steps
   - title
   - description

Use the mock data to render the existing Report Page.

IMPORTANT:
- Do not connect to a backend yet.
- Do not add API calls.
- Do not change the existing routing.
- Do not redesign the page.
- Do not remove the existing interactive elements.
- Keep the Midnight Electric colors, fonts, spacing and visual style.
- Keep the page responsive.
- Keep the current report values visually similar to what we already have.
- Make the data structure easy for us to replace later with real backend data.

Before changing anything, inspect the existing ReportPage.jsx and related components so you don't duplicate existing code.

After completing the work:
1. Tell me which files you changed.
2. Explain where the centralized `reportData` object is located.
3. Confirm that the Report Page still works through the existing "View Interview Report" button.


- Member 3 — Integration / Testing / Interview Engine 
# TASK 01: Build the Interview Engine Data Foundation

You are working on a 36-hour hackathon project called **AI Interview Agent**.

The goal is NOT to build a generic chatbot.

We are building an adaptive technical interviewer that:

* understands the candidate's actual learning journey
* understands the curriculum structure
* maintains an evolving model of the candidate's knowledge
* uses evidence from answers to decide what to ask next
* adapts difficulty and interview strategy dynamically

## IMPORTANT: USE THE PROVIDED DATA

The project already contains the official hackathon-provided:

1. **Curriculum JSON**
2. **Candidate Profile JSON**

DO NOT:

* create a new curriculum
* create mock curriculum data
* create a simplified replacement curriculum
* create fake candidate profiles
* hardcode candidate information
* change the source JSON structure unnecessarily
* invent curriculum days, topics, objectives, tools, or candidate history

First inspect the existing project and locate the actual curriculum JSON and candidate profile JSON files.

Treat those files as the source of truth.

Before writing implementation code, inspect their actual schemas and understand:

* how curriculum days/modules are represented
* how topics are represented
* how learning objectives are represented
* how tools are represented
* how candidate completion is represented
* how attempts are represented
* how skipped topics are represented
* what learning signals are available

Preserve the original data.

---

# OBJECTIVE

Implement the first foundation layer of the Interview Engine:

```text
Existing Curriculum JSON
          +
Existing Candidate Profile JSON
          ↓
   Candidate Context
          ↓
     Interview State
          ↓
   Candidate Knowledge Model
```

Do NOT implement question generation, answer analysis, or the full interview loop yet.

We are deliberately building the foundation first.

---

# 1. Create a Curriculum Context Layer

Build a small service/module that loads the existing curriculum JSON and exposes a normalized read-only representation for the interview engine.

The normalized representation should preserve all useful source information.

It should allow the engine to answer questions such as:

* What curriculum days exist?
* What module does a day belong to?
* What topics are covered?
* What are the learning objectives?
* What tools are associated with the topic?
* What concepts appear to be prerequisites for other concepts, IF such relationships can be derived safely from the provided curriculum.

Do NOT invent prerequisite relationships if they are not supported by the source data.

If prerequisite relationships are not explicitly present, leave them unavailable rather than fabricating them.

Example conceptual structure only:

```ts
CurriculumContext {
  days: [...]
  modules: [...]
  topics: [...]
  objectives: [...]
  tools: [...]
}
```

Adapt this to the ACTUAL JSON schema.

---

# 2. Create a Candidate Context Layer

Load the existing candidate profile JSON.

Do not modify the source candidate profile.

Create a read-only candidate context that allows the engine to understand:

* candidate identity/profile fields that are relevant to interviewing
* completed missions/days
* attempted missions
* skipped topics
* learning signals
* any other interview-relevant information actually present in the source file

Again:

DO NOT invent fields that don't exist.

If the candidate profile contains additional useful information, preserve it.

---

# 3. Create InterviewState

Create a runtime state object for ONE active interview.

This is NOT persistent long-term memory.

It represents the current interview session.

Design it so that it can eventually support:

```text
InterviewState
│
├── candidateContext
├── curriculumContext
├── interviewStatus
├── questionCount
├── coveredCurriculumDays
├── currentTopic
├── currentDifficulty
├── currentStrategy
├── conversation
├── knowledgeModel
├── misconceptions
├── evidenceLedger
└── interviewRequirements
```

Use the minimum necessary implementation now.

Do not over-engineer it.

The state must be serializable so that it can later be passed between API requests.

---

# 4. Create CandidateKnowledgeModel

This is the most important part of this task.

The candidate knowledge model represents what the Interview Engine currently believes about the candidate.

IMPORTANT:

This is NOT the same as the candidate profile.

The candidate profile tells us:

> what the candidate has done.

The knowledge model tells us:

> what the interviewer currently believes the candidate understands.

At interview start, the knowledge model should contain INITIAL HYPOTHESES derived only from the candidate profile and curriculum.

Do not pretend these are confirmed facts.

For example:

```ts
CandidateKnowledgeModel {
  topics: {
    [topicId]: {
      knowledgeConfidence: number | null,
      depthConfidence: number | null,
      reasoningConfidence: number | null,
      communicationConfidence: number | null,

      evidence: string[],

      status:
        | "unknown"
        | "hypothesized"
        | "developing"
        | "strong"
        | "weak"
    }
  },

  misconceptions: [],

  globalSignals: {
    communication: null,
    reasoning: null,
    confidence: null
  }
}
```

The exact schema is up to you after inspecting the existing project, but keep the following distinction:

### Profile evidence

Things explicitly known from the provided candidate JSON.

Example:

```text
Candidate skipped Day X.
```

### Interview evidence

Things discovered from actual candidate answers.

Example:

```text
Candidate could not explain ANN indexing.
```

Never mix these two.

---

# 5. Initial Knowledge State

At interview start, DO NOT assign arbitrary scores such as:

```text
RAG = 80%
Vector DB = 90%
Deployment = 40%
```

unless the source data actually provides evidence that supports such numerical values.

Instead use:

```text
unknown
hypothesized
```

or another appropriate representation.

The interview should UPDATE these beliefs based on evidence.

This is important because the system should behave like an interviewer forming hypotheses, not like a scoring system pretending to know the candidate before speaking to them.

---

# 6. Evidence Ledger

Create the structure now, but do not implement sophisticated evidence extraction yet.

The ledger should eventually allow us to say:

```text
Finding:
Candidate has strong understanding of RAG retrieval.

Evidence:
Q3
Q6
Q8
```

For now define the data structure.

Conceptually:

```ts
Evidence {
  id: string
  source: "candidate_profile" | "interview_answer"
  questionId?: string
  topicId?: string
  observation: string
  confidence?: number
  timestamp?: string
}
```

Adapt this to the project's existing architecture.

---

# 7. Interview Requirements

Store the hackathon constraints inside the interview state/configuration.

At minimum:

```text
minimumQuestions = 8
minimumCurriculumDays = 4
```

The state should track:

```text
questionsAsked
curriculumDaysCovered
```

so the future Strategy Engine can enforce the hackathon requirements.

Do not implement the Strategy Engine yet.

---

# 8. Architecture Requirements

Keep responsibilities separated.

Recommended structure:

```text
src/
  interview/
    context/
      curriculum-context
      candidate-context

    state/
      interview-state
      candidate-knowledge-model
      evidence-ledger

    types/
      ...

    services/
      ...
```

Adapt the folder structure to the existing project instead of blindly creating this exact structure.

Do not introduce unnecessary frameworks or dependencies.

Do not introduce a database.

Do not introduce a vector database.

Do not introduce RAG.

Do not introduce multi-agent orchestration yet.

We are building the foundation first.

---

# 9. Validation / Test

Create a small test or executable validation that loads the REAL provided curriculum and candidate JSON files and successfully produces:

```text
Candidate Context
+
Curriculum Context
+
Initial Interview State
+
Initial Candidate Knowledge Model
+
Empty Evidence Ledger
```

The validation should prove that:

1. The actual curriculum JSON can be loaded.
2. The actual candidate profile JSON can be loaded.
3. No source data is being replaced with mock data.
4. Interview state can be initialized.
5. The candidate knowledge model can be initialized.
6. The state can be serialized/deserialized.
7. The original source files remain unchanged.

Print a concise debug representation showing:

```text
Candidate loaded: YES
Curriculum loaded: YES

Curriculum days: <actual count>
Candidate completed: <actual count>
Candidate skipped: <actual count>

Interview state initialized: YES
Knowledge model initialized: YES
Evidence ledger initialized: YES
```

Use the actual values from the provided files.

---

# 10. IMPORTANT ENGINEERING PRINCIPLE

Do not build this as:

```text
JSON → LLM → everything
```

Build it as:

```text
SOURCE DATA
    ↓
STRUCTURED CONTEXT
    ↓
RUNTIME INTERVIEW STATE
    ↓
AI REASONING LAYERS
```

The source data and runtime state belong to the application.

The LLM/AI agent will later reason over this state.

The LLM must NOT become the database.

---

# 11. Do NOT implement yet

Do not implement:

* question generation
* answer analysis
* misconception detection
* strategy selection
* adaptive difficulty
* final feedback
* RAG
* vector database
* multi-agent system
* frontend
* chat UI
* authentication
* persistent accounts

Those come later.

---

# 12. Definition of Done

This task is complete ONLY when I can clearly demonstrate:

```text
REAL CURRICULUM JSON
        ↓
Curriculum Context
        +
REAL CANDIDATE JSON
        ↓
Candidate Context
        ↓
InterviewState
        ↓
CandidateKnowledgeModel
        ↓
EvidenceLedger
```

and the entire state can be serialized and restored without losing information.

After implementation, report back with:

1. Which existing curriculum JSON file you found.
2. Which existing candidate profile JSON file you found.
3. Their actual top-level schema/structure.
4. The files/modules you created or modified.
5. The final InterviewState schema.
6. The final CandidateKnowledgeModel schema.
7. How source facts are distinguished from interview-derived evidence.
8. The validation/test result.
9. Any assumptions you had to make.

Do not proceed to the next Interview Engine component until this foundation is working.

Proceed with the implementation plan, with these adjustments:

1. Do not model each curriculum day as a single "topic". A day is a curriculum unit containing objectives. Preserve the hierarchy:
   Module → Day → Objectives → Tools.

2. The CandidateKnowledgeModel should support future objective/concept-level evidence, while also maintaining an aggregate day-level view.

3. Keep all interview-derived confidence fields null during initialization. Do not infer numerical knowledge/depth/reasoning/communication scores from mission attempts.

4. Treat candidate-profile information only as initial hypotheses/evidence, never as confirmed technical knowledge.

5. Use CAND-003 as the development/default candidate for validation, but keep candidateId configurable and do not hardcode CAND-003 into the engine.

6. Preserve the original curriculum.json and candidates.json exactly. Do not modify either source file.

7. Do not implement any question generation, answer analysis, strategy engine, or LLM/agent logic yet. This task is only the data/context/state foundation.

After implementation, show me the resulting file tree and the actual serialized InterviewState for CAND-003.

## TASK 02: Build the Answer Analyzer

Step 1 of the Interview Engine is complete and validated.

We now have:

* real `curriculum.json`
* real `candidates.json`
* `CurriculumContext`
* `CandidateContext`
* `InterviewState`
* `CandidateKnowledgeModel`
* `EvidenceLedger`

Do NOT modify or recreate those source datasets.

The next component is the **Answer Analyzer**.

### Core principle

The Answer Analyzer answers:

> "What did we learn about the candidate from this answer?"

It must NOT decide the next question.

The future Strategy Engine will make that decision.

Architecture:

Candidate Answer
↓
Answer Analyzer
↓
Structured Assessment
↓
Candidate Knowledge Model Updater
↓
Evidence Ledger

Do NOT implement the Strategy Engine or Question Generator in this task.

---

# 1. Build AnswerAnalyzer

Create an `answer-analyzer` module/service that accepts:

```text
current question
candidate answer
relevant curriculum day
relevant curriculum objectives
current candidate knowledge model
previous relevant evidence
conversation context
```

Use the project's existing AI-agent/LLM integration if one already exists.

Do not introduce a new agent framework unnecessarily.

The analyzer should return strict structured JSON.

---

# 2. Assessment Schema

The output should contain:

```js
{
  assessment: {
    technicalAccuracy: number,
    conceptualDepth: number,
    reasoning: number,
    communication: number
  },

  understood: [
    {
      objectiveId: string,
      observation: string
    }
  ],

  missing: [
    {
      objectiveId: string,
      observation: string
    }
  ],

  uncertainties: [
    {
      objectiveId: string,
      observation: string
    }
  ],

  misconceptions: [
    {
      objectiveId: string,
      misconception: string,
      evidence: string,
      confidence: number
    }
  ],

  evidence: [
    {
      observation: string,
      objectiveIds: string[]
    }
  ],

  selfReportedConfidence: "low" | "medium" | "high" | "not_stated",

  confidenceMismatch: {
    detected: boolean,
    type: "overconfident" | "underconfident" | "none",
    explanation: string | null
  }
}
```

Use appropriate validation.

Scores must be normalized between 0 and 1 if numeric scores are used.

---

# 3. IMPORTANT: Objective-Level Analysis

Do not evaluate only at the curriculum-day level.

The curriculum contains 31 days and 155 objectives.

Given a question related to a particular day, identify which objectives the candidate's answer provides evidence for.

Example:

Day 10 contains objectives related to:

* query routing
* SQL retrieval
* semantic retrieval
* hybrid retrieval
* deduplication
* retrieval evaluation

If the candidate explains only semantic retrieval, the analyzer should NOT mark the entire Day 10 as understood.

It should produce something like:

```json
{
  "understood": [
    {
      "objectiveId": "day-10-obj-3",
      "observation": "Candidate correctly explained semantic retrieval using vector similarity."
    }
  ],

  "uncertainties": [
    {
      "objectiveId": "day-10-obj-1",
      "observation": "No evidence yet that the candidate understands query routing."
    }
  ]
}
```

Do not invent objective IDs. Use the IDs created by the Step 1 foundation.

---

# 4. Do Not Confuse Missing Evidence With Incorrect Knowledge

This distinction is critical.

If the candidate was never asked about hybrid retrieval:

DO NOT say:

"Candidate does not understand hybrid retrieval."

Instead say:

"Insufficient evidence to assess hybrid retrieval."

Use:

```text
unknown
```

or `uncertainties`.

Only identify a weakness when the candidate's actual answer provides evidence for it.

---

# 5. Misconception Detection

Detect conceptual misconceptions, not merely incorrect answers.

Example:

Candidate:

"Embeddings compress documents into smaller files."

Possible analyzer output:

```json
{
  "misconceptions": [
    {
      "objectiveId": "day-7-obj-1",
      "misconception": "Candidate appears to conflate semantic vector representation with data compression.",
      "evidence": "Candidate described embeddings primarily as a compression mechanism.",
      "confidence": 0.91
    }
  ]
}
```

Do not manufacture misconceptions from weak evidence.

If uncertain, place the observation under `uncertainties`.

---

# 6. Confidence Mismatch

Analyze the candidate's expressed confidence when it is actually stated.

Example:

Candidate:

"I'm not completely sure, but I think..."

If the technical answer is strong:

```json
{
  "selfReportedConfidence": "low",
  "confidenceMismatch": {
    "detected": true,
    "type": "underconfident",
    "explanation": "Candidate expressed uncertainty despite providing a technically strong explanation."
  }
}
```

If the candidate confidently states an incorrect concept:

```json
{
  "selfReportedConfidence": "high",
  "confidenceMismatch": {
    "detected": true,
    "type": "overconfident",
    "explanation": "Candidate expressed high confidence while demonstrating a significant conceptual misconception."
  }
}
```

Do not infer confidence from writing style alone.

Only use explicit or reasonably clear self-reported confidence.

---

# 7. Candidate Knowledge Model Updater

Create a separate updater.

Do NOT let the LLM directly mutate InterviewState.

Flow:

```text
LLM Answer Analyzer
        ↓
Structured Analysis
        ↓
Deterministic Updater
        ↓
CandidateKnowledgeModel
```

The updater should:

* attach evidence to relevant objective IDs
* update objective-level state
* update day-level aggregate state
* append misconceptions
* add evidence to the EvidenceLedger
* preserve previous evidence
* distinguish profile evidence from interview evidence

The updater should be deterministic wherever practical.

---

# 8. Confidence Updates

Do not invent a complicated mathematical model yet.

For this first implementation, create a clear update mechanism that can later evolve.

For example:

```text
No interview evidence
→ null

First strong evidence
→ initial confidence

Additional consistent evidence
→ confidence increases

Contradictory evidence
→ confidence decreases / becomes uncertain
```

Do not overwrite previous evidence.

The system must maintain an evidence trail explaining why a belief changed.

---

# 9. Preserve Source vs Interview Evidence

Existing Step 1 guarantees:

```text
candidate_profile
interview_answer
```

remain separate.

Continue that rule.

A candidate passing Day 10 is profile evidence.

A candidate correctly explaining semantic retrieval during Question 4 is interview evidence.

Never merge them into a single undifferentiated score.

---

# 10. Analyzer Prompt Design

Keep the LLM prompt focused.

The LLM should be instructed that:

* curriculum objectives are the evaluation reference
* candidate profile data is contextual evidence, not proof of technical mastery
* answer quality must be judged from the actual response
* lack of evidence is not evidence of weakness
* misconceptions require evidence
* output MUST follow the schema
* do not generate the next question
* do not provide final interview feedback
* do not make decisions about interview completion

Use structured output / JSON schema if supported by the existing AI agent.

---

# 11. Test Cases

Create tests using manually written answers for at least these cases:

### Test A: Strong answer

Should produce strong technical evidence.

### Test B: Partially correct answer

Should identify what was understood and what remains uncertain.

### Test C: Incorrect answer

Should identify the actual conceptual error.

### Test D: Confident but wrong

Should detect possible overconfidence mismatch.

### Test E: Uncertain but correct

Should detect possible underconfidence mismatch.

### Test F: Answer only covers one objective

Should NOT mark the entire curriculum day as understood.

### Test G: Off-topic answer

Should identify that the answer does not provide useful evidence for the requested objective.

### Test H: Ambiguous answer

Should prefer uncertainty over inventing a weakness.

---

# 12. Integration Test

Demonstrate this complete flow:

```text
Question
↓
Candidate Answer
↓
Answer Analyzer
↓
Structured Analysis
↓
Candidate Knowledge Model Update
↓
Evidence Ledger Update
```

Use a real curriculum day from `curriculum.json`.

Use CAND-003 as the initial test candidate.

After one answer, print:

```text
Question:
...

Answer:
...

Analysis:
...

Updated Objective State:
...

New Evidence:
...

Misconceptions:
...
```

---

# 13. Do NOT implement yet

Do not implement:

* Strategy Engine
* adaptive difficulty
* Question Generator
* interview planner
* final feedback generation
* RAG/vector database
* multi-agent orchestration
* frontend
* API changes unless absolutely required to expose/test this component

The goal is to make the Answer Analyzer reliable before building the decision-making layer.

---

# Definition of Done

This task is complete when:

1. A candidate answer can be analyzed against actual curriculum objectives.
2. The analyzer returns structured JSON.
3. Objective-level evidence is captured.
4. Missing evidence is distinguished from demonstrated weakness.
5. Misconceptions can be identified with supporting evidence.
6. Confidence mismatch can be detected when explicitly supported.
7. CandidateKnowledgeModel updates deterministically from analyzer output.
8. EvidenceLedger records interview evidence separately from profile evidence.
9. Previous evidence is preserved.
10. At least the 8 test scenarios pass.
11. Existing `curriculum.json` and `candidates.json` remain unchanged.
12. No Strategy Engine or Question Generator has been implemented yet.

After implementation, report:

* files created/modified
* analyzer schema
* updater logic
* prompt/system instructions used
* test results
* one complete example of before/after CandidateKnowledgeModel state
* one example of detected misconception
* one example of confidence mismatch

## TASK 1.5: Add the AI Runtime Layer

The Interview Engine data foundation is complete and validated.

Current architecture:

```text
curriculum.json
candidates.json
        ↓
CurriculumContext
CandidateContext
        ↓
InterviewState
        ↓
CandidateKnowledgeModel
        ↓
EvidenceLedger
```

There is currently NO LLM or AI agent integrated into the project.

Do NOT implement the Answer Analyzer yet.

We first need a clean AI Runtime abstraction that allows the Interview Engine to communicate with an AI model/agent without coupling the rest of the application to a specific provider.

---

# Goal

Create an AI Runtime interface/adapter layer.

Architecture:

```text
Interview Engine
       ↓
AI Runtime Interface
       ↓
Provider / Agent Adapter
       ↓
LLM / AI Agent
```

The Interview Engine should never directly depend on provider-specific SDK calls.

---

# 1. Inspect the existing repository first

Before coding:

* inspect package.json
* inspect existing src structure
* inspect current runtime/environment
* identify whether any AI SDK or agent framework is already installed
* identify the project's backend framework, if any
* do NOT install a new AI framework yet unless absolutely necessary

Do not modify the existing curriculum or candidate JSON files.

---

# 2. Create a provider-agnostic AI interface

Create a minimal interface capable of supporting future operations such as:

```text
generateText(...)
generateStructured(...)
```

The interface should accept structured input/context rather than forcing callers to construct provider-specific prompts.

Conceptually:

```js
aiRuntime.generateStructured({
  system,
  input,
  schema
})
```

The exact API should match the existing project's language and architecture.

---

# 3. Keep provider implementation separate

Create a provider adapter boundary.

Conceptually:

```text
src/
  ai/
    ai-runtime.js
    providers/
      ...
```

Do not hardcode a specific provider throughout the Interview Engine.

If no provider has been selected yet, create the interface and a clearly marked placeholder adapter rather than inventing credentials or fake API behavior.

---

# 4. Environment configuration

If an AI provider requires an API key:

* read it from environment variables
* never hardcode credentials
* never commit secrets
* add/update `.env.example`
* document the required environment variable

Do not put an actual API key into the repository.

---

# 5. Structured output support

The runtime must eventually support structured JSON responses because our Answer Analyzer will require machine-readable output.

Design for:

```text
AI response
      ↓
schema validation
      ↓
typed/validated object
```

Do not rely on parsing arbitrary natural-language AI output if structured output is available from the selected provider.

---

# 6. Minimal smoke test

Do NOT build the Interview Agent yet.

Create a tiny smoke test that verifies:

```text
Application
   ↓
AI Runtime
   ↓
Selected provider
   ↓
Simple structured response
   ↓
Schema validation
```

The test can ask something trivial such as:

```text
Return { "status": "ok" }
```

and verify that the returned object matches the expected schema.

This is only an integration test.

---

# 7. Important architectural rule

The AI model/agent must NOT own:

* InterviewState
* CandidateKnowledgeModel
* EvidenceLedger
* candidate data
* curriculum data
* session persistence

Those remain application-owned state.

The AI receives relevant context and returns structured reasoning/results.

Architecture:

```text
Application State
       │
       ▼
AI Runtime
       │
       ▼
Structured AI Result
       │
       ▼
Deterministic Application Update
```

The AI should not directly mutate state.

---

# 8. Do NOT implement

Do not implement yet:

* Answer Analyzer
* Strategy Engine
* Question Generator
* autonomous agent loop
* interview loop
* final evaluation
* RAG
* vector database
* multi-agent orchestration
* frontend
* API changes

This task is ONLY the AI Runtime integration boundary.

---

# 9. If an AI provider has not yet been selected

STOP before installing provider-specific dependencies.

Report:

1. Which AI providers/SDKs are currently available in the repository.
2. Which provider integration would be easiest to add.
3. What environment variable would be required.
4. What dependency would be installed.
5. Any architectural implications.

Do not make the provider decision silently.

---

# Definition of Done

The task is complete when:

1. The repository has a provider-agnostic AI Runtime interface.
2. Provider-specific code is isolated behind an adapter.
3. Structured output is supported.
4. Schema validation is supported.
5. Secrets use environment variables.
6. A minimal AI smoke test exists.
7. Existing InterviewState and CandidateKnowledgeModel remain AI-provider-independent.
8. `curriculum.json` and `candidates.json` remain unchanged.
9. No Answer Analyzer or interview logic has been implemented yet.

After implementation, report:

* files created/modified
* existing AI dependencies discovered
* provider selected, if any
* environment variables required
* example AI Runtime call
* smoke-test result
* final architecture

We are integrating the Interview Engine with the existing Python backend.

IMPORTANT:
Do NOT rewrite the existing backend.
Do NOT create a JavaScript implementation.
Do NOT duplicate CandidateState.
Do NOT modify candidates.json or curriculum.json.

The backend already contains a working Candidate Profile Parser and CandidateState in:

backend/models/interview.py
backend/services/candidate_profile_service.py
backend/services/session_manager.py
backend/api/interview.py

The existing Step 2A tests are passing. Treat this implementation as the source of truth.

## TASK: Align the Interview Engine with the existing Python backend

Build the following missing layers in Python:

1. CurriculumContext
2. InterviewState
3. CandidateKnowledgeModel
4. EvidenceLedger

### 1. CurriculumContext

Create a curriculum service that loads the existing canonical curriculum.json and preserves:

Module
→ Day
→ title/type/tools/objectives

The curriculum contains 31 days and 155 objectives.

Do NOT flatten a day into a single topic.

Objective IDs may use the existing Step 1 convention if already present. If not, create stable IDs such as:

day-10-obj-1

Do not invent prerequisite relationships.

### 2. InterviewState

Extend the existing session architecture rather than creating a second session model.

InterviewState should contain:

* session/interview ID
* CandidateState
* CurriculumContext
* conversation
* CandidateKnowledgeModel
* EvidenceLedger
* questions_asked
* covered_curriculum_days
* current_objective
* current_strategy
* current_difficulty
* interview_status
* interview requirements

Minimum requirements:

minimum_questions = 8
minimum_curriculum_days = 4

### 3. CandidateKnowledgeModel

This represents the interviewer's evolving belief about the candidate's technical understanding.

It is NOT CandidateState.

CandidateState = facts known from the candidate profile.

CandidateKnowledgeModel = beliefs derived from interview evidence.

At initialization:

* confidence fields must be null
* no technical score should be inferred from mission attempts
* completed/skipped/attempted missions may create initial hypotheses/evidence only

Support objective-level state as well as day-level aggregate state.

Example conceptual structure:

CandidateKnowledgeModel
→ days
→ day
→ objectives
→ objective assessment

Also support:

* misconceptions
* global communication/reasoning/confidence signals

### 4. EvidenceLedger

Create an evidence structure/service that preserves the source of every finding.

Sources must remain separate:

candidate_profile
interview_answer

Candidate profile example:

"Candidate completed Day 10 after two attempts."

Interview evidence example:

"Candidate correctly explained semantic retrieval."

Do not merge these.

Every interview-derived finding should be traceable to a question and, when possible, curriculum objective.

### 5. Integration

Update SessionManager so a newly created session contains:

CandidateState
+
CurriculumContext
+
initial CandidateKnowledgeModel
+
empty/current EvidenceLedger

Do not break the existing POST /api/interview contract.

Do not modify the API contract unless required by the existing implementation.

### 6. Important architectural boundary

Do NOT add an LLM or AI agent yet.

Do NOT implement:

* Answer Analyzer
* Strategy Engine
* Question Generator
* adaptive interview loop
* final evaluation

Those will be added after this foundation is aligned.

The eventual architecture will be:

API
→ SessionManager
→ InterviewState
→ AI Runtime
→ Answer Analyzer / Strategy Engine / Question Generator

The AI must never directly mutate InterviewState.

AI returns structured results.
Application code validates and applies those results.

### 7. Tests

Add tests for:

* curriculum loads correctly
* 31 days available
* 155 objectives available
* candidate state integrates correctly
* InterviewState initializes correctly
* all confidence values are null initially
* profile evidence and interview evidence remain separate
* state can be serialized/deserialized
* existing Step 2A tests still pass
* existing API tests still pass

Use CAND-003 for the development validation, but keep candidate selection configurable.

### 8. Source-of-truth check

The current Candidate Profile Service references:

backend/data/candidates.json

Confirm that this is the ONLY canonical candidates.json used by the backend.

If another copy exists, do not silently maintain two independent sources. Report the duplication and identify which file should be canonical.

Do the same check for curriculum.json.

## Definition of Done

When finished, show:

1. Updated file tree
2. Final Pydantic schemas
3. Final InterviewState structure
4. Example initialized InterviewState for CAND-003
5. CurriculumContext summary
6. KnowledgeModel summary
7. EvidenceLedger summary
8. Test results

Do not proceed to AI integration.

We need to consolidate the Interview Engine architecture.

IMPORTANT:
The current repository contains an earlier JavaScript Interview Engine foundation under:

src/interview/

The backend developer has now implemented the working Python backend under:

backend/

The Python backend is the implementation that will be used for the final hackathon submission.

DO NOT continue extending the JavaScript Interview Engine.

DO NOT create a second parallel implementation.

Treat the existing JavaScript implementation as an architectural reference only.

The concepts already designed in src/interview/ are:

- CandidateContext
- CurriculumContext
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger

The backend already has:

- CandidateState
- Candidate Profile Service
- Session Manager
- /api/interview
- Pydantic models
- passing backend tests

TASK:

1. Inspect the existing Python backend.
2. Inspect the existing JavaScript Interview Engine foundation.
3. Map the JavaScript concepts to the Python architecture.
4. Do NOT blindly port code.
5. Identify which concepts are already implemented by the backend.
6. Identify which concepts are missing.
7. Propose a migration/consolidation plan.

The desired final architecture is Python-first:

backend/
├── api/
├── models/
├── services/
├── agents/
├── data/
└── tests/

CandidateState should remain the representation of candidate profile facts.

CandidateKnowledgeModel should remain separate and represent evolving beliefs derived from interview evidence.

EvidenceLedger must distinguish:

candidate_profile
interview_answer

CurriculumContext must preserve:

Module
→ Day
→ Objectives
→ Tools

InterviewState must combine the runtime state without duplicating CandidateState.

DO NOT implement the AI agent yet.

DO NOT implement Answer Analyzer yet.

DO NOT delete the JavaScript implementation yet.

DO NOT modify curriculum.json or candidates.json.

Return:

1. Current Python architecture
2. Current JavaScript architecture
3. Mapping between them
4. Duplicate responsibilities
5. Missing components
6. Recommended final Python architecture
7. Exact files that should eventually be migrated/removed
8. Any risks or compatibility issues

We have now merged the backend developer's Python implementation into the Merin branch.

The Python backend is the canonical implementation for the final project.

Do NOT continue or extend the JavaScript implementation under src/interview/.
Do NOT delete it yet.
Treat it only as an architectural reference.

Current Python components already exist:

backend/models/interview.py
backend/services/candidate_profile_service.py
backend/services/curriculum_service.py
backend/services/interview_planner.py
backend/services/memory_service.py
backend/services/session_manager.py
backend/api/interview.py

Breeth memory integration already exists through MemoryService.

TASK: Consolidate and wire the deterministic Interview Engine foundation.

==================================================
1. KEEP EXISTING COMPONENTS
==================================================

Do not recreate:

- CandidateState
- CurriculumState
- CurriculumContext
- InterviewPlanner
- InterviewState
- CandidateKnowledgeModel
- EvidenceLedger
- MemoryService

Extend them where necessary.

Do not create parallel implementations.

==================================================
2. WIRE CURRICULUM + PLANNER INTO SESSION CREATION
==================================================

Currently SessionManager creates InterviewState with:

interview_plan=None

Change the initialization flow to:

candidate input
↓
CandidateState
↓
CurriculumState
↓
InterviewPlanner.plan_interview()
↓
InterviewPlan
↓
InterviewState

A new session should have its InterviewPlan attached to InterviewState.

Use the existing InterviewPlanner.

Do not create a second planner.

==================================================
3. OBJECTIVE-LEVEL KNOWLEDGE MODEL
==================================================

The current CandidateKnowledgeModel stores knowledge by curriculum day:

topics: Dict[int, CandidateTopicKnowledge]

This is too coarse for adaptive interviewing.

Refactor it carefully so knowledge can be tracked at objective level.

Desired conceptual structure:

CandidateKnowledgeModel
  ↓
days
  ↓
day
  ↓
objectives
  ↓
objective assessment

For example:

Day 10
  objective-1 → UNKNOWN
  objective-2 → STRONG
  objective-3 → UNKNOWN
  objective-4 → WEAK

Maintain a day-level aggregate assessment as well if useful.

Do not invent knowledge scores at initialization.

All initial technical confidence should remain unknown/null.

Candidate profile facts must not be treated as confirmed technical knowledge.

==================================================
4. PRESERVE EVIDENCE LEDGER
==================================================

Keep EvidenceLedger as the source of traceable interview evidence.

Every interview-derived evidence item should be associated with:

- session
- question
- candidate
- curriculum day
- objective when available
- candidate claim
- evidence
- assessment
- confidence
- turn

Do not merge profile evidence and interview evidence.

==================================================
5. BREETH ROLE
==================================================

MemoryService is already implemented for Breeth.

Keep Breeth as a memory layer.

Do NOT make Breeth responsible for:

- InterviewState
- CandidateKnowledgeModel
- InterviewPlan
- question count
- curriculum coverage
- deterministic state mutation

Those remain application-owned.

Breeth should later provide:

- storing interview episodes
- retrieving relevant prior interview context

Do not add new Breeth functionality in this task unless required for the existing architecture.

==================================================
6. API FLOW
==================================================

Do not implement the AI agent yet.

But make the deterministic flow ready for it.

First request:

POST /api/interview

candidate
↓
create session
↓
CandidateState
↓
CurriculumState
↓
InterviewPlan
↓
InterviewState

Subsequent request:

POST /api/interview

message
↓
retrieve session
↓
store conversation
↓
return control to future AI interviewer

For now the response can remain a placeholder.

==================================================
7. DO NOT IMPLEMENT YET
==================================================

Do NOT implement:

- Answer Analyzer
- AI agent
- Question Generator
- adaptive strategy
- LLM calls
- RAG
- vector database
- final feedback generation

Those are the next phase.

==================================================
8. SOURCE DATA
==================================================

There are currently:

candidates.json
backend/data/candidates.json

and:

curriculum.json
backend/data/curriculum.json

Verify whether the pairs are identical.

Do not silently maintain divergent copies.

Use the backend/data versions only if they are confirmed identical and are already the backend's canonical source.

Do not modify either dataset in this task.

==================================================
9. TESTS
==================================================

Update/add tests verifying:

1. CandidateState creation still works.
2. CurriculumState creation works.
3. InterviewPlanner creates a valid plan.
4. Session creation automatically creates InterviewPlan.
5. InterviewState contains the plan.
6. Minimum 8 question budget is enforced when possible.
7. At least 4 curriculum days are selected when the candidate has enough eligible completed days.
8. CandidateKnowledgeModel starts unknown.
9. Objective-level knowledge can be represented.
10. EvidenceLedger remains traceable.
11. Existing API tests still pass.
12. Existing Candidate Profile tests still pass.
13. Existing Curriculum tests still pass.
14. Breeth configuration remains unaffected.

==================================================
10. IMPORTANT
==================================================

Do not delete src/interview/.

Do not modify the original JSON source files.

Do not add an AI provider yet.

Do not add new frameworks.

Use the existing Python/Pydantic architecture.

After implementation, report:

- exact files changed
- final InterviewState schema
- final CandidateKnowledgeModel schema
- how InterviewPlanner is now wired
- sample InterviewPlan for CAND-003
- sample initialized InterviewState
- test results
- confirmation that source JSON files are unchanged

We have completed the deterministic Interview Engine foundation.

Current status:

- CandidateState ✅
- CurriculumState ✅
- CurriculumContext ✅
- InterviewPlanner ✅
- InterviewPlan attached to InterviewState ✅
- CandidateKnowledgeModel with objective-level representation ✅
- EvidenceLedger ✅
- Breeth MemoryService ✅
- SessionManager ✅
- FastAPI interview endpoint ✅
- 53/53 tests passing ✅

Do NOT refactor the deterministic foundation unless required for this task.

We are now beginning STEP 3: AI Answer Analyzer.

==================================================
GOAL
==================================================

Build the first AI capability:

Answer Analyzer

Its responsibility is to analyze a candidate's answer against the
current interview question and relevant curriculum objectives.

It must NOT generate the next question yet.

==================================================
ARCHITECTURE
==================================================

Candidate answer
      ↓
Answer Analyzer
      ↓
structured CandidateEvidenceAnalysis
      ↓
SessionManager.apply_evidence_analysis()
      ↓
CandidateKnowledgeModel
      +
EvidenceLedger

The LLM must NEVER directly mutate application state.

The LLM only returns validated structured analysis.

Python application code performs state mutation.

==================================================
INPUT TO ANALYZER
==================================================

The analyzer should receive:

- candidate_id
- candidate profile context
- current curriculum day
- current topic
- relevant curriculum objectives
- current question
- candidate answer
- relevant conversation history
- current knowledge state for the topic/objectives
- optionally relevant Breeth memories

Keep the context focused. Do not send the entire 31-day curriculum
unless necessary.

==================================================
OUTPUT
==================================================

Use the existing CandidateEvidenceAnalysis Pydantic model where possible.

The structured result must contain:

- curriculum_day
- topic
- understanding_assessment
- assessment_type
- confidence
- strengths
- gaps
- evidence_text
- candidate_claim
- follow_up_recommended

If objective-level evidence is supported by the existing model,
include objective_id.

If the current schema needs a minimal extension for objective-level
analysis, make that extension carefully and preserve backward
compatibility.

==================================================
ASSESSMENT RULES
==================================================

The analyzer should distinguish:

1. Correct understanding
2. Partially correct understanding
3. Incorrect understanding
4. Shallow understanding
5. Strong/deep understanding
6. Ambiguous answer requiring follow-up

Do NOT infer technical knowledge from:

- candidate profile
- completed missions
- number of attempts
- job title
- years of experience

Those are contextual signals only.

Technical assessment must come from the interview answer.

==================================================
PROMPT DESIGN
==================================================

Create a dedicated system prompt for the analyzer.

The prompt should instruct the model to:

- evaluate the answer against curriculum objectives
- avoid rewarding keyword matching
- distinguish memorization from understanding
- identify reasoning quality
- identify misconceptions
- provide evidence grounded in the actual answer
- avoid inventing claims
- return only the required structured output

The analyzer should behave like a technical interviewer,
not a tutor.

Do not reveal the correct answer to the candidate.

==================================================
MODEL / PROVIDER BOUNDARY
==================================================

Create a clean provider abstraction.

For example:

backend/agents/
    answer_analyzer.py

The analyzer should not hard-code application state mutation.

If an LLM provider is already configured in the project, reuse it.

If no provider is currently configured, create the analyzer behind
a clean interface and use a clearly documented configuration point
for the model/API key.

Do not add unnecessary frameworks.

==================================================
BREETH
==================================================

Do not make Breeth responsible for technical assessment.

Breeth is memory.

The analyzer may receive relevant retrieved memories as context,
but the analyzer remains responsible for analyzing the current answer.

Do not make Breeth mandatory for local unit tests.

==================================================
TESTING
==================================================

Add tests for:

1. Structured output validates against Pydantic schema.
2. Correct answer produces an appropriate positive assessment.
3. Partial answer can produce a gap.
4. Incorrect answer can produce a misconception/gap.
5. Analyzer does not mutate InterviewState directly.
6. apply_evidence_analysis() remains responsible for mutation.
7. EvidenceLedger receives traceable evidence.
8. KnowledgeModel is updated through the existing state update path.
9. Analyzer can work when Breeth is unavailable.
10. Existing 53 tests remain passing.

For unit tests, mock the LLM provider rather than making real
network calls.

==================================================
IMPORTANT
==================================================

Do NOT implement:

- next-question generation
- adaptive strategy
- full interview loop
- final feedback
- voice
- UI

Those come later.

The definition of done is:

Candidate answer
→ AI Answer Analyzer
→ validated CandidateEvidenceAnalysis
→ existing state update path

with tests proving the boundary works.

After implementation, report:

1. Files created/modified
2. LLM provider abstraction
3. Analyzer input schema
4. Analyzer output schema
5. System prompt
6. Example analysis for a sample RAG answer
7. How state mutation is protected from direct LLM mutation
8. Test results

"Build the Answer Analyzer on top of the existing Python backend. Do not modify the deterministic architecture unless required. Use the existing LLM Gateway abstraction if the backend developer has created it. The analyzer receives the current question, candidate answer, relevant curriculum objectives, current knowledge state, and relevant conversation/memory context. It returns validated CandidateEvidenceAnalysis. It must not mutate application state. Use mocked LLM responses in tests. Test excellent, shallow, partial, incorrect, and ambiguous answers. Keep Breeth optional through the existing MemoryService interface."




