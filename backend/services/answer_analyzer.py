import json
import re
from typing import Optional
from pydantic import ValidationError
from services.llm_gateway import llm_gateway, LLMGateway
from models.interview import CandidateEvidenceAnalysis
from models.analyzer import AnswerAnalyzerInput, AnalyzerError

SYSTEM_PROMPT = """You are a rigorous technical interview evidence evaluator.
Your ONLY job is to evaluate a candidate's answer against the supplied curriculum topic and learning objectives, and extract evidence about the candidate's technical understanding.

CRITICAL RULES:
1. Judge ACTUAL demonstrated understanding, not just keyword matching.
2. Distinguish between:
   - HIGH: Strong understanding, technically correct, well-reasoned.
   - MEDIUM: Partial understanding, correct but shallow.
   - LOW: Weak understanding, incorrect, or misconception.
   - UNKNOWN: Ambiguous or inconclusive evidence.
3. Identify concrete strengths (what they clearly understand).
4. Identify concrete gaps (what they missed, got wrong, or did not demonstrate).
5. Extract evidence precisely from what the candidate actually said.
6. NEVER invent claims. NEVER assume knowledge that was not explicitly demonstrated.
7. Treat candidate profile information/history as context only, NOT confirmed technical knowledge.
8. NEVER infer technical mastery just because a candidate completed a mission, has years of experience, or has a senior job title.
9. Do NOT provide the correct answer to the candidate.
10. Do NOT generate the next interview question. Do NOT decide the interview strategy.
11. 'follow_up_recommended' should be true if there is a gap, misconception, partial understanding, ambiguity, or untested objectives.
12. Your output MUST be valid JSON matching the exact schema provided. Do not include markdown formatting or extra text outside the JSON.

JSON SCHEMA:
{
    "curriculum_day": int,
    "topic": "string",
    "understanding_assessment": "HIGH|MEDIUM|LOW|UNKNOWN",
    "assessment_type": "supports_understanding|indicates_gap|ambiguous|needs_follow_up",
    "confidence": float (0.0 to 1.0),
    "strengths": ["list of strings"],
    "gaps": ["list of strings"],
    "evidence_text": "Summary of what the candidate demonstrated",
    "candidate_claim": "The core technical claim made by the candidate",
    "follow_up_recommended": boolean
}
"""

class AnswerAnalyzer:
    def __init__(self, gateway: Optional[LLMGateway] = None):
        self.gateway = gateway or llm_gateway

    def _build_user_prompt(self, input_data: AnswerAnalyzerInput) -> str:
        prompt = f"Candidate ID: {input_data.candidate_id}\n"
        prompt += f"Curriculum Day: {input_data.curriculum_day}\n"
        prompt += f"Topic: {input_data.topic}\n"
        
        prompt += "Relevant Objectives:\n"
        for obj in input_data.relevant_objectives:
            prompt += f"- {obj}\n"
            
        prompt += f"\nCurrent Question: {input_data.current_question}\n"
        prompt += f"Candidate Answer: {input_data.candidate_answer}\n"
        
        return prompt

    def _extract_json(self, content: str) -> str:
        """Extract JSON from markdown code blocks if present."""
        content = content.strip()
        match = re.search(r'```(?:json)?(.*?)```', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content

    def analyze(self, input_data: AnswerAnalyzerInput) -> CandidateEvidenceAnalysis:
        user_prompt = self._build_user_prompt(input_data)
        
        response = self.gateway.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2
        )
        
        if not response.success:
            raise AnalyzerError(f"LLM generation failed: {response.error_category}")
            
        try:
            json_str = self._extract_json(response.content)
            parsed_data = json.loads(json_str)
            return CandidateEvidenceAnalysis(**parsed_data)
        except json.JSONDecodeError as e:
            raise AnalyzerError(f"Failed to parse LLM output as JSON: {e}")
        except ValidationError as e:
            raise AnalyzerError(f"LLM output failed schema validation: {e}")
        except Exception as e:
            raise AnalyzerError(f"Unexpected error during analysis: {e}")
