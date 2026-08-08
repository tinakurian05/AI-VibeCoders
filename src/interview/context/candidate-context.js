/**
 * Candidate Context Layer
 *
 * Loads the existing candidates.json and produces a normalized, read-only
 * representation of a SINGLE candidate for the Interview Engine.
 *
 * IMPORTANT:
 * - Does NOT modify the source candidates.json file
 * - Does NOT invent fields not present in the source data
 * - Candidate profile represents what the candidate HAS DONE, not what they KNOW
 * - All derived fields come strictly from the source data
 */

const fs = require('fs');
const path = require('path');

/**
 * Loads a single candidate's context from the candidates JSON file.
 *
 * @param {string} filePath - Absolute or relative path to candidates.json
 * @param {string} candidateId - The candidate ID to load (e.g., "CAND-003")
 * @returns {Readonly<import('../types/candidate.types.js').CandidateContext>}
 * @throws {Error} If the candidate ID is not found
 */
function loadCandidateContext(filePath, candidateId) {
  const absolutePath = path.resolve(filePath);
  const raw = fs.readFileSync(absolutePath, 'utf-8');
  const source = JSON.parse(raw);

  // Find the requested candidate
  const candidateEntry = source.candidates.find(
    (c) => c.member.id === candidateId
  );

  if (!candidateEntry) {
    const availableIds = source.candidates.map((c) => c.member.id).join(', ');
    throw new Error(
      `Candidate "${candidateId}" not found. Available IDs: ${availableIds}`
    );
  }

  const { member, missions, signals } = candidateEntry;

  // --- Derive convenience arrays from missions ---
  const completedDays = [];
  const failedDays = [];
  const skippedDays = [];
  const attemptedDays = [];
  const missionsByDay = {};

  for (const mission of missions) {
    missionsByDay[mission.day] = mission;

    if (mission.skipped) {
      skippedDays.push(mission.day);
    } else if (mission.passed === true) {
      completedDays.push(mission.day);
      attemptedDays.push(mission.day);
    } else if (mission.passed === false) {
      failedDays.push(mission.day);
      attemptedDays.push(mission.day);
    }
  }

  // --- Assemble the context ---
  const context = {
    member: Object.freeze({ ...member }),
    missions: Object.freeze(missions.map((m) => Object.freeze({ ...m }))),
    signals: Object.freeze({ ...signals }),

    // Derived convenience fields
    completedDays: Object.freeze([...completedDays]),
    failedDays: Object.freeze([...failedDays]),
    skippedDays: Object.freeze([...skippedDays]),
    attemptedDays: Object.freeze([...attemptedDays]),
    missionsByDay: Object.freeze(missionsByDay),

    _meta: Object.freeze({
      totalMissions: missions.length,
      passedCount: completedDays.length,
      failedCount: failedDays.length,
      skippedCount: skippedDays.length,
      sourcePath: absolutePath,
    }),
  };

  return Object.freeze(context);
}

/**
 * Lists all available candidate IDs from the candidates JSON file.
 *
 * @param {string} filePath - Path to candidates.json
 * @returns {Array<{id: string, name: string, jobRole: string}>}
 */
function listCandidates(filePath) {
  const absolutePath = path.resolve(filePath);
  const raw = fs.readFileSync(absolutePath, 'utf-8');
  const source = JSON.parse(raw);

  return source.candidates.map((c) => ({
    id: c.member.id,
    name: c.member.name,
    jobRole: c.member.jobRole,
  }));
}

module.exports = { loadCandidateContext, listCandidates };
