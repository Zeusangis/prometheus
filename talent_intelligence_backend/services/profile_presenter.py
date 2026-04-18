from services.profile_aggregator import DeveloperProfile


class ProfilePresenter:
    def build(self, profile: DeveloperProfile) -> dict:
        return {
            "username": profile.username,
            "developer_profile": {
                "level": profile.level,
                "score": self._as_int(profile.score),
                "confidence": self._as_int(profile.confidence),
            },
            "verified_skills": {
                skill: {
                    "score": self._as_int(details.get("score", 0)),
                    "repos": max(0, int(details.get("repos", 0))),
                    "confidence": self._as_int(details.get("confidence", 0)),
                    "evidence": list(details.get("evidence", [])),
                }
                for skill, details in profile.verified_skills.items()
            },
            "repo_summary": {
                "total_repos": max(0, int(profile.repos_analyzed)),
                "total_stars": max(0, int(profile.total_stars)),
            },
            "risk_flags": list(profile.risk_flags),
        }

    def build_compact(self, profile: DeveloperProfile) -> dict:
        full = self.build(profile)
        sorted_skills = sorted(
            full["verified_skills"].items(),
            key=lambda item: item[1]["score"],
            reverse=True,
        )
        return {
            "username": full["username"],
            "developer_level": full["developer_profile"]["level"],
            "total_score": full["developer_profile"]["score"],
            "confidence": full["developer_profile"]["confidence"],
            "skills_count": len(full["verified_skills"]),
            "top_skills": [
                {
                    "skill": skill,
                    "score": details["score"],
                    "repos": details["repos"],
                    "evidence": details["evidence"],
                }
                for skill, details in sorted_skills[:5]
            ],
            "repo_summary": full["repo_summary"],
            "risk_flags": full["risk_flags"],
        }

    def _as_int(self, value) -> int:
        if value != value:
            return 0
        return max(0, min(100, int(round(float(value)))))
