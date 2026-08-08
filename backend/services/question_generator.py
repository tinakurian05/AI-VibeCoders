import json
from typing import Optional

from services.llm_gateway import llm_gateway, LLMResponse
from models.question_generator import (
    QuestionGeneratorInput,
    GeneratedQuestion,
    QuestionGeneratorError,
    InterviewShouldEnd,
)
from models.interview import CandidateEvidenceAnalysis

SYSTEM_PROMPT = """You are a senior technical interviewer. Given a StrategyDecision and the surrounding interview context, generate ONE concise interview question in JSON format matching the GeneratedQuestion schema.

Rules:
- The StrategyDecision is authoritative. Follow its action (DEEPEN, FOLLOW_UP, CLARIFY, MOVE_TOPIC, CHANGE_DIFFICULTY).
- The question must target the specified target_day and target_objective (if any).
- Respect the difficulty level (EASY, MEDIUM, HARD) with appropriate depth.
- Use the candidate's recent answer/evidence to tailor the question; do NOT invent facts.
- Include any relevant memories only as background context; they must not override the recent evidence.
- If the decision indicates END (should_end=True), do NOT generate a question.
- Return ONLY a JSON object with fields: question_id, question, target_day, target_objective, difficulty, intent.
- Do NOT wrap the JSON in markdown code fences.
"""

class QuestionGenerator:
    def __init__(self, gateway: Optional[LLMResponse] = None):
        self.gateway = gateway or llm_gateway

    def _build_user_prompt(self, input_data: QuestionGeneratorInput) -> str:
        sd = input_data.strategy_decision
        lines = []
        lines.append(f"Strategy Action: {sd.action}\nDifficulty: {sd.difficulty}\nIntent: {sd.intent}\nTarget Day: {sd.target_day}\n")
        if sd.target_objective:
            lines.append(f"Target Objective: {sd.target_objective}\n")
        # Recent evidence (most recent item) for context
        if input_data.recent_evidence:
            latest = input_data.recent_evidence[-1]
            lines.append("Recent Evidence:\n")
            lines.append(f"- Claim: {latest.candidate_claim}\n")
            lines.append(f"- Evidence Text: {latest.evidence_text}\n")
        # Recent conversation (last two turns) for flavor
        if input_data.recent_conversation:
            lines.append("Recent Conversation Snippets:\n")
            recent = input_data.recent_conversation[-2:]
            for turn in recent:
                role = turn.get("role", "")
                content = turn.get("content", "")
                lines.append(f"{role}: {content}\n")
        # Optional memories
        if input_data.relevant_memories:
            lines.append("Relevant Memories (background):\n")
            for mem in input_data.relevant_memories:
                lines.append(f"- {mem}\n")
        return "".join(lines)

    def generate(self, input_data: QuestionGeneratorInput) -> GeneratedQuestion:
        # END handling
        if input_data.strategy_decision.should_end:
            raise InterviewShouldEnd("Strategy indicates interview should end.")

        user_prompt = self._build_user_prompt(input_data)
        try:
            response: LLMResponse = self.gateway.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.2,
            )
        except Exception as e:
            raise QuestionGeneratorError(f"LLM call failed: {e}")

        if not response.success:
            raise QuestionGeneratorError(
                f"LLM generation error: {response.error_category or 'unknown'}"
            )
        # Extract raw JSON – the LLM is instructed not to use markdown, but be defensive
        content = response.content.strip()
        try:
            # If the content is wrapped in code fences, strip them
            if content.startswith("```"):
                # simple removal of backticks and optional language tag
                content = "\n".join(content.splitlines()[1:-1]).strip()
            data = json.loads(content)
            generated = GeneratedQuestion(**data)
            return generated
        except json.JSONDecodeError as e:
            raise QuestionGeneratorError(f"Failed to parse LLM output as JSON: {e}")
        except Exception as e:
            raise QuestionGeneratorError(f"Invalid GeneratedQuestion data: {e}")
