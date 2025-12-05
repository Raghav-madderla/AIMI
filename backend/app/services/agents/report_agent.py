"""
Report Generation Agent

Purpose: Generates comprehensive interview analysis and feedback report
"""

from typing import Dict, List
from app.services.local_llm_service import local_llm_service


async def generate_final_report(
    evaluation_history: List[Dict],
    user_answers: List[Dict],
    previous_questions: List[Dict],
    job_role: str,
    session_id: str
) -> Dict:
    """
    Generate comprehensive interview report with analytics
    
    Args:
        evaluation_history: List of all evaluations with scores
        user_answers: List of user answers
        previous_questions: List of questions asked
        job_role: Target job role
        session_id: Interview session ID
    
    Returns:
        Comprehensive report with scores, strengths, weaknesses, and recommendations
    """
    
    # Calculate overall statistics
    total_questions = len(evaluation_history)
    if total_questions == 0:
        return {
            "error": "No evaluations available",
            "message": "Interview was too short to generate a report"
        }
    
    scores = [eval.get("score", 0) for eval in evaluation_history]
    average_score = sum(scores) / len(scores) if scores else 0
    
    # Domain-wise performance
    domain_performance = {}
    for i, eval in enumerate(evaluation_history):
        domain = eval.get("domain", "Unknown")
        score = eval.get("score", 0)
        if domain not in domain_performance:
            domain_performance[domain] = []
        domain_performance[domain].append(score)
    
    domain_averages = {
        domain: sum(scores) / len(scores) 
        for domain, scores in domain_performance.items()
    }
    
    # Prepare conversation history for LLM analysis
    conversation_summary = []
    for i in range(min(len(previous_questions), len(user_answers), len(evaluation_history))):
        q = previous_questions[i]
        a = user_answers[i]
        e = evaluation_history[i]
        
        conversation_summary.append({
            "question": q.get("question_text", ""),
            "answer": a.get("answer", ""),
            "score": e.get("score", 0),
            "domain": e.get("domain", ""),
            "feedback": e.get("feedback", {})
        })
    
    # Create comprehensive prompt for final analysis
    prompt = f"""You are an expert hiring manager providing final interview feedback for a {job_role} position.

INTERVIEW STATISTICS:
- Total Questions: {total_questions}
- Overall Score: {average_score:.2f}/1.0 ({average_score*100:.1f}%)
- Domain Performance: {domain_averages}

CONVERSATION HISTORY:
{format_conversation_for_analysis(conversation_summary)}

Provide a comprehensive interview report with:

1. **Overall Performance Summary** (2-3 sentences about general impression)

2. **Strengths** (3-5 key strengths demonstrated)

3. **Areas for Improvement** (3-5 areas to work on)

4. **Domain-Specific Analysis** (Brief analysis for each technical domain covered)

5. **Recommendations** (3-4 specific, actionable recommendations for improvement)

6. **Hiring Decision Guidance** (Would you recommend this candidate? Why or why not?)

Format as JSON with keys: overall_summary, strengths (array), areas_for_improvement (array), domain_analysis (object), recommendations (array), hiring_decision (object with 'recommendation' and 'reasoning')
"""
    
    try:
        print(f"Generating report with Hugging Face API")
        messages = [
                {
                    "role": "system",
                    "content": "You are an expert hiring manager providing detailed, constructive interview feedback. Be honest but encouraging. Format response as valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
        ]
        
        analysis = await local_llm_service.generate_json_async(messages, max_new_tokens=2000, temperature=0.7)
        print(f"API response received")
        
        if not analysis:
            # Fallback if JSON parsing fails
            raise ValueError("Failed to parse JSON response")
        
        # Combine statistics with LLM analysis
        final_report = {
            "session_id": session_id,
            "job_role": job_role,
            "statistics": {
                "total_questions": total_questions,
                "overall_score": round(average_score, 2),
                "overall_percentage": round(average_score * 100, 1),
                "domain_scores": {
                    domain: round(avg, 2) 
                    for domain, avg in domain_averages.items()
                },
                "score_distribution": {
                    "excellent (>0.8)": len([s for s in scores if s > 0.8]),
                    "good (0.6-0.8)": len([s for s in scores if 0.6 <= s <= 0.8]),
                    "needs_improvement (<0.6)": len([s for s in scores if s < 0.6])
                }
            },
            "analysis": analysis,
            "detailed_feedback": conversation_summary  # Include per-question feedback
        }
        
        return final_report
        
    except Exception as e:
        print(f"Report generation failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Fallback: Return basic statistics with better analysis
        return {
            "session_id": session_id,
            "job_role": job_role,
            "statistics": {
                "total_questions": total_questions,
                "overall_score": round(average_score, 2),
                "overall_percentage": round(average_score * 100, 1),
                "domain_scores": domain_averages
            },
            "analysis": {
                "overall_summary": generate_basic_summary(average_score, total_questions, domain_averages),
                "strengths": generate_basic_strengths(domain_averages, scores),
                "areas_for_improvement": generate_basic_improvements(domain_averages, scores),
                "domain_analysis": {
                    domain: f"Score: {avg:.0%}" for domain, avg in domain_averages.items()
                },
                "recommendations": generate_basic_recommendations(average_score, domain_averages),
                "hiring_decision": {
                    "recommendation": "Review Required" if average_score < 0.6 else "Recommend" if average_score >= 0.8 else "Borderline",
                    "reasoning": f"Based on {average_score*100:.1f}% overall score across {total_questions} questions"
                }
            },
            "error": str(e)
        }


def generate_basic_summary(avg_score: float, total_q: int, domains: dict) -> str:
    """Generate basic summary when LLM fails"""
    if avg_score >= 0.8:
        performance = "excellent"
    elif avg_score >= 0.6:
        performance = "good"
    else:
        performance = "needs improvement"
    
    top_domain = max(domains.items(), key=lambda x: x[1])[0] if domains else "N/A"
    return f"Completed {total_q} questions with {performance} overall performance ({avg_score*100:.1f}%). Strongest in {top_domain}."


def generate_basic_strengths(domains: dict, scores: list) -> list:
    """Generate basic strengths when LLM fails"""
    strengths = []
    for domain, avg in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:3]:
        if avg >= 0.7:
            strengths.append(f"Strong performance in {domain} ({avg*100:.1f}%)")
    
    if not strengths:
        strengths = ["Completed all questions", "Showed engagement throughout"]
    
    return strengths


def generate_basic_improvements(domains: dict, scores: list) -> list:
    """Generate basic improvements when LLM fails"""
    improvements = []
    for domain, avg in sorted(domains.items(), key=lambda x: x[1])[:3]:
        if avg < 0.7:
            improvements.append(f"Develop deeper knowledge in {domain} (current: {avg*100:.1f}%)")
    
    if not improvements:
        improvements = ["Continue practicing", "Explore advanced topics"]
    
    return improvements


def generate_basic_recommendations(avg_score: float, domains: dict) -> list:
    """Generate basic recommendations when LLM fails"""
    recommendations = []
    
    # Lowest scoring domain
    if domains:
        lowest_domain = min(domains.items(), key=lambda x: x[1])[0]
        recommendations.append(f"Focus on improving {lowest_domain} skills")
    
    if avg_score < 0.6:
        recommendations.append("Review fundamental concepts")
        recommendations.append("Practice with more examples")
    elif avg_score < 0.8:
        recommendations.append("Work on depth of understanding")
        recommendations.append("Practice explaining concepts clearly")
    else:
        recommendations.append("Continue with advanced topics")
        recommendations.append("Focus on real-world applications")
    
    return recommendations


def format_conversation_for_analysis(conversation_summary: List[Dict]) -> str:
    """Format conversation history for LLM analysis"""
    formatted = []
    for i, item in enumerate(conversation_summary, 1):
        formatted.append(f"""
Question {i} ({item['domain']}):
Q: {item['question']}
A: {item['answer'][:300]}...
Score: {item['score']:.2f}
Feedback: {item['feedback'].get('feedback_text', 'N/A')}
---""")
    return "\n".join(formatted)
