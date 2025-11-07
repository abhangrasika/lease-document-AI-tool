#!/usr/bin/env python3
"""
Script to fetch all applications and ask Gemini AI for the best applicant
Uses the internal API endpoint to fetch applications (no direct DB access needed)
"""

import os
import sys
import json
import httpx
import asyncio
from typing import List, Dict, Any

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('LLM_API_KEY') or ''
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'

if not GEMINI_API_KEY:
    print('❌ GEMINI_API_KEY or LLM_API_KEY environment variable not set')
    sys.exit(1)

# Frontend API Configuration
FRONTEND_URL = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')
SERVICE_TOKEN = os.getenv('APPLICATION_SERVICE_TOKEN', '')  # Must be set via environment variable


def format_application_for_gemini(app: Dict[str, Any], index: int) -> str:
    """Format a single application for Gemini analysis"""
    property_info = 'No property assigned'
    if app.get('property'):
        prop = app['property']
        property_info = prop.get('name') or prop.get('address') or 'Unknown Property'
    
    monthly_income = app.get('monthlyIncome')
    annual_income = app.get('annualIncome')
    
    formatted = f"""
Application #{index + 1}:
- Name: {app.get('applicantName', 'Unknown')}
- Email: {app.get('applicantEmail', 'Not provided')}
- Phone: {app.get('applicantPhone') or 'Not provided'}
- Credit Score: {app.get('creditScore') or 'Not provided'}"""
    
    if monthly_income:
        formatted += f"\n- Monthly Income: ${monthly_income:,.2f}"
    else:
        formatted += "\n- Monthly Income: Not provided"
    
    if annual_income:
        formatted += f"\n- Annual Income: ${annual_income:,.2f}"
    else:
        formatted += "\n- Annual Income: Not provided"
    formatted += f"""
- Employer: {app.get('employerName') or 'Not provided'}
- Screening Score: {app.get('screeningScore') or 'Not provided'}
- Status: {app.get('status', 'pending')}
- Property: {property_info}
- Application ID: {app.get('id', 'Unknown')}"""
    
    if app.get('screeningNotes'):
        formatted += f"""
- Notes: {app['screeningNotes']}"""
    
    return formatted


async def fetch_applications_from_api(user_id: str = None) -> List[Dict[str, Any]]:
    """Fetch applications from the internal API endpoint"""
    print('📊 Fetching applications from API...\n')
    
    # If no user_id provided, try to get from environment or use a default
    if not user_id:
        user_id = os.getenv('USER_ID', 'cmgk8d5yz0000l104mkwr8j0w')  # Default to Michael Wang
    
    api_url = f"{FRONTEND_URL}/api/applications/internal"
    print(f'🔗 Using API endpoint: {api_url}')
    print(f'👤 User ID: {user_id}\n')
    headers = {
        "Content-Type": "application/json"
    }
    
    if SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {SERVICE_TOKEN}"
    
    params = {"userId": user_id}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, headers=headers, params=params)
            
            if response.status_code == 401:
                print('❌ Unauthorized. Please set APPLICATION_SERVICE_TOKEN environment variable.')
                print('   Or run the script with proper authentication.\n')
                return []
            
            response.raise_for_status()
            result = response.json()
            applications = result.get('applications', [])
            
            print(f'✅ Found {len(applications)} applications\n')
            return applications
            
    except httpx.HTTPError as e:
        print(f'❌ Error fetching applications from API: {e}')
        print(f'   URL: {api_url}')
        print(f'   Make sure the frontend is running on {FRONTEND_URL}\n')
        return []
    except Exception as e:
        print(f'❌ Unexpected error: {e}\n')
        return []


async def ask_gemini_for_best_applicant(applications: List[Dict[str, Any]]):
    """Send all applications to Gemini and ask for the best applicant"""
    print('🤖 Sending applications to Gemini AI...\n')
    
    if not applications:
        print('⚠️  No applications to analyze')
        return
    
    # Format all applications
    applications_text = '\n---\n'.join(
        format_application_for_gemini(app, idx) 
        for idx, app in enumerate(applications)
    )
    
    prompt = """You are a property management expert. Analyze the following tenant applications and identify the BEST applicant based on:
1. Credit score (higher is better)
2. Income stability and amount (higher income relative to typical rent is better)
3. Screening score (green > yellow > red)
4. Overall financial stability
5. Completeness of application (has all required documents)

Here are all the applications:

""" + applications_text + """

Please provide:
1. The name of the BEST applicant
2. Their email address
3. A brief explanation (2-3 sentences) of why they are the best choice
4. Any concerns or red flags to be aware of

Format your response clearly."""
    
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            if not response.is_success:
                error_text = await response.aread()
                raise Exception(f"Gemini API error: {response.status_code} - {error_text.decode()}")
            
            data = response.json()
            
            if data.get('candidates') and data['candidates'][0].get('content'):
                text_parts = ''.join(
                    part.get('text', '') 
                    for part in data['candidates'][0]['content'].get('parts', [])
                    if part.get('text')
                )
                
                print('🎯 GEMINI AI ANALYSIS:\n')
                print('=' * 60)
                print(text_parts)
                print('=' * 60)
                print('\n')
                
                return text_parts
            else:
                raise Exception('No response generated from Gemini')
                
    except Exception as e:
        print(f'❌ Error calling Gemini API: {e}\n')
        raise


async def main():
    """Main function"""
    try:
        # Fetch all applications
        user_id = sys.argv[1] if len(sys.argv) > 1 else None
        applications = await fetch_applications_from_api(user_id)
        
        if not applications:
            print('⚠️  No applications found. Make sure:')
            print('   1. Applications exist in the database')
            print('   2. The frontend API is running and accessible')
            print('   3. APPLICATION_SERVICE_TOKEN is set if required')
            return
        
        # Display summary
        print('📋 Applications Summary:')
        print('-' * 60)
        for idx, app in enumerate(applications, 1):
            credit = app.get('creditScore') or 'N/A'
            score = app.get('screeningScore') or 'N/A'
            status = app.get('status', 'pending')
            print(f'{idx}. {app.get("applicantName", "Unknown")} - Credit: {credit}, Score: {score}, Status: {status}')
        print('-' * 60)
        print('\n')
        
        # Ask Gemini for best applicant
        await ask_gemini_for_best_applicant(applications)
        
    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
        sys.exit(0)
    except Exception as e:
        print(f'❌ Fatal error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

