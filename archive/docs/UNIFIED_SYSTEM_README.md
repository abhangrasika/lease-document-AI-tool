# PropAI Unified Backend System

A comprehensive property management AI system that combines:
- **AI Chat Interface** for property managers
- **SMS Processing** with Twilio integration
- **Message Classification** and auto-reply
- **Database Persistence** for all conversations

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Unified Backend │    │   Twilio SMS    │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│   Webhooks      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Database       │
                       │ (PostgreSQL/     │
                       │  SQLite)         │
                       └──────────────────┘
```

## Features

### 🤖 AI Chat System
- Property manager chat interface
- Context-aware responses
- Image/document analysis
- Chat history persistence

### 📱 SMS Processing
- Twilio webhook integration
- Automatic message classification
- Emergency detection and escalation
- Auto-reply generation

### 🗄️ Database Storage
- **Contacts**: Tenant information
- **Messages**: SMS conversations
- **Chat Messages**: AI chat history
- Full conversation threading

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file:
```env
# LLM Configuration
LLM_API_KEY=your_groq_api_key
LLM_MODEL=llama-3.1-8b-instant
LLM_VISION_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
LLM_URL=https://api.groq.com/openai/v1/chat/completions

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname
# OR for SQLite: DATABASE_URL=sqlite:///./propai.db

# Twilio
TWILIO_FROM_NUMBER=+1234567890
USE_FAKE_TWILIO=1

# Frontend
FRONTEND_ORIGIN=http://localhost:3000
```

### 3. Start the Backend
```bash
python start_backend.py
```

### 4. Start the Frontend
```bash
cd propai-frontend
npm install
npm run dev
```

## API Endpoints

### AI Chat
- `POST /pm_chat` - Property manager chat
- `GET /chat/{phone}` - Get chat history

### SMS & Threads
- `POST /sms` - Twilio webhook (incoming SMS)
- `GET /threads` - List all conversation threads
- `GET /threads/{phone}` - Get SMS thread for phone

### Contacts
- `POST /contacts/upsert` - Create/update contact
- `GET /contacts/{phone}` - Get contact info

### Classification
- `POST /classify` - Classify message thread

### Health & Stats
- `GET /health` - Health check
- `GET /api/stats` - Message statistics
- `GET /api/messages` - Recent messages

## Database Schema

### Contacts Table
```sql
CREATE TABLE contacts (
    phone VARCHAR PRIMARY KEY,
    tenant_name VARCHAR NOT NULL,
    unit VARCHAR NOT NULL,
    address VARCHAR NOT NULL,
    hotline VARCHAR,
    portal_url VARCHAR,
    property_name VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    message_sid VARCHAR UNIQUE NOT NULL,
    phone VARCHAR NOT NULL,
    direction VARCHAR NOT NULL, -- 'inbound' | 'outbound'
    to_number VARCHAR,
    from_number VARCHAR,
    body TEXT,
    media_urls JSON,
    status VARCHAR DEFAULT 'received',
    created_at TIMESTAMP,
    
    -- AI Classification
    category VARCHAR,
    priority VARCHAR,
    action VARCHAR,
    confidence FLOAT,
    entities JSON,
    ai_reply TEXT
);
```

### Chat Messages Table
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    phone VARCHAR NOT NULL,
    role VARCHAR NOT NULL, -- 'user' | 'assistant'
    content TEXT NOT NULL,
    image_url VARCHAR,
    document_url VARCHAR,
    created_at TIMESTAMP
);
```

## Frontend Integration

The frontend has been updated to work with the unified backend:

### AIChat Component
- Uses `/pm_chat` endpoint
- Stores chat history in database
- Supports image uploads

### TextHistory Component
- Displays SMS conversations
- Shows AI classifications
- Real-time updates

### API Functions
- `pmChat()` - Send message to AI
- `getChatHistory()` - Get chat history
- `getThread()` - Get SMS thread
- `upsertContact()` - Manage contacts

## Twilio Setup

### 1. Configure Webhook
Set your Twilio webhook URL to:
```
https://your-domain.com/sms
```

### 2. Test with Fake Twilio
For development, set `USE_FAKE_TWILIO=1` and use:
```bash
curl -X POST http://localhost:8000/sms \
  -d "From=+1234567890" \
  -d "To=+0987654321" \
  -d "Body=Hello, my sink is leaking"
```

## Message Classification

The system automatically classifies incoming SMS messages:

### Categories
- `maintenance` - Repair requests
- `rent` - Payment questions
- `general` - General inquiries
- `emergency` - Urgent issues
- `other` - Spam/unrelated

### Priorities
- `low` - Non-urgent
- `normal` - Standard priority
- `high` - Important
- `critical` - Emergency

### Actions
- `route_to_pm` - Forward to property manager
- `auto_reply` - Send automated response
- `escalate` - Urgent escalation
- `ask_clarify` - Request more information

## Emergency Detection

The system automatically detects emergency keywords:
- Gas leaks
- Fire/smoke
- Flooding
- Electrical issues
- Carbon monoxide

Emergency messages are automatically:
- Categorized as `emergency`
- Prioritized as `critical`
- Action set to `escalate`
- Reply includes emergency contact info

## Development

### Running Tests
```bash
# Test AI chat
curl -X POST http://localhost:8000/pm_chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I do about a leaky faucet?",
    "context": {
      "tenant_name": "John Doe",
      "unit": "3A",
      "address": "123 Main St",
      "hotline": "+1-555-0100"
    }
  }'

# Test SMS webhook
curl -X POST http://localhost:8000/sms \
  -d "From=+1234567890" \
  -d "To=+0987654321" \
  -d "Body=My toilet is overflowing"
```

### Database Migrations
The system uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

## Production Deployment

### Environment Variables
Set all required environment variables in your production environment.

### Database
Use PostgreSQL for production:
```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### Twilio
Configure real Twilio webhook:
```env
USE_FAKE_TWILIO=0
TWILIO_FROM_NUMBER=+1234567890
```

### CORS
Update CORS origins for your frontend domain:
```python
allow_origins=[
    "https://your-frontend-domain.com",
    "http://localhost:3000"
]
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check `DATABASE_URL` format
   - Ensure database is running
   - Verify credentials

2. **LLM API Error**
   - Check `LLM_API_KEY` is valid
   - Verify API quota/limits
   - Check model availability

3. **Twilio Webhook Not Working**
   - Verify webhook URL is accessible
   - Check Twilio configuration
   - Test with fake Twilio first

4. **Frontend Connection Issues**
   - Check `NEXT_PUBLIC_BACKEND_URL`
   - Verify CORS configuration
   - Check network connectivity

### Logs
The system provides detailed logging for debugging:
- SMS reception
- AI classification
- Database operations
- Error messages

## License

This project is licensed under the MIT License.
