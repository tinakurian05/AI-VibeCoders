/**
 * Interview Engine — Validation Script
 *
 * Proves the data foundation works by:
 * 1. Loading the REAL curriculum.json
 * 2. Loading the REAL candidates.json (CAND-003 by default, configurable via CLI arg)
 * 3. Creating InterviewState with initial CandidateKnowledgeModel
 * 4. Serializing → deserializing → verifying no data loss
 * 5. Verifying source files remain unchanged
 *
 * Usage:
 *   node src/validate.js              # Uses CAND-003 (Emily Chen)
 *   node src/validate.js CAND-001     # Uses a specific candidate
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const {
  loadCurriculumContext,
  loadCandidateContext,
  listCandidates,
  createInterviewState,
  serializeInterviewState,
  deserializeInterviewState,
  getEvidenceBySource,
} = require('./interview/index');

// ─── Configuration ───────────────────────────────────────────────────────────
const PROJECT_ROOT = path.resolve(__dirname, '..');
const CURRICULUM_PATH = path.join(PROJECT_ROOT, 'curriculum.json');
const CANDIDATES_PATH = path.join(PROJECT_ROOT, 'candidates.json');
const DEFAULT_CANDIDATE_ID = 'CAND-003';

const candidateId = process.argv[2] || DEFAULT_CANDIDATE_ID;

// ─── Helpers ─────────────────────────────────────────────────────────────────
function fileHash(filePath) {
  const content = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

function check(label, passed) {
  const status = passed ? '✅ YES' : '❌ NO';
  console.log(`  ${label}: ${status}`);
  return passed;
}

function separator(title) {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  ${title}`);
  console.log('═'.repeat(60));
}

// ─── Main Validation ─────────────────────────────────────────────────────────
function validate() {
  let allPassed = true;

  // Record source file hashes BEFORE loading
  const curriculumHashBefore = fileHash(CURRICULUM_PATH);
  const candidatesHashBefore = fileHash(CANDIDATES_PATH);

  separator('1. LOADING SOURCE DATA');

  // Load curriculum
  let curriculumContext;
  try {
    curriculumContext = loadCurriculumContext(CURRICULUM_PATH);
    allPassed &= check('Curriculum loaded', true);
  } catch (err) {
    check('Curriculum loaded', false);
    console.error(`     Error: ${err.message}`);
    return;
  }

  // Load candidate
  let candidateContext;
  try {
    candidateContext = loadCandidateContext(CANDIDATES_PATH, candidateId);
    allPassed &= check('Candidate loaded', true);
  } catch (err) {
    check('Candidate loaded', false);
    console.error(`     Error: ${err.message}`);
    console.log('\n  Available candidates:');
    listCandidates(CANDIDATES_PATH).forEach((c) => {
      console.log(`    ${c.id} — ${c.name} (${c.jobRole})`);
    });
    return;
  }

  separator('2. SOURCE DATA SUMMARY');

  console.log(`  Candidate:       ${candidateContext.member.name} (${candidateContext.member.id})`);
  console.log(`  Job Role:        ${candidateContext.member.jobRole}`);
  console.log(`  Experience:      ${candidateContext.member.yearsExperience} years`);
  console.log(`  Education:       ${candidateContext.member.education}`);
  console.log('');
  console.log(`  Curriculum days: ${curriculumContext._meta.totalDays}`);
  console.log(`  Modules:         ${curriculumContext._meta.totalModules}`);
  console.log(`  Total objectives:${curriculumContext._meta.totalObjectives}`);
  console.log(`  Unique tools:    ${curriculumContext._meta.totalUniqueTools}`);
  console.log('');
  console.log(`  Missions total:  ${candidateContext._meta.totalMissions}`);
  console.log(`  Completed:       ${candidateContext._meta.passedCount}`);
  console.log(`  Failed:          ${candidateContext._meta.failedCount}`);
  console.log(`  Skipped:         ${candidateContext._meta.skippedCount}`);
  console.log('');
  console.log(`  Completed days:  [${candidateContext.completedDays.join(', ')}]`);
  console.log(`  Skipped days:    [${candidateContext.skippedDays.join(', ')}]`);
  console.log(`  Failed days:     [${candidateContext.failedDays.join(', ')}]`);

  separator('3. INTERVIEW STATE INITIALIZATION');

  let state;
  try {
    state = createInterviewState(candidateContext, curriculumContext);
    allPassed &= check('Interview state initialized', true);
  } catch (err) {
    check('Interview state initialized', false);
    console.error(`     Error: ${err.message}`);
    return;
  }

  allPassed &= check('Knowledge model initialized', !!state.knowledgeModel);
  allPassed &= check('Evidence ledger initialized', !!state.evidenceLedger);

  // Knowledge model summary
  const kmDays = Object.values(state.knowledgeModel.days);
  const hypothesized = kmDays.filter((d) => d.status === 'hypothesized').length;
  const unknown = kmDays.filter((d) => d.status === 'unknown').length;

  console.log('');
  console.log(`  Knowledge model days:  ${kmDays.length}`);
  console.log(`    ├─ hypothesized:     ${hypothesized}`);
  console.log(`    └─ unknown:          ${unknown}`);

  // Count objectives
  let totalObjEntries = 0;
  for (const dayKnowledge of kmDays) {
    totalObjEntries += Object.keys(dayKnowledge.objectives).length;
  }
  console.log(`  Objective-level entries: ${totalObjEntries}`);

  // Evidence summary
  const profileEvidence = getEvidenceBySource(state.evidenceLedger, 'candidate_profile');
  const interviewEvidence = getEvidenceBySource(state.evidenceLedger, 'interview_answer');
  console.log('');
  console.log(`  Evidence entries:       ${state.evidenceLedger.entries.length}`);
  console.log(`    ├─ from profile:      ${profileEvidence.length}`);
  console.log(`    └─ from interview:    ${interviewEvidence.length}`);

  // Verify all confidence fields are null
  let allConfidenceNull = true;
  for (const dayKnowledge of kmDays) {
    if (
      dayKnowledge.knowledgeConfidence !== null ||
      dayKnowledge.depthConfidence !== null ||
      dayKnowledge.reasoningConfidence !== null ||
      dayKnowledge.communicationConfidence !== null
    ) {
      allConfidenceNull = false;
      break;
    }
    for (const obj of Object.values(dayKnowledge.objectives)) {
      if (obj.knowledgeConfidence !== null) {
        allConfidenceNull = false;
        break;
      }
    }
  }
  allPassed &= check('All confidence fields null (no premature scores)', allConfidenceNull);

  // Verify global signals are null
  const gs = state.knowledgeModel.globalSignals;
  allPassed &= check(
    'Global signals null (no premature assessment)',
    gs.communication === null && gs.reasoning === null && gs.confidence === null
  );

  // Verify interview requirements
  allPassed &= check(
    'Interview requirements set',
    state.interviewRequirements.minimumQuestions === 8 &&
      state.interviewRequirements.minimumCurriculumDays === 4
  );

  separator('4. SERIALIZATION ROUND-TRIP');

  const serialized = serializeInterviewState(state);
  const deserialized = deserializeInterviewState(serialized);
  const reSerialized = serializeInterviewState(deserialized);

  const roundTripMatch = serialized === reSerialized;
  allPassed &= check('Serialization round-trip', roundTripMatch);
  console.log(`  Serialized size: ${(Buffer.byteLength(serialized) / 1024).toFixed(1)} KB`);

  separator('5. SOURCE FILE INTEGRITY');

  const curriculumHashAfter = fileHash(CURRICULUM_PATH);
  const candidatesHashAfter = fileHash(CANDIDATES_PATH);

  allPassed &= check(
    'curriculum.json unchanged',
    curriculumHashBefore === curriculumHashAfter
  );
  allPassed &= check(
    'candidates.json unchanged',
    candidatesHashBefore === candidatesHashAfter
  );

  separator('6. INTERVIEW STATE STRUCTURE');

  console.log('  Top-level keys:');
  for (const key of Object.keys(state)) {
    const val = state[key];
    let desc;
    if (val === null) {
      desc = 'null';
    } else if (Array.isArray(val)) {
      desc = `Array(${val.length})`;
    } else if (typeof val === 'object') {
      desc = `Object(${Object.keys(val).length} keys)`;
    } else {
      desc = `${typeof val}: ${val}`;
    }
    console.log(`    ├─ ${key}: ${desc}`);
  }

  separator('RESULT');

  if (allPassed) {
    console.log('  ✅ ALL CHECKS PASSED');
    console.log('  The Interview Engine data foundation is working correctly.');
  } else {
    console.log('  ❌ SOME CHECKS FAILED');
    console.log('  Review the output above for details.');
  }

  console.log('');

  // ─── Output serialized state ────────────────────────────────────────────
  separator('SERIALIZED INTERVIEW STATE (full)');
  console.log(serialized);
}

// ─── Run ─────────────────────────────────────────────────────────────────────
validate();
