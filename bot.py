"""
WhatsApp Auto-Reply Bot
A simple bot that automatically replies to incoming WhatsApp messages
"""

import os
import logging
from flask import Flask, request, jsonify
import boto3
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# WhatsApp Business API configuration
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'your_verify_token')

# DynamoDB table for storing conversations (optional)
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', 'whatsapp-conversations')

# Simple in-memory storage for auto-reply messages (can be replaced with database)
AUTO_REPLY_MESSAGES = {
    'default': "Hello! Thank you for your message. This is an automated response. Our team will get back to you shortly.",
    'greeting': "Hi there! 👋 Welcome to our WhatsApp business account. How can we help you today?",
    'hours': "Our business hours are 9 AM - 6 PM, Monday to Friday. We'll respond as soon as possible!",
    'support': "For support, please email us at support@example.com or call +1-234-567-8900."
}

# Initialize DynamoDB client if table is configured
dynamodb = None
if DYNAMODB_TABLE != 'whatsapp-conversations':
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(DYNAMODB_TABLE)
        logger.info(f"Connected to DynamoDB table: {DYNAMODB_TABLE}")
    except Exception as e:
        logger.warning(f"Could not connect to DynamoDB: {e}")
        dynamodb = None


def get_auto_reply_message(incoming_message: str, phone_number: str) -> str:
    """
    Generate an auto-reply based on the incoming message content
    """
    message_lower = incoming_message.lower()
    
    # Check for keywords to determine response
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return AUTO_REPLY_MESSAGES['greeting']
    elif any(word in message_lower for word in ['hours', 'time', 'when', 'open']):
        return AUTO_REPLY_MESSAGES['hours']
    elif any(word in message_lower for word in ['help', 'support', 'issue', 'problem']):
        return AUTO_REPLY_MESSAGES['support']
    else:
        return AUTO_REPLY_MESSAGES['default']


def save_conversation(phone_number: str, incoming_message: str, reply_message: str):
    """
    Save conversation to DynamoDB (if configured)
    """
    if dynamodb is None:
        return
    
    try:
        table.put_item(
            Item={
                'phone_number': phone_number,
                'timestamp': datetime.now().isoformat(),
                'incoming_message': incoming_message,
                'reply_message': reply_message
            }
        )
        logger.info(f"Saved conversation for {phone_number}")
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")


@app.route('/webhook/whatsapp', methods=['GET'])
def verify_webhook():
    """
    Verify webhook with WhatsApp
    This is required when setting up the webhook in WhatsApp Business API
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return challenge, 200
    else:
        logger.warning("Webhook verification failed")
        return jsonify({'status': 'error', 'message': 'Invalid verification token'}), 403


@app.route('/webhook/whatsapp', methods=['POST'])
def webhook_handler():
    """
    Handle incoming WhatsApp messages
    """
    data = request.json
    
    logger.info(f"Received webhook event: {json.dumps(data, indent=2)}")
    
    try:
        # Extract message details
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if value.get('field') == 'messages':
            messages = value.get('messages', [])
            
            for message in messages:
                # Extract message details
                phone_number = message.get('from')
                message_id = message.get('id')
                message_type = message.get('type')
                
                # Handle text messages
                if message_type == 'text':
                    text_content = message.get('text', {}).get('body', '')
                    logger.info(f"Received message from {phone_number}: {text_content}")
                    
                    # Generate auto-reply
                    reply_message = get_auto_reply_message(text_content, phone_number)
                    
                    # Send reply
                    send_whatsapp_message(phone_number, reply_message)
                    
                    # Save conversation
                    save_conversation(phone_number, text_content, reply_message)
                    
                # Handle other message types (media, location, etc.)
                else:
                    logger.info(f"Received {message_type} message from {phone_number}")
                    reply_message = AUTO_REPLY_MESSAGES['default']
                    send_whatsapp_message(phone_number, reply_message)
                    save_conversation(phone_number, f"[{message_type}] message", reply_message)
        
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def send_whatsapp_message(phone_number: str, message: str):
    """
    Send a message via WhatsApp Business API
    """
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    try:
        import requests
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            logger.info(f"Message sent successfully to {phone_number}")
            return response.json()
        else:
            logger.error(f"Failed to send message: {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/config/replies', methods=['GET', 'POST'])
def manage_replies():
    """
    Get or update auto-reply messages
    """
    if request.method == 'GET':
        return jsonify(AUTO_REPLY_MESSAGES)
    
    elif request.method == 'POST':
        new_replies = request.json
        AUTO_REPLY_MESSAGES.update(new_replies)
        logger.info(f"Updated auto-reply messages: {new_replies}")
        return jsonify({'status': 'success', 'messages': AUTO_REPLY_MESSAGES})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting WhatsApp Auto-Reply Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
