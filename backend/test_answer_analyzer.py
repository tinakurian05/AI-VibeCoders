import pytest
from unittest.mock import MagicMock
from models.analyzer import AnswerAnalyzerInput, AnalyzerError
from models.interview import CandidateTopicKnowledge, CandidateEvidenceAnalysis, LLMResponse, EvidenceLedger, CandidateKnowledgeModel, InterviewState
from services.answer_analyzer import AnswerAnalyzer

@pytest.fixture
def base_input():
    return AnswerAnalyzerInput(
        candidate_id="CAND-001",
        current_question="Why use RAG instead of fine-tuning?",
        candidate_answer="...",
        curriculum_day=21,
        topic="RAG",
        relevant_objectives=["Understand when to use RAG vs Fine-tuning"],
        current_topic_knowledge=CandidateTopicKnowledge(curriculum_day=21, topic="RAG"),
        conversation_history=[]
    )

def _create_mock_gateway(response_content: str, success: bool = True):
    mock_gateway = MagicMock()
    mock_response = LLMResponse(
        content=response_content,
        model_used="mock-model",
        success=success,
        error_category=None if success else "api_error"
    )
    mock_gateway.generate.return_value = mock_response
    return mock_gateway

def test_strong_answer(base_input):
    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "HIGH",
        "assessment_type": "supports_understanding",
        "confidence": 0.9,
        "strengths": ["Clear explanation"],
        "gaps": [],
        "evidence_text": "Evidence",
        "candidate_claim": "Claim",
        "follow_up_recommended": false
    }'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    
    result = analyzer.analyze(base_input)
    assert result.understanding_assessment == "HIGH"
    assert result.confidence == 0.9
    assert result.follow_up_recommended is False

def test_correct_but_shallow_answer(base_input):
    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "MEDIUM",
        "assessment_type": "supports_understanding",
        "confidence": 0.7,
        "strengths": ["Basic definition"],
        "gaps": ["Lacks depth"],
        "evidence_text": "Evidence",
        "candidate_claim": "Claim",
        "follow_up_recommended": true
    }'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    
    result = analyzer.analyze(base_input)
    assert result.understanding_assessment == "MEDIUM"
    assert result.follow_up_recommended is True

def test_partially_correct(base_input):
    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "MEDIUM",
        "assessment_type": "indicates_gap",
        "confidence": 0.8,
        "strengths": ["Part A"],
        "gaps": ["Missed Part B"],
        "evidence_text": "Evidence",
        "candidate_claim": "Claim",
        "follow_up_recommended": true
    }'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    
    result = analyzer.analyze(base_input)
    assert result.understanding_assessment == "MEDIUM"
    assert len(result.gaps) > 0

def test_incorrect_answer(base_input):
    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "LOW",
        "assessment_type": "indicates_gap",
        "confidence": 0.9,
        "strengths": [],
        "gaps": ["Completely misunderstood"],
        "evidence_text": "Evidence",
        "candidate_claim": "Claim",
        "follow_up_recommended": true
    }'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    
    result = analyzer.analyze(base_input)
    assert result.understanding_assessment == "LOW"
    assert len(result.strengths) == 0

def test_misconception(base_input):
    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "LOW",
        "assessment_type": "indicates_gap",
        "confidence": 0.85,
        "strengths": [],
        "gaps": ["Believes RAG trains the model"],
        "evidence_text": "Evidence",
        "candidate_claim": "Claim",
        "follow_up_recommended": true
    }'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    
    result = analyzer.analyze(base_input)
    assert "Believes RAG trains the model" in result.gaps

def test_ambiguous_answer(base_input):
    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "UNKNOWN",
        "assessment_type": "ambiguous",
        "confidence": 0.4,
        "strengths": [],
        "gaps": [],
        "evidence_text": "Vague response",
        "candidate_claim": "Claim",
        "follow_up_recommended": true
    }'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    
    result = analyzer.analyze(base_input)
    assert result.understanding_assessment == "UNKNOWN"

def test_valid_structured_output(base_input):
    # Already implicitly tested by others, but explicit check
    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "HIGH",
        "assessment_type": "supports_understanding",
        "confidence": 0.9,
        "strengths": [],
        "gaps": [],
        "evidence_text": "Ev",
        "candidate_claim": "Cl",
        "follow_up_recommended": false
    }'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    result = analyzer.analyze(base_input)
    assert isinstance(result, CandidateEvidenceAnalysis)

def test_markdown_json(base_input):
    mock_json = '''```json
{
    "curriculum_day": 21,
    "topic": "RAG",
    "understanding_assessment": "HIGH",
    "assessment_type": "supports_understanding",
    "confidence": 0.9,
    "strengths": [],
    "gaps": [],
    "evidence_text": "Ev",
    "candidate_claim": "Cl",
    "follow_up_recommended": false
}
```'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    result = analyzer.analyze(base_input)
    assert result.understanding_assessment == "HIGH"

def test_invalid_json(base_input):
    mock_json = "This is not JSON"
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    with pytest.raises(AnalyzerError, match="Failed to parse LLM output"):
        analyzer.analyze(base_input)

def test_llm_failure(base_input):
    gateway = _create_mock_gateway("irrelevant", success=False)
    analyzer = AnswerAnalyzer(gateway=gateway)
    with pytest.raises(AnalyzerError, match="LLM generation failed"):
        analyzer.analyze(base_input)

def test_no_state_mutation(base_input):
    mock_json = '''{
        "curriculum_day": 21,
        "topic": "RAG",
        "understanding_assessment": "HIGH",
        "assessment_type": "supports_understanding",
        "confidence": 0.9,
        "strengths": [],
        "gaps": [],
        "evidence_text": "Ev",
        "candidate_claim": "Cl",
        "follow_up_recommended": false
    }'''
    gateway = _create_mock_gateway(mock_json)
    analyzer = AnswerAnalyzer(gateway=gateway)
    
    # Snapshot the input topic knowledge before
    initial_level = base_input.current_topic_knowledge.understanding_level
    
    # We also mock SessionManager objects to verify they aren't touched, 
    # but AnswerAnalyzer literally takes AnswerAnalyzerInput, which contains no reference to SessionManager
    # We just ensure `current_topic_knowledge` wasn't mutated inline.
    
    analyzer.analyze(base_input)
    assert base_input.current_topic_knowledge.understanding_level == initial_level
