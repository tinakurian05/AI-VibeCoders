/**
 * Interview Engine — Public API
 *
 * Barrel export for the Interview Engine data foundation.
 * This is the single entry point for consumers of the interview engine.
 */

// Context Layer
const {
  loadCurriculumContext,
} = require('./context/curriculum-context');
const {
  loadCandidateContext,
  listCandidates,
} = require('./context/candidate-context');

// State Layer
const {
  createInterviewState,
  serializeInterviewState,
  deserializeInterviewState,
} = require('./state/interview-state');
const {
  createInitialKnowledgeModel,
} = require('./state/candidate-knowledge-model');
const {
  createEvidenceLedger,
  createEvidence,
  addEvidence,
  getEvidenceByDay,
  getEvidenceByObjective,
  getEvidenceBySource,
} = require('./state/evidence-ledger');

module.exports = {
  // Context
  loadCurriculumContext,
  loadCandidateContext,
  listCandidates,

  // State
  createInterviewState,
  serializeInterviewState,
  deserializeInterviewState,
  createInitialKnowledgeModel,

  // Evidence
  createEvidenceLedger,
  createEvidence,
  addEvidence,
  getEvidenceByDay,
  getEvidenceByObjective,
  getEvidenceBySource,
};
