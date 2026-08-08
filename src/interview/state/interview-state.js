/**
 * Interview State
 *
 * Runtime state for ONE active interview session.
 * This is NOT persistent long-term memory — it represents the current session.
 *
 * The state is fully serializable to JSON so it can be passed between
 * API requests or persisted temporarily during a session.
 */

const crypto = require('crypto');
const {
  createInitialKnowledgeModel,
} = require('./candidate-knowledge-model');

/**
 * Creates a new InterviewState for a candidate.
 *
 * @param {import('../types/candidate.types.js').CandidateContext} candidateContext
 * @param {import('../types/curriculum.types.js').CurriculumContext} curriculumContext
 * @returns {import('../types/interview.types.js').InterviewState}
 */
function createInterviewState(candidateContext, curriculumContext) {
  const { knowledgeModel, evidenceLedger } = createInitialKnowledgeModel(
    candidateContext,
    curriculumContext
  );

  return {
    interviewId: crypto.randomUUID(),
    startedAt: new Date().toISOString(),
    interviewStatus: 'not_started',

    // Context references
    candidateContext,
    curriculumContext,

    // Knowledge & evidence
    knowledgeModel,
    evidenceLedger,

    // Conversation state
    conversation: [],
    questionsAsked: 0,
    coveredCurriculumDays: [],
    currentTopic: null,
    currentDifficulty: null,
    currentStrategy: null,

    // Misconceptions
    misconceptions: [],

    // Hackathon requirements
    interviewRequirements: {
      minimumQuestions: 8,
      minimumCurriculumDays: 4,
    },
  };
}

/**
 * Serializes an InterviewState to a JSON string.
 * Strips internal metadata that can be reconstructed.
 *
 * @param {import('../types/interview.types.js').InterviewState} state
 * @returns {string}
 */
function serializeInterviewState(state) {
  return JSON.stringify(state, null, 2);
}

/**
 * Deserializes a JSON string back into an InterviewState.
 *
 * Note: The deserialized state is a plain object — it does not have
 * Object.freeze protections. The caller is responsible for treating
 * context fields as read-only.
 *
 * @param {string} json
 * @returns {import('../types/interview.types.js').InterviewState}
 */
function deserializeInterviewState(json) {
  return JSON.parse(json);
}

module.exports = {
  createInterviewState,
  serializeInterviewState,
  deserializeInterviewState,
};
