# WhatsApp Marketing Automation Architecture

For the Shraddha Properties pilot, see the [pilot architecture and action
plan](./docs/PILOT-ARCHITECTURE.md). It distinguishes the deployed POC from the
proposed queue, worker, persistent state, delivery tracking, and recovery design.

## Overview

This document details the technical architecture for a comprehensive WhatsApp marketing automation platform.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Web App     │  │  Mobile App  │  │  Admin Panel │     │
│  │  (React)     │  │  (React Native)│  │  (React)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────┼─────────────────────────────────┐
│                      API Gateway (Nginx/LB)                  │
├─────────────────────────────────────────────────────────────┤
│  SSL Termination, Load Balancing, Rate Limiting              │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Campaign    │  │  Contact     │  │  Message     │     │
│  │  Service    │  │  Service    │  │  Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Analytics   │  │  Template    │  │  Integration │     │
│  │  Service    │  │  Service    │  │  Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      Message Queue                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  High        │  │  Low         │  │  Scheduled   │     │
│  │  Priority    │  │  Priority    │  │  Tasks       │     │
│  │  Queue       │  │  Queue       │  │  Queue       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      Worker Layer                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Message     │  │  Campaign    │  │  Analytics   │     │
│  │  Workers    │  │  Workers    │  │  Workers    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      External Services                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  WhatsApp    │  │  Twilio      │  │  SendGrid    │     │
│  │  Business    │  │  API         │  │  (Email)     │     │
│  │  API         │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  PostgreSQL  │  │  Redis       │  │  S3          │     │
│  │  (Primary)   │  │  (Cache)     │  │  (Media)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Core Tables

#### Users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    plan_id INTEGER REFERENCES plans(id),
    whatsapp_business_id VARCHAR(255),
    whatsapp_api_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Contacts
```sql
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    phone_number VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    tags TEXT[],
    custom_fields JSONB,
    opt_in BOOLEAN DEFAULT TRUE,
    opt_in_date TIMESTAMP,
    last_message_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, phone_number)
);
```

#### Campaigns
```sql
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id INTEGER REFERENCES templates(id),
    status VARCHAR(50) DEFAULT 'draft',
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    total_contacts INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    read_count INTEGER DEFAULT 0,
    replied_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Messages
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    contact_id INTEGER REFERENCES contacts(id),
    whatsapp_message_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    direction VARCHAR(10) DEFAULT 'outbound',
    content TEXT,
    media_url TEXT,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    failed_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Templates
```sql
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    content TEXT NOT NULL,
    variables TEXT[],
    whatsapp_template_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    rejected_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Segments
```sql
CREATE TABLE segments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    rules JSONB,
    contact_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Service Architecture

### Campaign Service

```python
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class CampaignService:
    def __init__(self, db, whatsapp_client, queue):
        self.db = db
        self.whatsapp = whatsapp_client
        self.queue = queue

    async def create_campaign(self, user_id: int, campaign_data: dict) -> dict:
        """Create a new campaign"""
        campaign = Campaign(
            user_id=user_id,
            name=campaign_data['name'],
            description=campaign_data.get('description'),
            template_id=campaign_data['template_id'],
            scheduled_at=campaign_data.get('scheduled_at')
        )
        self.db.add(campaign)
        self.db.commit()
        return campaign.to_dict()

    async def schedule_campaign(self, campaign_id: int) -> None:
        """Schedule a campaign for execution"""
        campaign = self.db.query(Campaign).get(campaign_id)
        
        # Add to scheduled queue
        self.queue.enqueue_at(
            campaign.scheduled_at,
            execute_campaign,
            campaign_id=campaign_id
        )

    async def execute_campaign(self, campaign_id: int) -> None:
        """Execute a campaign"""
        campaign = self.db.query(Campaign).get(campaign_id)
        contacts = self.get_campaign_contacts(campaign)
        
        for contact in contacts:
            message = self.create_message(campaign, contact)
            self.queue.enqueue(send_message, message.id)
        
        campaign.status = 'sent'
        campaign.sent_at = datetime.now()
        self.db.commit()

    def get_campaign_contacts(self, campaign: Campaign) -> List[Contact]:
        """Get contacts for a campaign"""
        # Apply segmentation rules
        # Filter by opt-in status
        # Return filtered contacts
        pass
```

### Message Service

```python
class MessageService:
    def __init__(self, db, whatsapp_client):
        self.db = db
        self.whatsapp = whatsapp_client

    async def send_message(self, message_id: int) -> dict:
        """Send a single message via WhatsApp"""
        message = self.db.query(Message).get(message_id)
        contact = self.db.query(Contact).get(message.contact_id)
        template = self.db.query(Template).get(message.campaign.template_id)
        
        # Personalize message
        content = self.personalize(template.content, contact)
        
        # Send via WhatsApp API
        response = self.whatsapp.send_message(
            to=contact.phone_number,
            content=content,
            media_url=message.media_url
        )
        
        # Update message status
        message.whatsapp_message_id = response['message_id']
        message.status = 'sent'
        message.sent_at = datetime.now()
        self.db.commit()
        
        return response

    def personalize(self, template: str, contact: Contact) -> str:
        """Personalize template with contact data"""
        # Replace variables with contact data
        # Handle conditional logic
        # Return personalized content
        pass

    async def handle_webhook(self, webhook_data: dict) -> None:
        """Handle WhatsApp webhook events"""
        event_type = webhook_data['event']
        message_id = webhook_data['message_id']
        
        message = self.db.query(Message).filter(
            Message.whatsapp_message_id == message_id
        ).first()
        
        if event_type == 'delivered':
            message.status = 'delivered'
            message.delivered_at = datetime.now()
        elif event_type == 'read':
            message.status = 'read'
            message.read_at = datetime.now()
        elif event_type == 'failed':
            message.status = 'failed'
            message.failed_reason = webhook_data['reason']
        
        self.db.commit()
```

### Contact Service

```python
class ContactService:
    def __init__(self, db):
        self.db = db

    async def import_contacts(self, user_id: int, file_data: bytes) -> dict:
        """Import contacts from CSV/Excel"""
        # Parse file
        contacts = self.parse_file(file_data)
        
        # Validate phone numbers
        valid_contacts = self.validate_contacts(contacts)
        
        # Insert into database
        for contact in valid_contacts:
            existing = self.db.query(Contact).filter(
                Contact.user_id == user_id,
                Contact.phone_number == contact['phone']
            ).first()
            
            if existing:
                self.update_contact(existing, contact)
            else:
                new_contact = Contact(
                    user_id=user_id,
                    **contact
                )
                self.db.add(new_contact)
        
        self.db.commit()
        return {'imported': len(valid_contacts)}

    def segment_contacts(self, user_id: int, rules: dict) -> List[Contact]:
        """Segment contacts based on rules"""
        query = self.db.query(Contact).filter(Contact.user_id == user_id)
        
        # Apply segmentation rules
        for rule in rules:
            field = rule['field']
            operator = rule['operator']
            value = rule['value']
            
            if operator == 'equals':
                query = query.filter(getattr(Contact, field) == value)
            elif operator == 'contains':
                query = query.filter(getattr(Contact, field).contains(value))
            # ... other operators
        
        return query.all()
```

### Analytics Service

```python
class AnalyticsService:
    def __init__(self, db):
        self.db = db

    def get_campaign_metrics(self, campaign_id: int) -> dict:
        """Get comprehensive campaign metrics"""
        campaign = self.db.query(Campaign).get(campaign_id)
        
        return {
            'total_contacts': campaign.total_contacts,
            'sent': campaign.sent_count,
            'delivered': campaign.delivered_count,
            'read': campaign.read_count,
            'replied': campaign.replied_count,
            'delivery_rate': campaign.delivered_count / campaign.sent_count if campaign.sent_count > 0 else 0,
            'read_rate': campaign.read_count / campaign.delivered_count if campaign.delivered_count > 0 else 0,
            'reply_rate': campaign.replied_count / campaign.read_count if campaign.read_count > 0 else 0
        }

    def get_user_metrics(self, user_id: int, date_range: tuple) -> dict:
        """Get user metrics over time"""
        # Query messages sent, delivered, read
        # Calculate rates
        # Return time-series data
        pass

    def get_funnel_analysis(self, campaign_id: int) -> dict:
        """Analyze conversion funnel"""
        # Track user journey
        # Calculate conversion rates at each stage
        # Identify drop-off points
        pass
```

## WhatsApp Integration

### WhatsApp Business API Client

```python
import requests
from typing import Dict, Optional

class WhatsAppBusinessAPI:
    def __init__(self, api_key: str, phone_number_id: str):
        self.api_key = api_key
        self.phone_number_id = phone_number_id
        self.base_url = f"https://graph.facebook.com/v18.0/{phone_number_id}"

    def send_message(self, to: str, content: str, 
                     media_url: Optional[str] = None) -> Dict:
        """Send a message via WhatsApp Business API"""
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text" if not media_url else "media"
        }
        
        if media_url:
            data["media"] = {"link": media_url}
        else:
            data["text"] = {"body": content}
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def send_template_message(self, to: str, template_name: str, 
                              parameters: Dict) -> Dict:
        """Send a template message"""
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en_US"},
                "components": [
                    {
                        "type": "body",
                        "parameters": parameters
                    }
                ]
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def get_message_status(self, message_id: str) -> Dict:
        """Get message status"""
        url = f"{self.base_url}/messages/{message_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.get(url, headers=headers)
        return response.json()
```

### Webhook Handler

```python
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle WhatsApp webhook events"""
    data = await request.json()
    
    # Verify webhook signature
    if not verify_webhook_signature(request):
        raise HTTPException(status_code=401)
    
    # Process webhook
    event_type = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})
    
    if event_type.get('field') == 'messages':
        message_data = event_type.get('messages', [{}])[0]
        message_id = message_data.get('id')
        status = message_data.get('status')
        
        # Update message status in database
        message_service.handle_webhook({
            'event': status,
            'message_id': message_id
        })
    
    return {"status": "success"}

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """Verify webhook with WhatsApp"""
    mode = request.query_params.get('hub.mode')
    token = request.query_params.get('hub.verify_token')
    challenge = request.query_params.get('hub.challenge')
    
    if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
        return int(challenge)
    
    raise HTTPException(status_code=403)
```

## Task Queue Implementation

### Celery Configuration

```python
from celery import Celery

celery = Celery('whatsapp_marketing')

celery.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    task_routes={
        'tasks.send_message': {'queue': 'high_priority'},
        'tasks.execute_campaign': {'queue': 'low_priority'},
        'tasks.generate_analytics': {'queue': 'scheduled'},
    }
)

@celery.task
def send_message(message_id: int):
    """Send a message task"""
    message_service = MessageService(db, whatsapp_client)
    return await message_service.send_message(message_id)

@celery.task
def execute_campaign(campaign_id: int):
    """Execute a campaign task"""
    campaign_service = CampaignService(db, whatsapp_client, celery)
    return await campaign_service.execute_campaign(campaign_id)

@celery.task
def generate_analytics(user_id: int, date_range: tuple):
    """Generate analytics report task"""
    analytics_service = AnalyticsService(db)
    return await analytics_service.generate_report(user_id, date_range)
```

## API Design

### REST Endpoints

#### Campaigns
```
POST   /api/campaigns              Create campaign
GET    /api/campaigns              List campaigns
GET    /api/campaigns/:id          Get campaign details
PUT    /api/campaigns/:id          Update campaign
DELETE /api/campaigns/:id          Delete campaign
POST   /api/campaigns/:id/schedule Schedule campaign
POST   /api/campaigns/:id/execute  Execute campaign immediately
```

#### Contacts
```
POST   /api/contacts/import        Import contacts
GET    /api/contacts              List contacts
GET    /api/contacts/:id          Get contact details
PUT    /api/contacts/:id          Update contact
DELETE /api/contacts/:id          Delete contact
POST   /api/contacts/segment     Segment contacts
GET    /api/segments              List segments
POST   /api/segments              Create segment
```

#### Messages
```
GET    /api/messages              List messages
GET    /api/messages/:id          Get message details
POST   /api/messages/send        Send single message
POST   /api/messages/bulk       Bulk send messages
```

#### Templates
```
POST   /api/templates              Create template
GET    /api/templates              List templates
GET    /api/templates/:id          Get template details
PUT    /api/templates/:id          Update template
DELETE /api/templates/:id          Delete template
POST   /api/templates/:id/submit  Submit to WhatsApp for approval
```

#### Analytics
```
GET    /api/analytics/campaigns/:id Get campaign analytics
GET    /api/analytics/overview     Get overview metrics
GET    /api/analytics/funnel/:id  Get funnel analysis
GET    /api/analytics/export       Export analytics data
```

## Security Implementation

### Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/messages/send")
@limiter.limit("100/minute")
async def send_message_endpoint(message_data: dict, user_id: int = Depends(verify_token)):
    """Send message with rate limiting"""
    return await message_service.send_message(user_id, message_data)
```

## Performance Optimization

### Database Optimization
- Connection pooling
- Query optimization with indexes
- Read replicas for analytics queries
- Caching frequently accessed data

### Caching Strategy
```python
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

def get_contact(contact_id: int):
    """Get contact with caching"""
    cache_key = f"contact:{contact_id}"
    cached = cache.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    contact = db.query(Contact).get(contact_id)
    cache.setex(cache_key, 3600, json.dumps(contact.to_dict()))
    return contact
```

### Batch Processing
- Batch message sending
- Bulk contact operations
- Scheduled analytics generation
- Asynchronous processing for long tasks

## Monitoring & Logging

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
messages_sent = Counter('messages_sent_total', 'Total messages sent')
messages_delivered = Counter('messages_delivered_total', 'Total messages delivered')
messages_failed = Counter('messages_failed_total', 'Total messages failed')
campaigns_created = Counter('campaigns_created_total', 'Total campaigns created')
message_latency = Histogram('message_latency_seconds', 'Message send latency')
active_users = Gauge('active_users', 'Number of active users')
```

### Logging
```python
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
```

## Deployment Architecture

### Docker Configuration

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whatsapp-marketing-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: whatsapp-marketing-api
  template:
    metadata:
      labels:
        app: whatsapp-marketing-api
    spec:
      containers:
      - name: api
        image: whatsapp-marketing-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Conclusion

The WhatsApp Marketing Automation architecture provides a scalable, secure, and feature-rich platform for managing WhatsApp marketing campaigns. By leveraging modern technologies and best practices, the system can handle high message volumes while maintaining reliability and performance.

Success requires attention to WhatsApp's policies, user privacy, and compliance with relevant regulations. The architecture is designed to be flexible and extensible to support future growth and feature additions.
