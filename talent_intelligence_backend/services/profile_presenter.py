class ProfilePresenter:
    def build(self, profile):
        return {
            "username": profile.username,
            "repos_analyzed": profile.repos_analyzed,
            "total_stars": profile.total_stars,
            "avg_repo_quality": profile.avg_repo_quality,
            "avg_structure_score": profile.avg_structure_score,
            "repo_type_distribution": profile.repo_type_distribution,
            "repo_type_distribution_weighted": profile.repo_type_distribution_weighted,
            "weighted_repo_type_signal": profile.weighted_repo_type_signal,
            "repositories": profile.repositories,
            "weighted_skills": profile.weighted_skills,
            "adjusted_confidence_scores": profile.adjusted_confidence_scores,
            "skills": profile.adjusted_confidence_scores,
            "developer_level": profile.developer_level,
            "developer_level_explanation": profile.developer_level_explanation,
            "uncertainty_indicator": profile.uncertainty_indicator,
        }

    def build_compact(self, profile):
        sorted_skills = sorted(
            profile.adjusted_confidence_scores.items(),
            key=lambda item: item[1].get("confidence", 0),
            reverse=True,
        )
        return {
            "username": profile.username,
            "developer_level": profile.developer_level,
            "skills_count": len(profile.adjusted_confidence_scores),
            "top_skills": [
                {
                    "skill": skill,
                    "confidence": details.get("confidence", 0),
                    "evidence": details.get("evidence", []),
                }
                for skill, details in sorted_skills[:5]
            ],
            "repo_type_distribution": profile.repo_type_distribution,
            "uncertainty_indicator": profile.uncertainty_indicator,
        }
