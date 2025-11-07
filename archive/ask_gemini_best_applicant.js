// Script to fetch all applications from database and ask Gemini for the best applicant
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || process.env.LLM_API_KEY || '';
const GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

if (!GEMINI_API_KEY) {
  console.error('❌ GEMINI_API_KEY or LLM_API_KEY environment variable not set');
  process.exit(1);
}

async function fetchAllApplications() {
  console.log('📊 Fetching all applications from database...\n');
  
  try {
    const applications = await prisma.tenantApplication.findMany({
      include: {
        property: {
          select: {
            id: true,
            name: true,
            address: true
          }
        }
      },
      orderBy: {
        receivedAt: 'desc'
      }
    });
    
    console.log(`✅ Found ${applications.length} applications\n`);
    return applications;
  } catch (error) {
    console.error('❌ Error fetching applications:', error);
    throw error;
  }
}

function formatApplicationForGemini(app, index) {
  const property = app.property ? `${app.property.name || app.property.address || 'Unknown Property'}` : 'No property assigned';
  
  return `
Application #${index + 1}:
- Name: ${app.applicantName}
- Email: ${app.applicantEmail}
- Phone: ${app.applicantPhone || 'Not provided'}
- Credit Score: ${app.creditScore || 'Not provided'}
- Monthly Income: ${app.monthlyIncome ? `$${app.monthlyIncome.toLocaleString()}` : 'Not provided'}
- Annual Income: ${app.annualIncome ? `$${app.annualIncome.toLocaleString()}` : 'Not provided'}
- Employer: ${app.employerName || 'Not provided'}
- Screening Score: ${app.screeningScore || 'Not provided'}
- Status: ${app.status}
- Property: ${property}
- Application ID: ${app.id}
${app.screeningNotes ? `- Notes: ${app.screeningNotes}` : ''}
`;
}

async function askGeminiForBestApplicant(applications) {
  console.log('🤖 Sending applications to Gemini AI...\n');
  
  if (applications.length === 0) {
    console.log('⚠️  No applications to analyze');
    return;
  }
  
  // Format all applications
  const applicationsText = applications.map((app, idx) => 
    formatApplicationForGemini(app, idx)
  ).join('\n---\n');
  
  const prompt = `You are a property management expert. Analyze the following tenant applications and identify the BEST applicant based on:
1. Credit score (higher is better)
2. Income stability and amount (higher income relative to typical rent is better)
3. Screening score (green > yellow > red)
4. Overall financial stability
5. Completeness of application (has all required documents)

Here are all the applications:

${applicationsText}

Please provide:
1. The name of the BEST applicant
2. Their email address
3. A brief explanation (2-3 sentences) of why they are the best choice
4. Any concerns or red flags to be aware of

Format your response clearly.`;

  const payload = {
    contents: [{
      role: 'user',
      parts: [{ text: prompt }]
    }],
    generationConfig: {
      temperature: 0.3,
      maxOutputTokens: 1024,
    }
  };

  try {
    const response = await fetch(`${GEMINI_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Gemini API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    
    if (data.candidates && data.candidates[0] && data.candidates[0].content) {
      const textParts = data.candidates[0].content.parts
        .filter(part => part.text)
        .map(part => part.text)
        .join('');
      
      console.log('🎯 GEMINI AI ANALYSIS:\n');
      console.log('='.repeat(60));
      console.log(textParts);
      console.log('='.repeat(60));
      console.log('\n');
      
      return textParts;
    } else {
      throw new Error('No response generated from Gemini');
    }
  } catch (error) {
    console.error('❌ Error calling Gemini API:', error);
    throw error;
  }
}

async function main() {
  try {
    // Fetch all applications
    const applications = await fetchAllApplications();
    
    // Display summary
    console.log('📋 Applications Summary:');
    console.log('-'.repeat(60));
    applications.forEach((app, idx) => {
      console.log(`${idx + 1}. ${app.applicantName} - Credit: ${app.creditScore || 'N/A'}, Score: ${app.screeningScore || 'N/A'}, Status: ${app.status}`);
    });
    console.log('-'.repeat(60));
    console.log('\n');
    
    // Ask Gemini for best applicant
    await askGeminiForBestApplicant(applications);
    
  } catch (error) {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

main();

