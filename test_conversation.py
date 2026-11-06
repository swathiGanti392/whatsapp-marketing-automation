import os
import unittest
from unittest.mock import patch
from twilio.request_validator import RequestValidator
from conversation import run_workflow, WELCOME
from bot import app


class ConversationTests(unittest.TestCase):
    def test_welcome(self):
        for message in ('Hi','hello!','MENU'):
            self.assertEqual(run_workflow(message)['response'],WELCOME)

    def test_all_categories_and_numeric_options(self):
        for option,name,category in [('1','Villas','villa'),('2','Apartments','apartment'),('3','Office Space','office')]:
            a,b=run_workflow(option),run_workflow(name)
            self.assertEqual(a,b)
            self.assertEqual(a['category'],category)
            self.assertTrue(a['listing_ids'])
            self.assertIn('Price: INR',a['response'])
            self.assertIn('DEMO DATA',a['response'])

    def test_unknown_input_shows_menu(self):
        self.assertEqual(run_workflow('banana')['stage'],'choose_property_type')

    def test_capture_never_sends(self):
        url='https://example.test/webhook/whatsapp'
        data={'From':'whatsapp:+15555555555','Body':'Hi','MessageSid':'SMcapture'}
        signature=RequestValidator('test').compute_signature(url,data)
        with patch.dict(os.environ,{'TWILIO_AUTH_TOKEN':'test','TWILIO_WEBHOOK_URL':url,'REPLY_TRANSPORT':'capture'}), patch('bot.send_whatsapp_message') as send, self.assertLogs('bot',level='WARNING') as logs:
            result=app.test_client().post('/webhook/whatsapp',data=data,headers={'X-Twilio-Signature':signature})
        self.assertEqual(result.status_code,204)
        send.assert_not_called()
        self.assertIn('Shraddha Properties',logs.output[0])

    def test_web_tester_runs_shared_engine_without_sending(self):
        with patch('bot.send_whatsapp_message') as send:
            r=app.test_client().post('/test/workflow',json={'message':'Villas'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['category'],'villa')
        self.assertEqual(r.json['mode'],'capture')
        send.assert_not_called()

    def test_web_tester_validates_input(self):
        for payload in ({}, {'message':2}, {'message':' '*5}, {'message':'x'*1001}):
            self.assertEqual(app.test_client().post('/test/workflow',json=payload).status_code,400)

    def test_browser_origin_restricted(self):
        with patch.dict(os.environ, {'TEST_SITE_ORIGIN':'https://tester.example'}):
            client=app.test_client()
            good=client.options('/test/workflow',headers={'Origin':'https://tester.example'})
            bad=client.options('/test/workflow',headers={'Origin':'https://other.example'})
        self.assertEqual(good.headers['Access-Control-Allow-Origin'],'https://tester.example')
        self.assertNotIn('Access-Control-Allow-Origin',bad.headers)

    def test_rich_cards_use_recorded_facts(self):
        result=run_workflow('Villas')
        self.assertEqual(result['presentation'],'property_collection')
        card=result['cards'][0]
        self.assertEqual(card['id'],'DEMO-004')
        self.assertEqual(card['area'],'2,800 sq ft')
        self.assertTrue(card['demo'])
        self.assertEqual(len(card['actions']),4)

    def test_all_property_followups(self):
        for command in ('brochure','price','location','visit','details'):
            result=run_workflow(command+' DEMO-004')
            self.assertEqual(result['stage'],'property_followup')
            self.assertEqual(result['cards'][0]['view'],command)
        self.assertIn('not been uploaded',run_workflow('brochure DEMO-004')['response'])
        self.assertIn('not a confirmed booking',run_workflow('visit DEMO-004')['response'])


if __name__=='__main__':
    unittest.main()
