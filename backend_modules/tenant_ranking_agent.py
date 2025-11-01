"""
AI Agent for intelligent tenant applicant ranking using Gemini AI
Fetches applications from database and uses Gemini to rank, sort, and select best applicants
"""

import os
import httpx
import json
import re
from typing import List, Dict, Any, Optional
from backend_modules.llm_service import call_gemini, TEXT_MODEL


async def _fetch_applications_from_db(
    user_id: str,
    property_id: Optional[str] = None,
    application_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Fetch applications from database via frontend API"""
    frontend_url = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    service_token = os.getenv("APPLICATION_SERVICE_TOKEN", "").strip()
    
    if not service_token:
        print(f"⚠️ APPLICATION_SERVICE_TOKEN is not set - cannot fetch applications from database")
        return []
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            api_url = f"{frontend_url}/api/applications/internal"
            headers = {
                "Authorization": f"Bearer {service_token}",
                "Content-Type": "application/json"
            }
            
            params = {"userId": user_id}
            if property_id:
                params["propertyId"] = property_id
            
            response = await client.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            all_applications = result.get("applications", [])
            
            # Filter by application IDs if provided
            if application_ids and len(application_ids) > 0:
                all_applications = [app for app in all_applications if app.get("id") in application_ids]
            
            return all_applications
    except Exception as e:
        print(f"⚠️ Error fetching applications from database: {e}")
        return []


async def find_best_applicants_for_property(
    user_id: str,
    property_id: Optional[str] = None,
    property_monthly_rent: Optional[float] = None,
    limit: int = 1,
    min_credit_score: int = 680
) -> List[Dict[str, Any]]:
    """
    Find and rank the best applicants for a property using Gemini AI
    
    Args:
        user_id: Property manager's user ID
        property_id: Optional property ID to filter by
        property_monthly_rent: Optional rent amount for income ratio calculation
        limit: Maximum number of results
        min_credit_score: Minimum credit score threshold
    
    Returns:
        List of ranked applicants with metadata
    """
    # Fetch applications from database
    db_applications = await _fetch_applications_from_db(user_id, property_id)
    
    if not db_applications:
        return []
    
    # Prepare data for Gemini
    applicants_data = []
    for app in db_applications:
        monthly_income = app.get("monthlyIncome")
        income_ratio = None
        if property_monthly_rent and monthly_income:
            income_ratio = monthly_income / property_monthly_rent
        
        # Filter by min credit score if provided
        credit_score = app.get("creditScore")
        if min_credit_score and (not credit_score or credit_score < min_credit_score):
            continue
        
        applicants_data.append({
            "application_id": app.get("id"),
            "applicant_name": app.get("applicantName", "Unknown"),
            "applicant_email": app.get("applicantEmail", ""),
            "credit_score": credit_score,
            "monthly_income": monthly_income,
            "annual_income": app.get("annualIncome"),
            "income_ratio": income_ratio,
            "screening_score": app.get("screeningScore"),
            "status": app.get("status", "pending"),
            "employer_name": app.get("employerName"),
            "property_id": app.get("propertyId")
        })
    
    if not applicants_data:
        return []
    
    # Format for Gemini
    applicants_text_parts = []
    for idx, app in enumerate(applicants_data):
        monthly_income_str = f"${app.get('monthly_income', 0):,.2f}" if app.get('monthly_income') else "N/A"
        income_ratio_str = f"{app.get('income_ratio', 0):.2f}x" if app.get('income_ratio') else "N/A"
        
        applicant_text = f"""Applicant {idx + 1} (ID: {app.get('application_id', 'N/A')}):
Name: {app.get('applicant_name', 'N/A')}
Credit Score: {app.get('credit_score', 'N/A')}
Monthly Income: {monthly_income_str}
Income to Rent Ratio: {income_ratio_str}
Screening Score: {app.get('screening_score', 'N/A')}
Status: {app.get('status', 'N/A')}
Employer: {app.get('employer_name', 'N/A')}"""
        applicants_text_parts.append(applicant_text)
    
    applicants_text = "\n\n".join(applicants_text_parts)
    rent_info = f"Property rent: ${property_monthly_rent:,.2f}/month" if property_monthly_rent else "Property rent: Not specified"
    
    # Query Gemini for ranking
    prompt = f"""Rank these tenant applicants and return the top {limit} based on:
1. Credit score (higher is better, above 680 is ideal)
2. Income to rent ratio (3x or higher is ideal)
3. Screening score (green > yellow > red)

{applicants_text}

{rent_info}

Return JSON in this format:
{{
    "rankedApplicants": [
        {{"applicationId": "id", "rank": 1, "reason": "why ranked #1"}},
        {{"applicationId": "id", "rank": 2, "reason": "why ranked #2"}}
    ]
}}

Return ONLY valid JSON."""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = await call_gemini(messages, TEXT_MODEL)
        content = response.get("content", "")
        
        # Parse JSON
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            ranked = result.get("rankedApplicants", [])
            
            # Map ranked results back to full applicant data
            ranked_applications = []
            for rank_info in ranked[:limit]:
                app_id = rank_info.get("applicationId")
                app_data = next((app for app in applicants_data if app.get("application_id") == app_id), None)
                if app_data:
                    app_data["rank"] = rank_info.get("rank", len(ranked_applications) + 1)
                    app_data["rank_reason"] = rank_info.get("reason", "")
                    ranked_applications.append(app_data)
            
            return ranked_applications
    except Exception as e:
        print(f"⚠️ Error ranking applicants with Gemini: {e}")
    
    # Fallback: sort by credit score and income ratio
    sorted_apps = sorted(
        applicants_data,
        key=lambda x: (
            x.get("credit_score") or 0,
            x.get("income_ratio") or 0
        ),
        reverse=True
    )
    
    return sorted_apps[:limit]


async def rank_applicants_by_criteria(
    user_id: str,
    criteria: Dict[str, Any],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Rank applicants based on custom criteria using Gemini AI
    
    Args:
        user_id: Property manager's user ID
        criteria: Dict with criteria like:
            - min_credit_score: int
            - min_income_ratio: float
            - screening_score: str ("green", "yellow", or None)
            - property_id: str or None
            - status: str or None
        limit: Maximum results
    
    Returns:
        Ranked list of applicants
    """
    # Fetch applications from database
    db_applications = await _fetch_applications_from_db(user_id, criteria.get("property_id"))
    
    if not db_applications:
        return []
    
    # Filter by criteria
    applicants_data = []
    for app in db_applications:
        # Filter by credit score
        if criteria.get("min_credit_score"):
            if not app.get("creditScore") or app.get("creditScore") < criteria["min_credit_score"]:
                continue
        
        # Filter by screening score
        if criteria.get("screening_score"):
            if app.get("screeningScore") != criteria["screening_score"]:
                continue
        
        # Filter by status
        if criteria.get("status"):
            if app.get("status") != criteria["status"]:
                continue
        
        applicants_data.append({
            "application_id": app.get("id"),
            "applicant_name": app.get("applicantName"),
            "credit_score": app.get("creditScore"),
            "monthly_income": app.get("monthlyIncome"),
            "screening_score": app.get("screeningScore"),
            "status": app.get("status"),
            **{k: app.get(k) for k in ["applicantEmail", "employerName", "propertyId"] if app.get(k)}
        })
    
    if not applicants_data:
        return []
    
    # Use Gemini to rank
    return await find_best_applicants_for_property(
        user_id=user_id,
        property_id=criteria.get("property_id"),
        limit=limit,
        min_credit_score=criteria.get("min_credit_score", 0)
    )


async def get_applicant_summary(
    user_id: str,
    question: str,
    property_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get AI-generated summary/answer about applicants using Gemini
    
    Example questions:
    - "What's the average credit score of approved applicants?"
    - "Which properties have the most pending applications?"
    - "Who are the top 3 applicants overall?"
    
    Returns:
        Dict with AI answer and source documents
    """
    # Fetch applications from database
    db_applications = await _fetch_applications_from_db(user_id, property_id)
    
    if not db_applications:
        return {
            "answer": "No applicants found",
            "sources": [],
            "count": 0
        }
    
    # Format applications for Gemini
    apps_summary = []
    for app in db_applications[:20]:  # Limit to 20 for prompt size
        apps_summary.append(
            f"Name: {app.get('applicantName')}, "
            f"Credit: {app.get('creditScore', 'N/A')}, "
            f"Income: ${app.get('monthlyIncome', 0):,.2f}, "
            f"Status: {app.get('status')}, "
            f"Score: {app.get('screeningScore', 'N/A')}"
        )
    
    apps_text = "\n".join(apps_summary)
    
    prompt = f"""{question}

Here are the applicants:
{apps_text}

Please answer the question based on this data."""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = await call_gemini(messages, TEXT_MODEL)
        answer = response.get("content", "Unable to generate summary")
        
        return {
            "answer": answer,
            "sources": db_applications[:20],
            "count": len(db_applications)
        }
    except Exception as e:
        print(f"⚠️ Error generating summary with Gemini: {e}")
        return {
            "answer": "Unable to generate summary",
            "sources": [],
            "count": 0
        }


async def select_best_applicant_for_property(
    user_id: str,
    property_id: str,
    property_rent: float
) -> Optional[Dict[str, Any]]:
    """
    Agent decision: Select the single best applicant for a property
    
    Returns:
        Best applicant dict or None (returns only ONE applicant)
    """
    # Query for the single best applicant
    applicants = await find_best_applicants_for_property(
        user_id=user_id,
        property_id=property_id,
        property_monthly_rent=property_rent,
        limit=1,  # Only return the single best applicant
        min_credit_score=680
    )
    
    if applicants and len(applicants) > 0:
        best = applicants[0]  # Single best applicant
        return {
            "selected": True,
            "applicant": best,
            "reason": f"Best applicant selected: {best['credit_score']} credit score, {best['income_ratio']:.2f}x income ratio"
        }
    
    return {
        "selected": False,
        "applicant": None,
        "reason": "No qualified applicants found"
    }

