/**
 * Interview State & Knowledge Model Type Definitions
 *
 * KEY DISTINCTION:
 * - CandidateContext = what the candidate HAS DONE (profile facts)
 * - CandidateKnowledgeModel = what the INTERVIEWER BELIEVES the candidate UNDERSTANDS
 *
 * At initialization, all beliefs are either "unknown" or "hypothesized" based
 * on profile evidence. They are NEVER treated as confirmed technical knowledge.
 * Interview-derived confidence fields are always null until actual interview
 * evidence is collected.
 */

/**
 * Knowledge status for a topic/objective.
 * @typedef {"unknown" | "hypothesized" | "developing" | "strong" | "weak"} KnowledgeStatus
 */

/**
 * Knowledge belief about a single curriculum objective.
 *
 * @typedef {Object} ObjectiveKnowledge
 * @property {string} objectiveId - The objective ID (e.g., "day-7-obj-0")
 * @property {string} objectiveText - The objective text
 * @property {KnowledgeStatus} status - Current knowledge status
 * @property {number|null} knowledgeConfidence - null until interview evidence exists
 * @property {string[]} evidenceIds - IDs of evidence entries supporting this belief
 */

/**
 * Knowledge belief about a single curriculum day (aggregate of its objectives).
 *
 * @typedef {Object} DayKnowledge
 * @property {number} dayNumber - Curriculum day number
 * @property {string} dayTitle - Day title
 * @property {KnowledgeStatus} status - Aggregate status for this day
 * @property {number|null} knowledgeConfidence - null until interview evidence exists
 * @property {number|null} depthConfidence - null until interview evidence exists
 * @property {number|null} reasoningConfidence - null until interview evidence exists
 * @property {number|null} communicationConfidence - null until interview evidence exists
 * @property {string[]} evidenceIds - IDs of evidence entries at the day level
 * @property {Object<string, ObjectiveKnowledge>} objectives - Objective-level beliefs keyed by objective ID
 * @property {string} profileRelationship - "completed"|"failed"|"skipped"|"not_attempted"
 */

/**
 * The interviewer's evolving belief model about the candidate's knowledge.
 *
 * @typedef {Object} CandidateKnowledgeModel
 * @property {Object<number, DayKnowledge>} days - Day-level knowledge beliefs keyed by day number
 * @property {Array} misconceptions - Discovered misconceptions (empty at initialization)
 * @property {Object} globalSignals - Global interview-derived signals
 * @property {number|null} globalSignals.communication - null until interview evidence
 * @property {number|null} globalSignals.reasoning - null until interview evidence
 * @property {number|null} globalSignals.confidence - null until interview evidence
 */

/**
 * A single piece of evidence supporting a knowledge belief.
 *
 * @typedef {Object} Evidence
 * @property {string} id - Unique evidence ID
 * @property {"candidate_profile" | "interview_answer"} source - Where this evidence came from
 * @property {string|null} questionId - Question ID (null for profile-sourced evidence)
 * @property {number|null} dayNumber - Curriculum day number this evidence relates to
 * @property {string|null} objectiveId - Specific objective ID (null if day-level)
 * @property {string} observation - Human-readable description of the finding
 * @property {number|null} confidence - Confidence in this evidence (null at initialization)
 * @property {string} timestamp - ISO 8601 timestamp
 */

/**
 * Collection of all evidence gathered during an interview.
 *
 * @typedef {Object} EvidenceLedger
 * @property {Evidence[]} entries - All evidence entries
 * @property {number} profileEvidenceCount - Count of candidate_profile entries
 * @property {number} interviewEvidenceCount - Count of interview_answer entries
 */

/**
 * Hackathon interview constraints.
 *
 * @typedef {Object} InterviewRequirements
 * @property {number} minimumQuestions - Minimum questions to ask (8)
 * @property {number} minimumCurriculumDays - Minimum curriculum days to cover (4)
 */

/**
 * Runtime state for one active interview session.
 * Serializable to JSON for passing between API requests.
 *
 * @typedef {Object} InterviewState
 * @property {string} interviewId - Unique session ID
 * @property {string} startedAt - ISO 8601 timestamp
 * @property {"not_started" | "in_progress" | "completed"} interviewStatus - Current status
 * @property {CandidateContext} candidateContext - Frozen candidate context
 * @property {CurriculumContext} curriculumContext - Frozen curriculum context
 * @property {CandidateKnowledgeModel} knowledgeModel - Evolving knowledge beliefs
 * @property {EvidenceLedger} evidenceLedger - All gathered evidence
 * @property {Array} conversation - Conversation history (empty at initialization)
 * @property {number} questionsAsked - Count of questions asked so far
 * @property {number[]} coveredCurriculumDays - Day numbers covered during the interview
 * @property {number|null} currentTopic - Current day number being discussed
 * @property {string|null} currentDifficulty - Current difficulty level
 * @property {string|null} currentStrategy - Current interview strategy
 * @property {Array} misconceptions - Discovered misconceptions (mirrors knowledgeModel)
 * @property {InterviewRequirements} interviewRequirements - Hackathon constraints
 */

module.exports = {};
