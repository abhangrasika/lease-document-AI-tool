import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

const SERVICE_TOKEN = process.env.APPLICATION_SERVICE_TOKEN || "";

if (!SERVICE_TOKEN) {
  console.warn("⚠️ APPLICATION_SERVICE_TOKEN not set - internal API endpoints will be disabled");
}

/**
 * Internal API endpoint for creating applications from email processing
 * This endpoint is called by the backend (Python/FastAPI) when processing emails
 * It uses a service token for authentication instead of user sessions
 */
export async function POST(request: NextRequest) {
  try {
    // Verify service token
    if (!SERVICE_TOKEN) {
      return NextResponse.json(
        { error: "Service token not configured" },
        { status: 503 }
      );
    }
    
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    
    if (token !== SERVICE_TOKEN) {
      return NextResponse.json(
        { error: "Unauthorized - Invalid service token" },
        { status: 401 }
      );
    }

    const body = await request.json();
    const {
      userId,  // Required - which property manager this belongs to
      propertyId,
      applicantName,
      applicantEmail,
      applicantPhone,
      emailSubject,
      emailBody,
      driversLicenseUrl,
      payStubUrls,
      creditScoreUrl,
      // Extracted data
      licenseName,
      licenseDOB,
      licenseExpiration,
      licenseNumber,
      employerName,
      monthlyIncome,
      annualIncome,
      payFrequency,
      creditScore,
      creditScoreDate,
      status,
      screeningScore,
      screeningNotes
    } = body;

    if (!userId || !applicantName || !applicantEmail) {
      return NextResponse.json(
        { error: "userId, applicantName, and applicantEmail are required" },
        { status: 400 }
      );
    }

    // Create application in database
    const application = await prisma.tenantApplication.create({
      data: {
        userId,
        propertyId: propertyId || null,
        applicantName,
        applicantEmail,
        applicantPhone: applicantPhone || null,
        emailSubject: emailSubject || null,
        emailBody: emailBody || null,
        driversLicenseUrl: driversLicenseUrl || null,
        payStubUrls: payStubUrls || [],
        creditScoreUrl: creditScoreUrl || null,
        // Extracted data
        licenseName: licenseName || null,
        licenseDOB: licenseDOB ? new Date(licenseDOB) : null,
        licenseExpiration: licenseExpiration ? new Date(licenseExpiration) : null,
        licenseNumber: licenseNumber || null,
        employerName: employerName || null,
        monthlyIncome: monthlyIncome || null,
        annualIncome: annualIncome || null,
        payFrequency: payFrequency || null,
        creditScore: creditScore || null,
        creditScoreDate: creditScoreDate ? new Date(creditScoreDate) : null,
        status: status || "pending",
        screeningScore: screeningScore || null,
        screeningNotes: screeningNotes || null,
        receivedAt: new Date()
      },
      include: {
        property: {
          select: {
            id: true,
            name: true,
            address: true
          }
        }
      }
    });

    console.log(`✅ Created application ${application.id} from email for user ${userId}`);

    return NextResponse.json({
      success: true,
      application
    });
  } catch (error) {
    console.error("Error creating application from email:", error);
    return NextResponse.json(
      { 
        error: "Failed to create application",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}

/**
 * Internal API endpoint for fetching applications (used by backend for ranking)
 * GET /api/applications/internal?userId=xxx&propertyId=xxx
 */
export async function GET(request: NextRequest) {
  try {
    // Verify service token
    if (!SERVICE_TOKEN) {
      return NextResponse.json(
        { error: "Service token not configured" },
        { status: 503 }
      );
    }
    
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    
    if (token !== SERVICE_TOKEN) {
      return NextResponse.json(
        { error: "Unauthorized - Invalid service token" },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const userId = searchParams.get("userId");
    const propertyId = searchParams.get("propertyId");

    if (!userId) {
      return NextResponse.json(
        { error: "userId is required" },
        { status: 400 }
      );
    }

    const where: any = {
      userId
    };

    if (propertyId) {
      where.propertyId = propertyId;
    }

    const applications = await prisma.tenantApplication.findMany({
      where,
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
        receivedAt: "desc"
      }
    });

    return NextResponse.json({
      success: true,
      applications
    });
  } catch (error) {
    console.error("Error fetching applications:", error);
    return NextResponse.json(
      { 
        error: "Failed to fetch applications",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}

