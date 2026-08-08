/**
 * Candidate Knowledge Model
 *
 * This is the MOST IMPORTANT data structure in the Interview Engine.
 *
 * KEY DISTINCTION:
 * - CandidateContext = what the candidate HAS DONE (profile facts)
 * - CandidateKnowledgeModel = what the INTERVIEWER BELIEVES the candidate UNDERSTANDS
 *
 * At initialization:
 * - All interview-derived confidence fields are NULL
 * - No numerical knowledge/depth/reasoning/communication scores from mission attempts
 * - Profile data produces "hypothesized" status entries — never confirmed knowledge
 * - Days with no mission data → "unknown" status
 *
 * The model supports TWO levels of granularity:
 * 1. Day-level: aggregate view of knowledge per curriculum day
 * 2. Objective-level: granular view per learning objective within each day
 *
 * During the interview, evidence updates flow objective → day (bottom-up).
 */

const {
  createEvidenceLedger,
  createEvidence,
  addEvidence,
} = require('./evidence-ledger');

/**
 * Creates the initial knowledge model from candidate profile and curriculum.
 *
 * This produces HYPOTHESES, not confirmed knowledge. All confidence fields
 * are null. Status is either "unknown" or "hypothesized".
 *
 * @param {import('../types/candidate.types.js').CandidateContext} candidateContext
 * @param {import('../types/curriculum.types.js').CurriculumContext} curriculumContext
 * @returns {{ knowledgeModel: import('../types/interview.types.js').CandidateKnowledgeModel, evidenceLedger: import('../types/interview.types.js').EvidenceLedger }}
 */
function createInitialKnowledgeModel(candidateContext, curriculumContext) {
  let ledger = createEvidenceLedger();
  const days = {};

  for (const currDay of curriculumContext.days) {
    const mission = candidateContext.missionsByDay[currDay.day] || null;

    // --- Determine profile relationship and create day-level evidence ---
    let profileRelationship = 'not_attempted';
    let dayStatus = 'unknown';
    let dayEvidenceIds = [];

    if (mission) {
      if (mission.skipped) {
        profileRelationship = 'skipped';
        dayStatus = 'hypothesized';

        const ev = createEvidence({
          source: 'candidate_profile',
          dayNumber: currDay.day,
          observation: `Candidate skipped "${currDay.title}" (Day ${currDay.day}).`,
        });
        ledger = addEvidence(ledger, ev);
        dayEvidenceIds.push(ev.id);
      } else if (mission.passed === true) {
        profileRelationship = 'completed';
        dayStatus = 'hypothesized';

        const attemptNote =
          mission.attempts === 1
            ? 'on first attempt'
            : `after ${mission.attempts} attempts`;
        const ev = createEvidence({
          source: 'candidate_profile',
          dayNumber: currDay.day,
          observation: `Candidate passed "${currDay.title}" (Day ${currDay.day}) ${attemptNote}.`,
        });
        ledger = addEvidence(ledger, ev);
        dayEvidenceIds.push(ev.id);
      } else if (mission.passed === false) {
        profileRelationship = 'failed';
        dayStatus = 'hypothesized';

        const ev = createEvidence({
          source: 'candidate_profile',
          dayNumber: currDay.day,
          observation: `Candidate failed "${currDay.title}" (Day ${currDay.day}) after ${mission.attempts} attempts.`,
        });
        ledger = addEvidence(ledger, ev);
        dayEvidenceIds.push(ev.id);
      }
    }
    // If no mission data: profileRelationship stays "not_attempted", status stays "unknown"

    // --- Build objective-level knowledge entries ---
    const objectives = {};
    for (const obj of currDay.objectiveDetails) {
      objectives[obj.id] = {
        objectiveId: obj.id,
        objectiveText: obj.text,
        status: dayStatus, // inherits day status at initialization
        knowledgeConfidence: null, // null until interview evidence
        evidenceIds: [...dayEvidenceIds], // shares day-level evidence initially
      };
    }

    // --- Assemble day-level entry ---
    days[currDay.day] = {
      dayNumber: currDay.day,
      dayTitle: currDay.title,
      status: dayStatus,
      knowledgeConfidence: null,   // null — no interview evidence yet
      depthConfidence: null,       // null — no interview evidence yet
      reasoningConfidence: null,   // null — no interview evidence yet
      communicationConfidence: null, // null — no interview evidence yet
      evidenceIds: dayEvidenceIds,
      objectives,
      profileRelationship,
    };
  }

  const knowledgeModel = {
    days,
    misconceptions: [],
    globalSignals: {
      communication: null,
      reasoning: null,
      confidence: null,
    },
  };

  return { knowledgeModel, evidenceLedger: ledger };
}

module.exports = { createInitialKnowledgeModel };
