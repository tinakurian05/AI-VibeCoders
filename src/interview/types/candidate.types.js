/**
 * Candidate Type Definitions
 *
 * These types mirror the source candidates.json structure
 * and add derived convenience fields for the interview engine.
 *
 * IMPORTANT: Candidate profile data represents what the candidate HAS DONE.
 * It does NOT represent what the candidate KNOWS. That distinction belongs
 * to the CandidateKnowledgeModel.
 */

/**
 * Candidate identity and professional information.
 * Matches the source "member" object exactly.
 *
 * @typedef {Object} CandidateMember
 * @property {string} id - Candidate ID (e.g., "CAND-003")
 * @property {string} name - Full name
 * @property {string} jobRole - Current/recent job role
 * @property {number} yearsExperience - Years of professional experience
 * @property {string} education - Education background
 * @property {string} status - Completion status (e.g., "COMPLETED")
 */

/**
 * A single mission (curriculum day attempt) from the candidate's profile.
 *
 * Three possible states:
 * - Passed: { passed: true, attempts: N }
 * - Failed: { passed: false, attempts: N }
 * - Skipped: { skipped: true }
 *
 * @typedef {Object} CandidateMission
 * @property {number} day - Curriculum day number
 * @property {string} title - Mission title
 * @property {boolean} [passed] - Whether the mission was passed (absent when skipped)
 * @property {number} [attempts] - Number of attempts (absent when skipped)
 * @property {boolean} [skipped] - Whether the mission was skipped (absent when attempted)
 */

/**
 * Aggregate learning behavior signals from the candidate's profile.
 *
 * @typedef {Object} CandidateSignals
 * @property {number} commitDays - Number of days the candidate committed to
 * @property {number} missionsCompleted - Total missions completed
 * @property {number} missionsFirstTry - Missions completed on first attempt
 */

/**
 * The normalized, read-only candidate context for the interview engine.
 *
 * @typedef {Object} CandidateContext
 * @property {CandidateMember} member - Candidate identity/profile
 * @property {CandidateMission[]} missions - All mission entries from the source
 * @property {CandidateSignals} signals - Aggregate learning signals
 * @property {number[]} completedDays - Day numbers where passed === true (derived)
 * @property {number[]} failedDays - Day numbers where passed === false (derived)
 * @property {number[]} skippedDays - Day numbers where skipped === true (derived)
 * @property {number[]} attemptedDays - Day numbers where attempts exist, regardless of outcome (derived)
 * @property {Object<number, CandidateMission>} missionsByDay - Map: day number → mission (derived)
 * @property {Object} _meta - Metadata about this context
 * @property {number} _meta.totalMissions - Total mission entries
 * @property {number} _meta.passedCount - Number of passed missions
 * @property {number} _meta.failedCount - Number of failed missions
 * @property {number} _meta.skippedCount - Number of skipped missions
 */

module.exports = {};
