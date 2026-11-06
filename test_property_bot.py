import base64
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
from xml.etree import ElementTree

from bot import app
from listings import answer_question, load_catalog
from import_listings import convert
from lambda_handler import handler
from twilio.request_validator import RequestValidator

URL = 'https://example.execute-api.us-east-1.amazonaws.com/webhook/whatsapp'


class PropertyBotTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'TWILIO_AUTH_TOKEN':'test-token', 'TWILIO_WEBHOOK_URL':URL})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = app.test_client()
        self.data = {'From':'whatsapp:+15555555555','Body':'price DEMO-001','MessageSid':'SMtest'}
        self.signature = RequestValidator('test-token').compute_signature(URL, self.data)

    def test_signed_webhook_replies_without_rest_send(self):
        with patch('bot.send_whatsapp_message') as outbound:
            response = self.client.post('/webhook/whatsapp', data=self.data, headers={'X-Twilio-Signature':self.signature})
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/xml', response.content_type)
        self.assertIn('INR 28,000/month', ElementTree.fromstring(response.data).findtext('Message'))
        outbound.assert_not_called()

    def test_unsigned_webhook_rejected(self):
        self.assertEqual(self.client.post('/webhook/whatsapp',data=self.data).status_code,403)

    def test_rest_delivery_uses_incoming_sender(self):
        self.data['To'] = 'whatsapp:+17372508034'
        signature = RequestValidator('test-token').compute_signature(URL, self.data)
        with patch.dict(os.environ, {'REPLY_TRANSPORT':'rest'}), patch('bot.send_whatsapp_message') as send:
            send.return_value = object()
            response = self.client.post('/webhook/whatsapp',data=self.data,headers={'X-Twilio-Signature':signature})
        self.assertEqual(response.status_code,200)
        self.assertEqual(send.call_args.args[2], self.data['To'])
        self.assertIn('28,000/month',send.call_args.args[1])
        self.assertIsNone(ElementTree.fromstring(response.data).find('Message'))

    def test_rest_failure_does_not_report_success(self):
        self.data['To'] = 'whatsapp:+17372508034'
        signature = RequestValidator('test-token').compute_signature(URL, self.data)
        with patch.dict(os.environ, {'REPLY_TRANSPORT':'rest'}), patch('bot.send_whatsapp_message',return_value=None):
            response = self.client.post('/webhook/whatsapp',data=self.data,headers={'X-Twilio-Signature':signature})
        self.assertEqual(response.status_code,500)

    def test_tampered_body_rejected(self):
        self.data['Body']='price DEMO-002'
        self.assertEqual(self.client.post('/webhook/whatsapp',data=self.data,headers={'X-Twilio-Signature':self.signature}).status_code,403)

    def test_missing_security_fails_closed(self):
        with patch.dict(os.environ, {'TWILIO_AUTH_TOKEN':''}):
            self.assertEqual(self.client.post('/webhook/whatsapp',data=self.data).status_code,503)

    def test_missing_property_asks_for_id(self):
        self.assertIn('include a property ID', answer_question('What is the price?'))

    def test_ambiguous_location(self):
        self.assertIn('choose one property ID', answer_question('price in Demo North District'))

    def test_missing_fact_is_explicit(self):
        self.assertIn('Not recorded', answer_question('pets DEMO-005'))

    def test_unknown_question_does_not_invent(self):
        self.assertIn("don't have a recorded answer", answer_question('Is DEMO-001 earthquake proof?'))

    def test_zero_bedrooms_preserved(self):
        self.assertIn('Bedrooms: 0', answer_question('bedrooms DEMO-003'))

    def test_demo_warning(self):
        self.assertTrue(answer_question('DEMO-001').startswith('DEMO DATA'))

    def test_legacy_reply_configuration_removed(self):
        self.assertEqual(self.client.get('/config/replies').status_code, 404)

    def test_lambda_base64_form(self):
        event={'requestContext':{'http':{'method':'POST'},'domainName':'example.execute-api.us-east-1.amazonaws.com'},
               'rawPath':'/webhook/whatsapp','rawQueryString':'',
               'headers':{'content-type':'application/x-www-form-urlencoded','x-twilio-signature':self.signature},
               'body':base64.b64encode(urlencode(self.data).encode()).decode(),'isBase64Encoded':True}
        with patch.dict(os.environ, {'TWILIO_WEBHOOK_URL':''}):
            response=handler(event,None)
        self.assertEqual(response['statusCode'],200)
        self.assertIn('28,000',response['body'])

    def test_csv_import(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'listings.json'
            convert(Path(__file__).with_name('data')/'sample-property-listings.csv',output)
            self.assertEqual(len(load_catalog(output)['listings']),6)
            self.assertEqual(load_catalog(output)['listings'][4]['pets'], '')

    def test_invalid_import_keeps_previous_file(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'listings.json'
            output.write_text('previous')
            source=Path(folder)/'bad.csv'
            source.write_text('id,title,price\nx,Test,-10\n')
            with self.assertRaises(ValueError):
                convert(source,output)
            self.assertEqual(output.read_text(),'previous')


if __name__ == '__main__':
    unittest.main()
