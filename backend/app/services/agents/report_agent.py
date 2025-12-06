"""
Report Generation Agent

Generates comprehensive interview report with all metrics for visual dashboard:
1. Executive Summary
2. Metric Breakdown (Technical Accuracy, Completeness, Clarity)
3. Domain Performance
4. Difficulty Performance
5. Question-by-Question Details
6. LLM-Generated Insights
7. Score Progression
"""

from typing import Dict, List
from datetime import datetime
from app.services.local_llm_service import local_llm_service


async def generate_final_report(
    evaluation_history: List[Dict],
    user_answers: List[Dict],
    previous_questions: List[Dict],
    job_role: str,
    session_id: str
) -> Dict:
    """
    Generate comprehensive interview report with all 7 dashboard sections
    """
    
    total_questions = len(evaluation_history)
    if total_questions == 0:
        return {
            "error": "No evaluations available",
            "message": "Interview was too short to generate a report"
        }
    
    # ========================================
    # SECTION 1: EXECUTIVE SUMMARY
    # ========================================
    overall_scores = [eval.get("score", 0) for eval in evaluation_history]
    overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    
    performance_level = _get_performance_level(overall_score)
    
    executive_summary = {
        "overall_score": round(overall_score, 2),
        "overall_percentage": round(overall_score * 100, 1),
        "performance_level": performance_level["level"],
        "performance_color": performance_level["color"],
        "total_questions": total_questions,
        "timestamp": datetime.now().isoformat()
    }
    
    # ========================================
    # SECTION 2: METRIC BREAKDOWN (3 Core Pillars)
    # ========================================
    technical_accuracy_scores = []
    completeness_scores = []
    clarity_scores = []
    
    for eval in evaluation_history:
        feedback = eval.get("feedback", {})
        if isinstance(feedback, dict):
            technical_accuracy_scores.append(feedback.get("technical_accuracy", eval.get("score", 0.5)))
            completeness_scores.append(feedback.get("completeness", eval.get("score", 0.5)))
            clarity_scores.append(feedback.get("clarity", eval.get("score", 0.5)))
        else:
            # Fallback if feedback is not dict
            score = eval.get("score", 0.5)
            technical_accuracy_scores.append(score)
            completeness_scores.append(score)
            clarity_scores.append(score)
    
    metric_breakdown = {
        "technical_accuracy": {
            "score": round(sum(technical_accuracy_scores) / len(technical_accuracy_scores), 2) if technical_accuracy_scores else 0,
            "label": "Technical Accuracy",
            "description": "Factual correctness of answers"
        },
        "completeness": {
            "score": round(sum(completeness_scores) / len(completeness_scores), 2) if completeness_scores else 0,
            "label": "Completeness",
            "description": "Coverage of key points"
        },
        "clarity": {
            "score": round(sum(clarity_scores) / len(clarity_scores), 2) if clarity_scores else 0,
            "label": "Clarity",
            "description": "Clear communication"
        }
    }
    
    # ========================================
    # SECTION 3: DOMAIN PERFORMANCE
    # ========================================
    domain_scores = {}
    for i, eval in enumerate(evaluation_history):
        domain = eval.get("domain", "Unknown")
        if domain == "Introduction":
            continue  # Skip intro question
        score = eval.get("score", 0)
        if domain not in domain_scores:
            domain_scores[domain] = []
        domain_scores[domain].append(score)
    
    domain_performance = {
        domain: {
            "score": round(sum(scores) / len(scores), 2),
            "count": len(scores)
        }
        for domain, scores in domain_scores.items()
    }
    
    # Find strongest and weakest
    if domain_performance:
        sorted_domains = sorted(domain_performance.items(), key=lambda x: x[1]["score"], reverse=True)
        strongest_domain = sorted_domains[0][0] if sorted_domains else None
        weakest_domain = sorted_domains[-1][0] if len(sorted_domains) > 1 else None
    else:
        strongest_domain = None
        weakest_domain = None
    
    domain_analysis = {
        "scores": domain_performance,
        "strongest": strongest_domain,
        "weakest": weakest_domain,
        "domains_list": list(domain_performance.keys()),
        "scores_list": [d["score"] for d in domain_performance.values()]
    }
    
    # ========================================
    # SECTION 4: DIFFICULTY PERFORMANCE
    # ========================================
    difficulty_scores = {"easy": [], "medium": [], "hard": []}
    
    for i, eval in enumerate(evaluation_history):
        if i < len(previous_questions):
            difficulty = previous_questions[i].get("difficulty", "medium")
            score = eval.get("score", 0)
            if difficulty in difficulty_scores:
                difficulty_scores[difficulty].append(score)
    
    difficulty_performance = {
        difficulty: {
            "score": round(sum(scores) / len(scores), 2) if scores else 0,
            "count": len(scores)
        }
        for difficulty, scores in difficulty_scores.items()
    }
    
    # ========================================
    # SECTION 5: QUESTION-BY-QUESTION BREAKDOWN
    # ========================================
    questions_breakdown = []
    for i in range(min(len(previous_questions), len(user_answers), len(evaluation_history))):
        q = previous_questions[i]
        a = user_answers[i]
        e = evaluation_history[i]
        
        feedback = e.get("feedback", {})
        
        questions_breakdown.append({
            "index": i + 1,
            "question": q.get("question_text", ""),
            "answer": a.get("answer", "")[:500],  # Truncate long answers
            "domain": e.get("domain", q.get("domain", "Unknown")),
            "difficulty": q.get("difficulty", "medium"),
            "score": round(e.get("score", 0), 2),
            "feedback": feedback.get("feedback", feedback.get("feedback_text", "")) if isinstance(feedback, dict) else str(feedback),
            "technical_accuracy": feedback.get("technical_accuracy", e.get("score", 0.5)) if isinstance(feedback, dict) else e.get("score", 0.5),
            "completeness": feedback.get("completeness", e.get("score", 0.5)) if isinstance(feedback, dict) else e.get("score", 0.5),
            "clarity": feedback.get("clarity", e.get("score", 0.5)) if isinstance(feedback, dict) else e.get("score", 0.5)
        })
    
    # ========================================
    # SECTION 6: LLM-GENERATED INSIGHTS
    # ========================================
    insights = await _generate_llm_insights(
        overall_score=overall_score,
        domain_performance=domain_performance,
        difficulty_performance=difficulty_performance,
        metric_breakdown=metric_breakdown,
        questions_breakdown=questions_breakdown,
        job_role=job_role
    )
    
    # ========================================
    # SECTION 7: SCORE PROGRESSION
    # ========================================
    score_progression = []
    for i, eval in enumerate(evaluation_history):
        score_progression.append({
            "question_number": i + 1,
            "score": round(eval.get("score", 0), 2),
            "domain": eval.get("domain", "Unknown"),
            "difficulty": previous_questions[i].get("difficulty", "medium") if i < len(previous_questions) else "medium"
        })
    
    # Calculate trend
    if len(score_progression) >= 3:
        first_half = score_progression[:len(score_progression)//2]
        second_half = score_progression[len(score_progression)//2:]
        first_avg = sum(s["score"] for s in first_half) / len(first_half)
        second_avg = sum(s["score"] for s in second_half) / len(second_half)
        
        if second_avg > first_avg + 0.1:
            trend = "improving"
        elif second_avg < first_avg - 0.1:
            trend = "declining"
        else:
            trend = "consistent"
    else:
        trend = "too_few_questions"
    
    progression_analysis = {
        "scores": score_progression,
        "trend": trend,
        "highest_score": max(s["score"] for s in score_progression) if score_progression else 0,
        "lowest_score": min(s["score"] for s in score_progression) if score_progression else 0
    }
    
    # ========================================
    # COMPILE FINAL REPORT
    # ========================================
    final_report = {
        "session_id": session_id,
        "job_role": job_role,
        "generated_at": datetime.now().isoformat(),
        
        # Section 1: Executive Summary
        "executive_summary": executive_summary,
        
        # Section 2: Metric Breakdown
        "metric_breakdown": metric_breakdown,
        
        # Section 3: Domain Performance
        "domain_analysis": domain_analysis,
        
        # Section 4: Difficulty Performance
        "difficulty_performance": difficulty_performance,
        
        # Section 5: Question Breakdown
        "questions_breakdown": questions_breakdown,
        
        # Section 6: LLM Insights
        "insights": insights,
        
        # Section 7: Score Progression
        "score_progression": progression_analysis,
        
        # Legacy compatibility
        "statistics": {
            "total_questions": total_questions,
            "overall_score": round(overall_score, 2),
            "overall_percentage": round(overall_score * 100, 1),
            "domain_scores": {k: v["score"] for k, v in domain_performance.items()}
        },
        "analysis": insights  # Legacy field
    }
    
    return final_report


def _get_performance_level(score: float) -> Dict:
    """Get performance level with color"""
    if score >= 0.9:
        return {"level": "Outstanding", "color": "#10b981"}
    elif score >= 0.8:
        return {"level": "Excellent", "color": "#22c55e"}
    elif score >= 0.7:
        return {"level": "Strong", "color": "#84cc16"}
    elif score >= 0.6:
        return {"level": "Good", "color": "#eab308"}
    elif score >= 0.5:
        return {"level": "Developing", "color": "#f97316"}
    else:
        return {"level": "Needs Improvement", "color": "#ef4444"}


async def _generate_llm_insights(
    overall_score: float,
    domain_performance: Dict,
    difficulty_performance: Dict,
    metric_breakdown: Dict,
    questions_breakdown: List,
    job_role: str
) -> Dict:
    """Generate LLM-powered insights for the report"""
    
    # Prepare context for LLM
    context = f"""
Interview Performance Data for {job_role} position:

Overall Score: {overall_score*100:.1f}%

Domain Scores:
{chr(10).join([f'- {d}: {s["score"]*100:.0f}%' for d, s in domain_performance.items()])}

Difficulty Performance:
- Easy: {difficulty_performance.get("easy", {}).get("score", 0)*100:.0f}%
- Medium: {difficulty_performance.get("medium", {}).get("score", 0)*100:.0f}%
- Hard: {difficulty_performance.get("hard", {}).get("score", 0)*100:.0f}%

Metrics:
- Technical Accuracy: {metric_breakdown["technical_accuracy"]["score"]*100:.0f}%
- Completeness: {metric_breakdown["completeness"]["score"]*100:.0f}%
- Clarity: {metric_breakdown["clarity"]["score"]*100:.0f}%
"""

    prompt = f"""Based on this interview performance data, generate insights for the candidate.

{context}

Provide your response as JSON with these exact keys:
{{
    "overall_summary": "2-3 sentence summary of performance",
    "strengths": ["strength1", "strength2", "strength3"],
    "areas_for_improvement": ["area1", "area2", "area3"],
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
    "hiring_recommendation": {{
        "decision": "Strongly Recommend / Recommend / Consider / Not Recommended",
        "confidence": 0.0-1.0,
        "reasoning": "Brief reasoning"
    }}
}}

Be specific and actionable. Use the actual data provided."""

    try:
        messages = [
            {"role": "system", "content": "You are an expert technical interviewer providing actionable feedback. Output valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        result = await local_llm_service.generate_json_async(messages, max_new_tokens=1000, temperature=0.5)
        
        if result:
            return result
        
    except Exception as e:
        print(f"LLM insights generation failed: {e}")
        
    # Fallback insights based on data
    return _generate_fallback_insights(
        overall_score, domain_performance, difficulty_performance, metric_breakdown
    )


def _generate_fallback_insights(
    overall_score: float,
    domain_performance: Dict,
    difficulty_performance: Dict,
    metric_breakdown: Dict
) -> Dict:
    """Generate fallback insights when LLM fails"""
    
    # Find strongest/weakest domains
    sorted_domains = sorted(domain_performance.items(), key=lambda x: x[1]["score"], reverse=True)
    strongest = sorted_domains[0] if sorted_domains else ("N/A", {"score": 0})
    weakest = sorted_domains[-1] if len(sorted_domains) > 1 else ("N/A", {"score": 0})
    
    # Generate insights
    strengths = []
    improvements = []
    recommendations = []
    
    if strongest[1]["score"] >= 0.7:
        strengths.append(f"Strong performance in {strongest[0]} ({strongest[1]['score']*100:.0f}%)")
    
    if metric_breakdown["clarity"]["score"] >= 0.7:
        strengths.append("Clear and articulate communication")
    
    if metric_breakdown["technical_accuracy"]["score"] >= 0.7:
        strengths.append("Technically accurate responses")
    
    if not strengths:
        strengths = ["Completed all questions", "Showed effort throughout interview"]
    
    if weakest[1]["score"] < 0.6:
        improvements.append(f"Deepen knowledge in {weakest[0]}")
    
    if metric_breakdown["completeness"]["score"] < 0.6:
        improvements.append("Provide more comprehensive answers covering all key points")
    
    if difficulty_performance.get("hard", {}).get("score", 0) < 0.5:
        improvements.append("Practice with more challenging technical problems")
    
    if not improvements:
        improvements = ["Continue exploring advanced topics", "Gain more hands-on experience"]
    
    # Recommendations
    recommendations.append(f"Focus on improving {weakest[0]} skills with practical projects")
    recommendations.append("Practice explaining complex concepts with real-world examples")
    recommendations.append("Review technical fundamentals in weaker areas")
    
    # Hiring recommendation
    if overall_score >= 0.8:
        decision = "Strongly Recommend"
        confidence = 0.9
    elif overall_score >= 0.7:
        decision = "Recommend"
        confidence = 0.75
    elif overall_score >= 0.6:
        decision = "Consider"
        confidence = 0.6
    else:
        decision = "Not Recommended"
        confidence = 0.7
    
    return {
        "overall_summary": f"The candidate scored {overall_score*100:.0f}% overall, showing {_get_performance_level(overall_score)['level'].lower()} performance. Strongest in {strongest[0]}, with room to improve in {weakest[0]}.",
        "strengths": strengths[:3],
        "areas_for_improvement": improvements[:3],
        "recommendations": recommendations[:3],
        "hiring_recommendation": {
            "decision": decision,
            "confidence": confidence,
            "reasoning": f"Based on {overall_score*100:.0f}% overall score with notable strength in {strongest[0]}."
        }
    }
