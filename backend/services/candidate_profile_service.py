import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from models.interview import CandidateState, CandidateSignals


class CandidateProfileService:
    """
    Service responsible for loading candidates from backend/data/candidates.json,
    searching by candidate ID, and constructing normalized CandidateState objects.
    """

    def __init__(self, data_path: Optional[Path] = None) -> None:
        if data_path is None:
            # Default to backend/data/candidates.json relative to backend root
            base_dir = Path(__file__).resolve().parent.parent
            self.data_path = base_dir / "data" / "candidates.json"
        else:
            self.data_path = Path(data_path)

    def load_candidates(self) -> List[Dict[str, Any]]:
        """
        Load candidates.json and validate that the root structure contains a 'candidates' list.
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Candidate data file not found at: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict) or "candidates" not in data:
            raise ValueError("Invalid candidate data format: root must contain 'candidates' key.")

        candidates = data["candidates"]
        if not isinstance(candidates, list):
            raise ValueError("Invalid candidate data format: 'candidates' must be a list.")

        return candidates

    def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """
        Search for a candidate record by member.id.
        Raises ValueError if candidate_id is not found.
        """
        candidates = self.load_candidates()
        for candidate in candidates:
            member = candidate.get("member", {})
            if member.get("id") == candidate_id:
                return candidate

        raise ValueError(f"Candidate with ID '{candidate_id}' not found.")

    def build_candidate_state(self, candidate_input: Union[str, Dict[str, Any]]) -> CandidateState:
        """
        Build and return a CandidateState Pydantic model from either a candidate ID string
        or a candidate profile dictionary.
        """
        if isinstance(candidate_input, str):
            raw_candidate = self.get_candidate(candidate_input)
        elif isinstance(candidate_input, dict):
            # If a dict is provided, check if it contains a member.id that can be resolved
            # from candidates.json to retrieve full mission/signal metadata if incomplete.
            member_info = candidate_input.get("member", {})
            candidate_id = member_info.get("id")
            if candidate_id and "missions" not in candidate_input:
                try:
                    raw_candidate = self.get_candidate(candidate_id)
                except ValueError:
                    raw_candidate = candidate_input
            else:
                raw_candidate = candidate_input
        else:
            raise TypeError(f"Invalid candidate input type: {type(candidate_input)}")

        member = raw_candidate.get("member", {})
        missions = raw_candidate.get("missions", [])
        signals_data = raw_candidate.get("signals", {})

        # 1. Parse completed_days: missions with passed == True
        completed_days = [
            m["day"] for m in missions if m.get("passed") is True
        ]

        # 2. Parse skipped_days: missions with skipped == True
        skipped_days = [
            m["day"] for m in missions if m.get("skipped") is True
        ]

        # 3. Parse attempts: day -> attempts mapping
        attempts = {
            m["day"]: m["attempts"]
            for m in missions
            if "attempts" in m and m["attempts"] is not None
        }

        # 4. Parse mission_titles: day -> title mapping for all missions
        mission_titles = {
            m["day"]: m["title"]
            for m in missions
            if "day" in m and "title" in m
        }

        # 5. Parse signals
        signals = CandidateSignals(
            commitDays=signals_data.get("commitDays", 0),
            missionsCompleted=signals_data.get("missionsCompleted", 0),
            missionsFirstTry=signals_data.get("missionsFirstTry", 0)
        )

        return CandidateState(
            candidate_id=member.get("id", ""),
            name=member.get("name", ""),
            job_role=member.get("jobRole", ""),
            years_experience=member.get("yearsExperience", 0),
            education=member.get("education", ""),
            status=member.get("status", ""),
            completed_days=completed_days,
            skipped_days=skipped_days,
            attempts=attempts,
            mission_titles=mission_titles,
            signals=signals
        )


# Global default instance
candidate_profile_service = CandidateProfileService()
