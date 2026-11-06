"""
Test script to simulate WhatsApp webhook events
"""

import requests
import json

# Bot endpoint
WEBHOOK_URL = "http://127.0.0.1:5001/webhook/whatsapp"

# Simulate a WhatsApp webhook event
def test_webhook(message_text="Hello"):
    """
    Simulate a WhatsApp webhook event with a text message
    """
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1234567890",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+1234567890",
                                "phone_number_id": "1234567890"
                            },
                            "contacts": [
                                {
                                    "input": "from",
                                    "wa_id": "15555555555",
                                    "profile": {
                                        "name": "Test User"
                                    }
                                }
                            ],
                            "messages": [
                                {
                                    "from": "15555555555",
                                    "id": "wamid.H4yKdYY2LJQ9JL5xJpZ",
                                    "timestamp": 1699280000,
                                    "text": {
                                        "body": message_text
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    print(f"Sending test webhook with message: '{message_text}'")
    print(f"URL: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(webhook_data, indent=2)}")

    try:
        response = requests.post(WEBHOOK_URL, json=webhook_data)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"\nError: {e}")
        return None


if __name__ == "__main__":
    print("=== WhatsApp Auto-Reply Bot Test ===\n")
    
    # Test 1: Greeting message
    print("Test 1: Greeting message")
    test_webhook("Hello")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Hours query
    print("Test 2: Hours query")
    test_webhook("What are your business hours?")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Support request
    print("Test 3: Support request")
    test_webhook("I need help with my order")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Random message
    print("Test 4: Random message")
    test_webhook("I have a question about your products")
