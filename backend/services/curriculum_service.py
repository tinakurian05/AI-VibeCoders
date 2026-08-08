import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from models.interview import (
    CurriculumDay,
    CurriculumModule,
    CurriculumState,
    CurriculumContext,
    CurriculumContextDay,
    InterviewPlan,
)


class CurriculumService:
    """
    Service responsible for loading curriculum.json and providing deterministic lookup
    for curriculum days, modules, tools, and learning objectives, as well as deriving
    lightweight CurriculumContext objects for interview execution.
    """

    def __init__(self, data_path: Optional[Path] = None) -> None:
        if data_path is None:
            # Default to backend/data/curriculum.json relative to backend root
            base_dir = Path(__file__).resolve().parent.parent
            self.data_path = base_dir / "data" / "curriculum.json"
        else:
            self.data_path = Path(data_path)

        self._state: Optional[CurriculumState] = None

    def load_curriculum(self) -> CurriculumState:
        """
        Load and parse backend/data/curriculum.json into a structured CurriculumState.
        Validates the presence of expected root keys ('cohort', 'modules', 'days').
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Curriculum data file not found at: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Invalid curriculum data format: root must be a JSON object.")

        for required_key in ["cohort", "modules", "days"]:
            if required_key not in data:
                raise ValueError(f"Invalid curriculum data format: missing required key '{required_key}'.")

        # 1. Parse CurriculumDays
        days_map: Dict[int, CurriculumDay] = {}
        for d_item in data["days"]:
            day_obj = CurriculumDay(
                day=d_item["day"],
                title=d_item["title"],
                type=d_item["type"],
                tools=d_item.get("tools", []),
                objectives=d_item.get("objectives", []),
            )
            days_map[day_obj.day] = day_obj

        # 2. Parse CurriculumModules
        modules_map: Dict[int, CurriculumModule] = {}
        for m_item in data["modules"]:
            module_id = m_item["n"]
            title = m_item["title"]
            day_range = m_item.get("days", [])

            # Resolve CurriculumDay objects contained within this module
            assoc_days: List[CurriculumDay] = []
            if len(day_range) == 2:
                start_day, end_day = day_range[0], day_range[1]
                for day_num in range(start_day, end_day + 1):
                    if day_num in days_map:
                        assoc_days.append(days_map[day_num])
            else:
                for day_num in day_range:
                    if day_num in days_map:
                        assoc_days.append(days_map[day_num])

            module_obj = CurriculumModule(
                module_id=module_id,
                title=title,
                day_range=day_range,
                days=assoc_days,
            )
            modules_map[module_id] = module_obj

        self._state = CurriculumState(
            cohort=data["cohort"],
            modules=modules_map,
            days=days_map,
        )
        return self._state

    def get_state(self) -> CurriculumState:
        """
        Return the cached CurriculumState, or load it if not yet loaded.
        """
        if self._state is None:
            return self.load_curriculum()
        return self._state

    def get_day(self, day: int) -> CurriculumDay:
        """
        Retrieve a single CurriculumDay by day number.
        Raises ValueError if the requested day does not exist.
        """
        state = self.get_state()
        if day not in state.days:
            raise ValueError(f"Curriculum day '{day}' not found.")
        return state.days[day]

    def get_days(self, days: List[int]) -> List[CurriculumDay]:
        """
        Retrieve a list of CurriculumDay objects for the provided list of day numbers.
        Raises ValueError if any requested day does not exist.
        """
        result: List[CurriculumDay] = []
        for d in days:
            result.append(self.get_day(d))
        return result

    def get_module(self, module_id: int) -> CurriculumModule:
        """
        Retrieve a CurriculumModule by module ID (n).
        Raises ValueError if the requested module ID does not exist.
        """
        state = self.get_state()
        if module_id not in state.modules:
            raise ValueError(f"Curriculum module '{module_id}' not found.")
        return state.modules[module_id]

    def build_context(self, interview_plan: Optional[InterviewPlan] = None) -> CurriculumContext:
        """
        Derive a focused CurriculumContext tailored to an InterviewPlan (or full cohort).
        """
        state = self.get_state()
        module_titles = {m_id: m.title for m_id, m in state.modules.items()}

        target_days: List[CurriculumContextDay] = []
        if interview_plan and interview_plan.selected_days:
            selected_set = set(interview_plan.selected_days)
            for day_num in sorted(selected_set):
                if day_num in state.days:
                    cd = state.days[day_num]
                    target_days.append(
                        CurriculumContextDay(
                            day=cd.day,
                            title=cd.title,
                            type=cd.type,
                            tools=cd.tools,
                            objectives=cd.objectives,
                        )
                    )
        else:
            for day_num in sorted(state.days.keys()):
                cd = state.days[day_num]
                target_days.append(
                    CurriculumContextDay(
                        day=cd.day,
                        title=cd.title,
                        type=cd.type,
                        tools=cd.tools,
                        objectives=cd.objectives,
                    )
                )

        return CurriculumContext(
            cohort=state.cohort,
            target_days=target_days,
            module_titles=module_titles,
        )


# Global default service instance
curriculum_service = CurriculumService()
