/**
 * Curriculum Context Layer
 *
 * Loads the existing curriculum.json and produces a normalized, read-only
 * representation for the Interview Engine.
 *
 * Hierarchy: Module → Day → Objectives → Tools
 *
 * IMPORTANT:
 * - Does NOT modify the source curriculum.json file
 * - Does NOT invent prerequisite relationships (none exist in the source)
 * - All enrichment is derived from the source data only
 */

const fs = require('fs');
const path = require('path');

/**
 * Loads and normalizes the curriculum JSON into a CurriculumContext.
 *
 * @param {string} filePath - Absolute or relative path to curriculum.json
 * @returns {Readonly<import('../types/curriculum.types.js').CurriculumContext>}
 */
function loadCurriculumContext(filePath) {
  const absolutePath = path.resolve(filePath);
  const raw = fs.readFileSync(absolutePath, 'utf-8');
  const source = JSON.parse(raw);

  // --- Normalize modules ---
  const modules = source.modules.map((mod) => ({
    n: mod.n,
    title: mod.title,
    startDay: mod.days[0],
    endDay: mod.days[1],
    dayNumbers: [],  // populated below
  }));

  // --- Build module lookup by day number ---
  function findModuleForDay(dayNumber) {
    return modules.find(
      (mod) => dayNumber >= mod.startDay && dayNumber <= mod.endDay
    );
  }

  // --- Normalize days with objective details and module enrichment ---
  const objectiveIndex = {};
  let totalObjectives = 0;

  const days = source.days.map((dayEntry) => {
    const parentModule = findModuleForDay(dayEntry.day);

    // Build structured objective entries
    const objectiveDetails = (dayEntry.objectives || []).map((text, idx) => {
      const id = `day-${dayEntry.day}-obj-${idx}`;
      const detail = {
        id,
        dayNumber: dayEntry.day,
        index: idx,
        text,
      };
      objectiveIndex[id] = detail;
      totalObjectives++;
      return detail;
    });

    // Register day in its module
    if (parentModule) {
      parentModule.dayNumbers.push(dayEntry.day);
    }

    return {
      day: dayEntry.day,
      title: dayEntry.title,
      type: dayEntry.type,
      tools: [...(dayEntry.tools || [])],
      objectives: [...(dayEntry.objectives || [])],
      objectiveDetails,
      moduleNumber: parentModule ? parentModule.n : null,
      moduleTitle: parentModule ? parentModule.title : null,
    };
  });

  // --- Build tool index: tool name → day numbers ---
  const toolIndex = {};
  for (const day of days) {
    for (const tool of day.tools) {
      if (!toolIndex[tool]) {
        toolIndex[tool] = [];
      }
      toolIndex[tool].push(day.day);
    }
  }

  // --- Build daysByModule: module number → day objects ---
  const daysByModule = {};
  for (const mod of modules) {
    daysByModule[mod.n] = days.filter(
      (d) => d.day >= mod.startDay && d.day <= mod.endDay
    );
  }

  // --- Assemble the context ---
  const context = {
    cohort: source.cohort,
    modules: Object.freeze(modules.map((m) => Object.freeze(m))),
    days: Object.freeze(days.map((d) => Object.freeze(d))),
    toolIndex: Object.freeze(toolIndex),
    daysByModule: Object.freeze(daysByModule),
    objectiveIndex: Object.freeze(objectiveIndex),

    // Explicitly null — no prerequisite relationships in the source data
    prerequisites: null,

    _meta: Object.freeze({
      totalDays: days.length,
      totalModules: modules.length,
      totalObjectives,
      totalUniqueTools: Object.keys(toolIndex).length,
      sourcePath: absolutePath,
    }),
  };

  return Object.freeze(context);
}

module.exports = { loadCurriculumContext };
