from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from . import models

def calculate_flakiness_score(passed_count: int, failed_count: int) -> float:
    """
    Calculates the flakiness score of a test based on passed and failed execution counts.
    
    Formula: 2 * min(passed, failed) / (passed + failed)
    - Returns 0.0 if either passed or failed count is 0 (consistently passing or failing).
    - Returns 1.0 if passed == failed (maximum state flipping/flakiness).
    """
    total = passed_count + failed_count
    if total == 0 or passed_count == 0 or failed_count == 0:
        return 0.0
    return round((2.0 * min(passed_count, failed_count)) / total, 4)

def get_flaky_tests(
    db: Session,
    repository_id: Optional[int] = None,
    min_runs: int = 2,
    threshold: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Aggregates test history from DB, calculates flakiness scores, and returns sorted test metrics.
    """
    query = db.query(
        models.TestHistory.repository_id,
        models.TestHistory.test_suite,
        models.TestHistory.test_name,
        func.count(models.TestHistory.id).label("total_runs"),
        func.sum(
            case(
                (models.TestHistory.status.in_(["passed", "success"]), 1),
                else_=0
            )
        ).label("passed_count"),
        func.sum(
            case(
                (models.TestHistory.status.in_(["failed", "failure"]), 1),
                else_=0
            )
        ).label("failed_count")
    )
    
    if repository_id is not None:
        query = query.filter(models.TestHistory.repository_id == repository_id)
        
    results = query.group_by(
        models.TestHistory.repository_id,
        models.TestHistory.test_suite,
        models.TestHistory.test_name
    ).all()
    
    flaky_list = []
    for r in results:
        repo_id, suite, name, total_runs, passed, failed = r
        passed = passed or 0
        failed = failed or 0
        
        if total_runs < min_runs:
            continue
            
        score = calculate_flakiness_score(passed, failed)
        failure_rate = round(failed / total_runs, 4) if total_runs > 0 else 0.0
        
        flaky_list.append({
            "repository_id": repo_id,
            "test_suite": suite,
            "test_name": name,
            "total_runs": total_runs,
            "passed_count": passed,
            "failed_count": failed,
            "failure_rate": failure_rate,
            "flakiness_score": score,
            "is_flaky": score >= threshold
        })
        
    flaky_list.sort(key=lambda x: (x["flakiness_score"], x["failure_rate"]), reverse=True)
    return flaky_list
