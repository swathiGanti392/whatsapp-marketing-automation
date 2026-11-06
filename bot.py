"""Shraddha Properties webhook, workflow simulation, and test lead APIs."""

import os
import logging
from flask import Flask, request, jsonify, abort
from twilio.request_validator import RequestValidator
from conversation import run_workflow
from lead_analytics import save_submission, analytics
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import json
from datetime import datetime, timezone
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024


@app.after_request
def test_cors(response):
    origin = request.headers.get('Origin', '')
    allowed = os.getenv('TEST_SITE_ORIGIN', '')
    if allowed and origin == allowed and request.path in ('/test/workflow','/test/leads','/test/analytics'):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Vary'] = 'Origin'
    return response


@app.route('/test/leads',methods=['POST','OPTIONS'])
def submit_lead():
    if request.method=='OPTIONS': return '',204
    try:
        result=save_submission(request.get_json(silent=True))
        if not result['duplicate']:
            logger.warning(json.dumps({'event':'lead_saved','kind':result['kind'],'source':'web_test'}))
        return jsonify(result),200 if result['duplicate'] else 201
    except ValueError as e:
        return jsonify({'error':str(e)}),400
    except Exception as e:
        logger.error('Lead storage failed (%s)',type(e).__name__)
        return jsonify({'error':'Could not save your request. Retry with the same submission.'}),503


@app.route('/test/analytics',methods=['GET','OPTIONS'])
def lead_dashboard():
    if request.method=='OPTIONS': return '',204
    days=request.args.get('days','7')
    if days not in ('7','30'): return jsonify({'error':'Choose 7 or 30 days.'}),400
    try:
        response=jsonify(analytics(int(days)))
        response.headers['Cache-Control']='no-store'
        return response
    except Exception as e:
        logger.error('Lead analytics failed (%s)',type(e).__name__)
        return jsonify({'error':'Analytics are temporarily unavailable. Please refresh.'}),503


@app.route('/test/workflow', methods=['POST', 'OPTIONS'])
def test_workflow():
    """Public demo simulation only: no Twilio sends, credentials or private logs."""
    if request.method == 'OPTIONS':
        return '', 204
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('message'), str):
        return jsonify({'error':'Please provide a text message.'}), 400
    if not data['message'].strip() or len(data['message']) > 1000:
        return jsonify({'error':'Enter a message between 1 and 1,000 characters.'}), 400
    result = run_workflow(data['message'])
    logger.warning(json.dumps({'event':'workflow_test_response','workflow':result,'delivery':'captured_only'}))
    return jsonify({**result, 'mode':'capture', 'engine':'live_aws',
                    'trace':['receive','recognize','catalog','generate','capture']}), 200

@lru_cache(maxsize=1)
def get_twilio_client():
    """Initialize sending only when requested; capture mode needs no REST client."""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    if not account_sid or not token:
        raise RuntimeError('Twilio sending credentials are not configured')
    return Client(account_sid, token)


@app.route('/webhook/whatsapp', methods=['POST'])
def webhook_handler():
    """
    Handle incoming WhatsApp messages from Twilio
    """
    # Fail closed; pin the exact external URL so proxy headers cannot change it.
    token = os.getenv('TWILIO_AUTH_TOKEN', '')
    external_url = os.getenv('TWILIO_WEBHOOK_URL') or request.environ.get('twilio.external_url', '')
    if not token or not external_url:
        return jsonify({'error': 'Webhook security is not configured'}), 503
    if not RequestValidator(token).validate(
            external_url, request.form, request.headers.get('X-Twilio-Signature', '')):
        abort(403)
    if not request.form.get('From') or not request.form.get('MessageSid'):
        abort(400)
    # Get message details from Twilio webhook
    from_number = request.form.get('From', '')
    message_body = request.form.get('Body', '')
    message_sid = request.form.get('MessageSid', '')

    if len(message_body) > 4000:
        abort(400)

    try:
        # Generate auto-reply
        workflow = run_workflow(message_body)
        reply_message = workflow['response']
        if os.getenv('REPLY_TRANSPORT') == 'capture':
            # Trial mode records generated replies for inspection and automation.
            logger.warning(json.dumps({'event':'workflow_response','message_sid':message_sid,
                                      'input':message_body,'workflow':workflow,
                                      'delivery':'captured_only'}, ensure_ascii=True))
            return '', 204

        # Some trial webhook paths reject TwiML; REST delivery is independently tracked.
        use_rest = os.getenv('REPLY_TRANSPORT', 'twiml') == 'rest'
        if use_rest:
            sender = request.form.get('To', '')
            if not sender.startswith('whatsapp:'):
                abort(400)
            delivered = send_whatsapp_message(from_number, reply_message, sender)
            if delivered is None:
                raise RuntimeError('Twilio rejected outbound reply')

        # Twilio delivers the reply contained in this TwiML response.
        resp = MessagingResponse()
        if not use_rest:
            resp.message(reply_message)
        return str(resp), 200, {'Content-Type': 'text/xml; charset=utf-8'}

    except Exception as e:
        logger.error("Webhook processing failed (%s)", type(e).__name__)
        return str(MessagingResponse()), 500


def send_whatsapp_message(phone_number: str, message: str, sender: str = None):
    """
    Send a message via Twilio WhatsApp API
    """
    try:
        # Format phone number for Twilio (add whatsapp: prefix)
        to_number = "whatsapp:" + phone_number.removeprefix("whatsapp:")
        from_number = "whatsapp:" + (sender or os.getenv("TWILIO_WHATSAPP_NUMBER", "")).removeprefix("whatsapp:")

        message = get_twilio_client().messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )

        logger.info("Outbound message sent")
        return message

    except Exception as e:
        logger.error("Outbound message failed (%s)", type(e).__name__)
        return None


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    logger.info(f"Starting WhatsApp Auto-Reply Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
