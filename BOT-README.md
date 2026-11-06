# WhatsApp Auto-Reply Bot

A simple WhatsApp auto-reply bot that automatically responds to incoming messages sent to your WhatsApp Business number.

## Features

- **Auto-Reply**: Automatically replies to incoming messages
- **Keyword-Based Responses**: Different responses based on message content
- **Webhook Handler**: Receives and processes WhatsApp webhook events
- **Conversation Logging**: Optionally stores conversations in DynamoDB
- **Customizable Replies**: Configure auto-reply messages via API
- **Health Check**: Endpoint to monitor bot status

## Quick Start

### Prerequisites

1. WhatsApp Business Account with API access
2. AWS Account (optional, for DynamoDB)
3. Python 3.9+

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your credentials
# Add your WhatsApp Business API credentials
```

### Configuration

Set the following environment variables in `.env`:

```bash
# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
VERIFY_TOKEN=your_verify_token

# AWS (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
DYNAMODB_TABLE=whatsapp-conversations

# Server
PORT=5000
```

### Running the Bot

```bash
# Run the bot
python bot.py
```

The bot will start on port 5000 by default.

## Setting Up WhatsApp Webhook

1. **Deploy the bot** to a server (AWS, Heroku, Railway, etc.)
2. **Get the webhook URL**: `https://your-domain.com/webhook/whatsapp`
3. **Configure WhatsApp Business API**:
   - Go to WhatsApp Business API console
   - Navigate to Webhooks
   - Add your webhook URL
   - Set verify token to match your `VERIFY_TOKEN`
   - Subscribe to `messages` field

## Auto-Reply Messages

The bot comes with default auto-reply messages:

```python
AUTO_REPLY_MESSAGES = {
    'default': "Hello! Thank you for your message...",
    'greeting': "Hi there! 👋 Welcome to our WhatsApp business account...",
    'hours': "Our business hours are 9 AM - 6 PM...",
    'support': "For support, please email us at support@example.com..."
}
```

### Customizing Replies

You can customize replies by:

1. **Edit the code**: Modify `AUTO_REPLY_MESSAGES` in `bot.py`
2. **Use the API**: Send a POST request to `/config/replies`

```bash
curl -X POST http://localhost:5000/config/replies \
  -H "Content-Type: application/json" \
  -d '{"custom": "Your custom message here"}'
```

## API Endpoints

### Webhook Endpoints

#### Verify Webhook
```
GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE
```

#### Receive Messages
```
POST /webhook/whatsapp
```

### Management Endpoints

#### Health Check
```
GET /health
```

#### Get Auto-Reply Messages
```
GET /config/replies
```

#### Update Auto-Reply Messages
```
POST /config/replies
Content-Type: application/json

{
  "custom": "Your custom message",
  "greeting": "Updated greeting message"
}
```

## Keyword Detection

The bot automatically detects keywords in incoming messages:

- **Greetings**: hello, hi, hey, greetings
- **Hours/Time**: hours, time, when, open
- **Support**: help, support, issue, problem
- **Default**: Any other message

## Conversation Logging (Optional)

The bot can log conversations to DynamoDB:

1. Create a DynamoDB table named `whatsapp-conversations`
2. Add AWS credentials to `.env`
3. The bot will automatically save:
   - Phone number
   - Timestamp
   - Incoming message
   - Reply message

## Deployment

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

EXPOSE 5000

CMD ["python", "bot.py"]
```

### Using AWS Lambda + API Gateway

You can deploy this as a serverless function using AWS Lambda and API Gateway for better scalability and cost efficiency.

### Using Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create whatsapp-auto-reply-bot

# Set environment variables
heroku config:set WHATSAPP_PHONE_NUMBER_ID=your_id
heroku config:set WHATSAPP_ACCESS_TOKEN=your_token
heroku config:set VERIFY_TOKEN=your_token

# Deploy
git push heroku main
```

## Testing

### Local Testing

You can test the webhook locally using ngrok:

```bash
# Install ngrok
brew install ngrok

# Start ngrok
ngrok http 5000

# Use the ngrok URL in WhatsApp webhook configuration
```

### Testing Webhook

```bash
# Test health check
curl http://localhost:5000/health

# Test get replies
curl http://localhost:5000/config/replies

# Test update replies
curl -X POST http://localhost:5000/config/replies \
  -H "Content-Type: application/json" \
  -d '{"test": "Test message"}'
```

## Example Workflow

1. User sends message: "Hello"
2. Bot receives webhook event
3. Bot detects "hello" keyword
4. Bot replies with greeting message
5. Conversation is logged to DynamoDB (if configured)

## Troubleshooting

### Webhook Not Receiving Messages
- Verify webhook URL is correct
- Check verify token matches
- Ensure WhatsApp Business API is subscribed to messages
- Check server logs for errors

### Messages Not Sending
- Verify phone number ID is correct
- Check access token is valid
- Ensure phone number is verified
- Check API rate limits

### DynamoDB Errors
- Verify AWS credentials are correct
- Ensure table exists
- Check IAM permissions

## Security Considerations

- Never commit `.env` file with credentials
- Use environment variables for sensitive data
- Implement rate limiting for webhook endpoint
- Validate incoming webhook requests
- Use HTTPS in production
- Regularly rotate access tokens

## Limitations

- Simple keyword-based detection (can be enhanced with NLP)
- In-memory storage for replies (use database for production)
- No conversation context awareness
- No support for media messages (can be added)
- Basic error handling (can be enhanced)

## Future Enhancements

- **NLP Integration**: Use AI for smarter responses
- **Conversation Context**: Remember previous messages
- **Media Support**: Handle images, videos, documents
- **Multi-Language**: Support multiple languages
- **Analytics Dashboard**: Track message statistics
- **Integration**: Connect with CRM systems
- **Scheduled Messages**: Send messages at specific times
- **User Segmentation**: Different responses for different users

## License

MIT

## Support

For issues or questions:
- Open an issue on GitHub
- Check WhatsApp Business API documentation: https://developers.facebook.com/docs/whatsapp
