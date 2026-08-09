from models.strategy import (
    StrategyEngineInput, StrategyDecision, StrategyAction, DifficultyLevel
)

class StrategyEngine:
    def decide(self, input_data: StrategyEngineInput) -> StrategyDecision:
        state = input_data.interview_state
        plan = input_data.interview_plan
        analysis = input_data.latest_analysis
        knowledge = input_data.knowledge_model
        
        covered = set(state.covered_days)
        q_count = state.question_count
        
        # Evaluate end conditions
        budget_reached = q_count >= plan.total_question_budget
        min_constraints_met = q_count >= 8 and len(covered) >= 4
        
        # Identify available topics
        planned_days = [t.day for t in plan.topic_plans]
        remaining_days = [d for d in planned_days if d not in covered and d != state.current_topic_day]
        
        # 1. Budget and Requirements Check
        if budget_reached and min_constraints_met:
            return StrategyDecision(
                action=StrategyAction.END,
                target_day=analysis.curriculum_day,
                target_objective=None,
                difficulty=DifficultyLevel.MEDIUM,
                intent="end_interview",
                reasoning="Question budget reached and minimum requirements met.",
                follow_up=False,
                should_end=True
            )
            
        day = analysis.curriculum_day
        understanding = analysis.understanding_assessment
        assessment_type = analysis.assessment_type
        confidence = analysis.confidence
        gaps = analysis.gaps
        
        # 2. Identify unmet objectives for target_objective selection
        unmet_objectives = []
        if day in knowledge.topics:
            topic_k = knowledge.topics[day]
            for obj_id, obj_k in topic_k.objectives.items():
                if obj_k.understanding_level != "HIGH":
                    unmet_objectives.append(obj_id)
        else:
            # Fallback to plan if not tracked in knowledge yet
            for tp in plan.topic_plans:
                if tp.day == day:
                    if tp.objectives:
                        unmet_objectives = tp.objectives
                    break

        target_obj = unmet_objectives[0] if unmet_objectives else None

        # 3. Rule Evaluation (Deterministic)
        
        # Rule A: Ambiguous answer
        if assessment_type == "ambiguous" or understanding == "UNKNOWN" or confidence < 0.5:
            return StrategyDecision(
                action=StrategyAction.CLARIFY,
                target_day=day,
                target_objective=target_obj,
                difficulty=DifficultyLevel.EASY,
                intent="clarify_ambiguous_answer",
                reasoning="Candidate's answer was ambiguous or confidence is too low to assess.",
                follow_up=True,
                should_end=False
            )
            
        # Rule B: Misconception
        has_misconception = False
        if assessment_type == "indicates_misconception":
            has_misconception = True
        for gap in gaps:
            if "misconception" in gap.lower():
                has_misconception = True
                break
                
        if has_misconception:
            return StrategyDecision(
                action=StrategyAction.FOLLOW_UP,
                target_day=day,
                target_objective=target_obj,
                difficulty=DifficultyLevel.MEDIUM,
                intent="address_misconception",
                reasoning="Candidate demonstrated a misconception that requires targeted probing.",
                follow_up=True,
                should_end=False
            )
            
        # Rule E: Weak answer
        if understanding == "LOW":
            return StrategyDecision(
                action=StrategyAction.FOLLOW_UP,
                target_day=day,
                target_objective=target_obj,
                difficulty=DifficultyLevel.EASY,
                intent="probe_fundamental_gap",
                reasoning="Candidate showed weak understanding, scaling down difficulty to probe fundamentals.",
                follow_up=True,
                should_end=False
            )
            
        # Rule C: Partial understanding, or HIGH understanding where analyzer explicitly recommends follow-up
        if understanding == "MEDIUM" or (understanding != "HIGH" and gaps and analysis.follow_up_recommended) or (understanding == "HIGH" and analysis.follow_up_recommended):
            return StrategyDecision(
                action=StrategyAction.FOLLOW_UP,
                target_day=day,
                target_objective=target_obj,
                difficulty=DifficultyLevel.MEDIUM,
                intent="address_specific_gap",
                reasoning="Candidate showed partial understanding with specific gaps identified.",
                follow_up=True,
                should_end=False
            )
            
        # Rule D: Strong answer — HIGH understanding with no explicit follow-up recommendation.
        # Uses follow_up_recommended (not mere gap presence) as the authoritative advancement signal.
        # This fires for HIGH + no gaps, and for HIGH + minor gaps when follow_up_recommended=False.
        if understanding == "HIGH" and not analysis.follow_up_recommended:
            if unmet_objectives:
                return StrategyDecision(
                    action=StrategyAction.DEEPEN,
                    target_day=day,
                    target_objective=target_obj,
                    difficulty=DifficultyLevel.HARD,
                    intent="probe_unexplored_objective",
                    reasoning="Candidate showed strong understanding of current point, deepening into remaining objectives.",
                    follow_up=True,
                    should_end=False
                )
            else:
                if remaining_days:
                    return StrategyDecision(
                        action=StrategyAction.MOVE_TOPIC,
                        target_day=remaining_days[0],
                        target_objective=None,
                        difficulty=DifficultyLevel.MEDIUM,
                        intent="probe_new_topic",
                        reasoning="Current topic fully assessed, moving to next planned topic.",
                        follow_up=False,
                        should_end=False
                    )
                else:
                    if min_constraints_met:
                        return StrategyDecision(
                            action=StrategyAction.END,
                            target_day=day,
                            target_objective=None,
                            difficulty=DifficultyLevel.MEDIUM,
                            intent="end_interview",
                            reasoning="All topics exhausted and constraints met.",
                            follow_up=False,
                            should_end=True
                        )
                    else:
                        # Genuine exhaustion but constraints not met.
                        # Rule H: do not end unless genuinely impossible. No more planned days → impossible.
                        return StrategyDecision(
                            action=StrategyAction.END,
                            target_day=day,
                            target_objective=None,
                            difficulty=DifficultyLevel.MEDIUM,
                            intent="end_interview_forced",
                            reasoning="All planned topics exhausted, cannot meet 4 day requirement.",
                            follow_up=False,
                            should_end=True
                        )
                        
        # Default Fallback
        return StrategyDecision(
            action=StrategyAction.FOLLOW_UP,
            target_day=day,
            target_objective=target_obj,
            difficulty=DifficultyLevel.MEDIUM,
            intent="general_follow_up",
            reasoning="Default fallback strategy.",
            follow_up=True,
            should_end=False
        )
