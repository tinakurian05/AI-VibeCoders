/**
 * Curriculum Type Definitions
 *
 * Hierarchy: Module → Day → Objectives → Tools
 *
 * A "day" is a curriculum unit, NOT a single topic.
 * Each day contains multiple learning objectives and associated tools.
 * The Interview Engine reasons at the objective level for granularity,
 * while maintaining aggregate day-level and module-level views.
 */

/**
 * A single learning objective within a curriculum day.
 * This is the finest-grained curriculum unit.
 *
 * @typedef {Object} CurriculumObjective
 * @property {string} id - Synthesized ID: "day-{day}-obj-{index}" (0-based)
 * @property {number} dayNumber - The curriculum day this objective belongs to
 * @property {number} index - Position within the day's objectives list (0-based)
 * @property {string} text - The full objective text from the curriculum
 */

/**
 * A single curriculum day, enriched with its parent module information.
 *
 * @typedef {Object} CurriculumDay
 * @property {number} day - Day number (1–31)
 * @property {string} title - Day title from the source curriculum
 * @property {string} type - Day type: "SETUP"|"BUILD"|"AI_CORE"|"LEARN"|"SHIP_IT"|"OPTIMIZE"|"CAPSTONE"
 * @property {string[]} tools - Tool names associated with this day
 * @property {string[]} objectives - Raw objective strings from the source
 * @property {CurriculumObjective[]} objectiveDetails - Structured objective entries with IDs
 * @property {number} moduleNumber - Parent module number (derived)
 * @property {string} moduleTitle - Parent module title (derived)
 */

/**
 * A curriculum module containing a range of days.
 *
 * @typedef {Object} CurriculumModule
 * @property {number} n - Module number (1–8)
 * @property {string} title - Module title
 * @property {number} startDay - First day in this module (inclusive)
 * @property {number} endDay - Last day in this module (inclusive)
 * @property {number[]} dayNumbers - All day numbers belonging to this module
 */

/**
 * The normalized, read-only curriculum context.
 *
 * @typedef {Object} CurriculumContext
 * @property {string} cohort - Cohort description string
 * @property {CurriculumModule[]} modules - All 8 modules
 * @property {CurriculumDay[]} days - All 31 days, enriched with module info
 * @property {Object<string, number[]>} toolIndex - Map: tool name → day numbers where it appears
 * @property {Object<number, CurriculumDay[]>} daysByModule - Map: module number → days in that module
 * @property {Object<string, CurriculumObjective>} objectiveIndex - Map: objective ID → objective detail
 * @property {null} prerequisites - Explicitly null; the source data has no prerequisite relationships
 * @property {Object} _meta - Metadata about this context
 * @property {number} _meta.totalDays - Total number of curriculum days
 * @property {number} _meta.totalModules - Total number of modules
 * @property {number} _meta.totalObjectives - Total number of objectives across all days
 * @property {number} _meta.totalUniqueTools - Total number of unique tools
 */

module.exports = {};
