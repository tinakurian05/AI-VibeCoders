from typing import Dict, Any, List, Optional
from models.interview import (
    CandidateState,
    CurriculumState,
    CurriculumDay,
    CurriculumModule,
    InterviewPlan,
    InterviewTopicPlan,
)

MIN_QUESTIONS: int = 8
MIN_CURRICULUM_DAYS: int = 4


class InterviewPlanner:
    """
    Service responsible for deterministically generating an InterviewPlan from
    a candidate's CandidateState and the cohort's CurriculumState.
    """

    def plan_interview(
        self, candidate_state: CandidateState, curriculum_state: CurriculumState
    ) -> InterviewPlan:
        """
        Generate a structured, deterministic InterviewPlan for the candidate.
        
        Rules:
        - Only selects completed days from CandidateState.
        - Never selects skipped days or failed missions.
        - Prioritizes module diversity.
        - Uses attempts count as a probing signal (higher attempts = higher probing priority).
        - Enforces minimum 8 question slots and attempts at least 4 distinct curriculum days.
        """
        # 1. Identify eligible completed days present in CurriculumState
        eligible_day_numbers = [
            d for d in candidate_state.completed_days
            if d in curriculum_state.days and d not in candidate_state.skipped_days
        ]

        # 2. Build candidate topic records with priority scores
        day_records: List[Dict[str, Any]] = []
        for day_num in eligible_day_numbers:
            curr_day: CurriculumDay = curriculum_state.days[day_num]
            
            # Find associated module
            mod_id = 0
            mod_title = "General"
            for m_id, module in curriculum_state.modules.items():
                if any(d.day == day_num for d in module.days):
                    mod_id = m_id
                    mod_title = module.title
                    break

            attempts = candidate_state.attempts.get(day_num, 1)

            # Calculate deterministic priority score:
            # - Base score: 10.0
            # - Attempt bonus: +2.0 per extra attempt (probing signal for deeper exploration)
            # - Objectives bonus: +0.2 per objective
            # - Build/Capstone type bonus: +1.0 for hands-on missions
            attempt_bonus = (attempts - 1) * 2.0
            depth_bonus = len(curr_day.objectives) * 0.2
            type_bonus = 1.0 if curr_day.type in ["BUILD", "CAPSTONE"] else 0.5
            priority_score = round(10.0 + attempt_bonus + depth_bonus + type_bonus, 2)

            if attempts > 1:
                probing_reason = f"Deeper probing recommended due to {attempts} attempt(s) on mission."
            else:
                probing_reason = "Core topic assessment based on completed mission."

            day_records.append({
                "day": day_num,
                "title": curr_day.title,
                "module_id": mod_id,
                "module_title": mod_title,
                "priority_score": priority_score,
                "attempts": attempts,
                "probing_reason": probing_reason,
                "tools": curr_day.tools,
                "objectives": curr_day.objectives,
            })

        # 3. Module diversity selection strategy
        # Group records by module_id
        modules_map: Dict[int, List[Dict[str, Any]]] = {}
        for rec in day_records:
            mod_id = rec["module_id"]
            modules_map.setdefault(mod_id, []).append(rec)

        # Sort days within each module by priority_score descending
        for mod_id in modules_map:
            modules_map[mod_id].sort(key=lambda r: (-r["priority_score"], r["day"]))

        selected_records: List[Dict[str, Any]] = []

        # Round 1: Select top day from each module (sorted by module_id for determinism)
        sorted_module_ids = sorted(modules_map.keys())
        for mod_id in sorted_module_ids:
            selected_records.append(modules_map[mod_id][0])

        # Round 2: If we need more days to reach MIN_CURRICULUM_DAYS, pick remaining top days across modules
        if len(selected_records) < MIN_CURRICULUM_DAYS:
            selected_days_set = {r["day"] for r in selected_records}
            remaining_records = [
                r for r in day_records if r["day"] not in selected_days_set
            ]
            remaining_records.sort(key=lambda r: (-r["priority_score"], r["day"]))

            needed = MIN_CURRICULUM_DAYS - len(selected_records)
            selected_records.extend(remaining_records[:needed])

        # Determine if min 4 days constraint is satisfied
        min_days_met = len(selected_records) >= MIN_CURRICULUM_DAYS
        notes: Optional[str] = None
        if not min_days_met:
            notes = (
                f"Candidate has only {len(selected_records)} eligible completed curriculum day(s). "
                f"Minimum {MIN_CURRICULUM_DAYS}-day requirement cannot be fully satisfied from supplied data."
            )

        # Sort selected records deterministically by priority_score descending, then day ascending
        selected_records.sort(key=lambda r: (-r["priority_score"], r["day"]))

        # 4. Allocate question budget (Minimum 8 questions total)
        N = len(selected_records)
        if N > 0:
            base_q = max(1, MIN_QUESTIONS // N)
            counts = [base_q] * N
            total_allocated = base_q * N

            # Distribute remaining question slots to highest priority topics
            rem = max(0, MIN_QUESTIONS - total_allocated)
            for i in range(rem):
                counts[i % N] += 1
        else:
            counts = []

        # 5. Build InterviewTopicPlan and InterviewPlan objects
        topic_plans: List[InterviewTopicPlan] = []
        for rec, q_count in zip(selected_records, counts):
            topic_plan = InterviewTopicPlan(
                day=rec["day"],
                title=rec["title"],
                module_id=rec["module_id"],
                module_title=rec["module_title"],
                question_count=q_count,
                priority_score=rec["priority_score"],
                attempts=rec["attempts"],
                follow_up_allowed=True,
                probing_reason=rec["probing_reason"],
                tools=rec["tools"],
                objectives=rec["objectives"],
            )
            topic_plans.append(topic_plan)

        total_budget = sum(t.question_count for t in topic_plans)
        min_questions_met = total_budget >= MIN_QUESTIONS if N > 0 else False

        selected_day_numbers = [t.day for t in topic_plans]

        return InterviewPlan(
            candidate_id=candidate_state.candidate_id,
            candidate_name=candidate_state.name,
            job_role=candidate_state.job_role,
            selected_days=selected_day_numbers,
            total_question_budget=total_budget,
            topic_plans=topic_plans,
            min_questions_met=min_questions_met,
            min_days_met=min_days_met,
            notes=notes,
        )


# Global default instance
interview_planner = InterviewPlanner()
