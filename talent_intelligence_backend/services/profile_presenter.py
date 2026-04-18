class ProfilePresenter:
    def _risk_flags(self, profile):
        flags = []
        quality_score = round(profile.avg_repo_quality * 100)
        structure_score = round(profile.avg_structure_score * 100)
        uncertainty = profile.uncertainty_indicator or {}

        if quality_score < 40:
            flags.append("low_repo_quality")
        if structure_score < 40:
            flags.append("low_repo_structure")
        if uncertainty.get("is_uncertain"):
            flags.append("high_uncertainty")
        if profile.developer_level == "unknown":
            flags.append("unclear_developer_signal")

        return flags

    def _verified_skills(self, profile):
        verified = {}
        for skill, details in profile.adjusted_confidence_scores.items():
            score = round(details.get("confidence", 0) * 100)
            verified[skill] = {
                "score": score,
                "repos": details.get("repo_count", 0),
                "evidence": details.get("evidence", [])[:5],
            }
        return verified

    def _project_distribution(self, profile):
        distribution = profile.repo_type_distribution
        personal = (
            distribution.get("personal_project", 0)
            + distribution.get("library_or_framework", 0)
            + distribution.get("unknown", 0)
        )
        tutorial = distribution.get("tutorial_or_clone", 0) + distribution.get(
            "educational_content", 0
        )
        other = distribution.get("organization_repo", 0)
        return {"personal": personal, "tutorial": tutorial, "other": other}

    def build(self, profile):
        confidence_multiplier = (profile.uncertainty_indicator or {}).get(
            "confidence_multiplier", 1.0
        )
        return {
            "username": profile.username,
            "verified_skills": self._verified_skills(profile),
            "developer_profile": {
                "level": profile.developer_level,
                "score": round(profile.total_score),
                "confidence": round(confidence_multiplier * 100),
            },
            "repo_summary": {
                "total_repos": profile.repos_analyzed,
                "avg_quality": round(profile.avg_repo_quality * 100),
                "avg_structure": round(profile.avg_structure_score * 100),
                "project_distribution": self._project_distribution(profile),
            },
            "risk_flags": self._risk_flags(profile),
        }

    def build_compact(self, profile):
        full = self.build(profile)
        sorted_skills = sorted(
            full["verified_skills"].items(),
            key=lambda item: item[1].get("score", 0),
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
                    "score": details.get("score", 0),
                    "repos": details.get("repos", 0),
                    "evidence": details.get("evidence", []),
                }
                for skill, details in sorted_skills[:5]
            ],
            "repo_summary": full["repo_summary"],
            "risk_flags": full["risk_flags"],
        }
