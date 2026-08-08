/**
 * Evidence Ledger
 *
 * Tracks all evidence gathered about a candidate's knowledge.
 * Evidence comes from two sources that must NEVER be mixed:
 *
 * 1. "candidate_profile" — facts derived from the source candidate JSON
 *    (e.g., "Candidate passed Day 7 on first attempt")
 *    These are INITIAL HYPOTHESES, not confirmed knowledge.
 *
 * 2. "interview_answer" — observations from actual interview responses
 *    (e.g., "Candidate could not explain ANN indexing")
 *    These are discovered during the interview session.
 */

let evidenceCounter = 0;

/**
 * Creates a new, empty evidence ledger.
 *
 * @returns {import('../types/interview.types.js').EvidenceLedger}
 */
function createEvidenceLedger() {
  return {
    entries: [],
    profileEvidenceCount: 0,
    interviewEvidenceCount: 0,
  };
}

/**
 * Creates a single evidence entry.
 *
 * @param {Object} params
 * @param {"candidate_profile" | "interview_answer"} params.source
 * @param {number|null} [params.dayNumber] - Curriculum day number
 * @param {string|null} [params.objectiveId] - Specific objective ID
 * @param {string|null} [params.questionId] - Question ID (for interview evidence)
 * @param {string} params.observation - Human-readable finding
 * @param {number|null} [params.confidence] - Confidence in this evidence
 * @returns {import('../types/interview.types.js').Evidence}
 */
function createEvidence({
  source,
  dayNumber = null,
  objectiveId = null,
  questionId = null,
  observation,
  confidence = null,
}) {
  evidenceCounter++;
  return {
    id: `ev-${Date.now()}-${evidenceCounter}`,
    source,
    questionId,
    dayNumber,
    objectiveId,
    observation,
    confidence,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Adds an evidence entry to the ledger. Returns the updated ledger.
 * (Does NOT mutate the original — returns a new ledger object.)
 *
 * @param {import('../types/interview.types.js').EvidenceLedger} ledger
 * @param {import('../types/interview.types.js').Evidence} evidence
 * @returns {import('../types/interview.types.js').EvidenceLedger}
 */
function addEvidence(ledger, evidence) {
  const newEntries = [...ledger.entries, evidence];
  return {
    entries: newEntries,
    profileEvidenceCount:
      ledger.profileEvidenceCount +
      (evidence.source === 'candidate_profile' ? 1 : 0),
    interviewEvidenceCount:
      ledger.interviewEvidenceCount +
      (evidence.source === 'interview_answer' ? 1 : 0),
  };
}

/**
 * Retrieves all evidence for a specific curriculum day.
 *
 * @param {import('../types/interview.types.js').EvidenceLedger} ledger
 * @param {number} dayNumber
 * @returns {import('../types/interview.types.js').Evidence[]}
 */
function getEvidenceByDay(ledger, dayNumber) {
  return ledger.entries.filter((e) => e.dayNumber === dayNumber);
}

/**
 * Retrieves all evidence for a specific objective.
 *
 * @param {import('../types/interview.types.js').EvidenceLedger} ledger
 * @param {string} objectiveId
 * @returns {import('../types/interview.types.js').Evidence[]}
 */
function getEvidenceByObjective(ledger, objectiveId) {
  return ledger.entries.filter((e) => e.objectiveId === objectiveId);
}

/**
 * Retrieves all evidence from a specific source.
 *
 * @param {import('../types/interview.types.js').EvidenceLedger} ledger
 * @param {"candidate_profile" | "interview_answer"} source
 * @returns {import('../types/interview.types.js').Evidence[]}
 */
function getEvidenceBySource(ledger, source) {
  return ledger.entries.filter((e) => e.source === source);
}

module.exports = {
  createEvidenceLedger,
  createEvidence,
  addEvidence,
  getEvidenceByDay,
  getEvidenceByObjective,
  getEvidenceBySource,
};
