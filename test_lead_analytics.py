from datetime import datetime,timezone,timedelta
import unittest
from unittest.mock import patch,MagicMock
from lead_analytics import prepare_submission,save_submission,summarize
from bot import app


class LeadAnalyticsTests(unittest.TestCase):
    def payload(self,kind='lead'):
        return {'submission_id':'4f9b6970-97ce-4dfd-9601-f21ac1b0071b','kind':kind,'property_id':'DEMO-004',
                'name':'Automation Tester','contact':'tester@example.com','consent':True,
                'preferred_date':(datetime.now(timezone.utc).date()+timedelta(days=2)).isoformat()}

    def test_valid_lead_and_visit(self):
        for kind in ['lead','visit']:
            r=prepare_submission(self.payload(kind));self.assertEqual(r['kind'],kind)
            self.assertEqual(r['source'],'web_test');self.assertNotEqual(r['contact_hash'],r['contact'])

    def test_consent_and_contact_validation(self):
        for changes in [{'consent':False},{'contact':'invalid'},{'property_id':'missing'},{'kind':'unknown'}]:
            with self.assertRaises(ValueError): prepare_submission({**self.payload(),**changes})

    def test_visit_cannot_be_in_past(self):
        with self.assertRaises(ValueError): prepare_submission({**self.payload('visit'),'preferred_date':'2020-01-01'})

    def test_aggregate_excludes_contacts_and_counts_kinds(self):
        records=[prepare_submission(self.payload()),prepare_submission(self.payload('visit'))]
        result=summarize(records,7)
        self.assertEqual(result['lead_submissions'],1);self.assertEqual(result['visit_requests'],1)
        self.assertEqual(result['unique_contacts'],1)
        self.assertNotIn('tester@example.com',str(result));self.assertNotIn('Automation Tester',str(result))

    def test_duplicate_returns_existing_result(self):
        class Duplicate(Exception): pass
        store=MagicMock();store.meta.client.exceptions.ConditionalCheckFailedException=Duplicate
        store.put_item.side_effect=Duplicate();store.get_item.return_value={'Item':prepare_submission(self.payload())}
        with patch('lead_analytics.table',return_value=store): result=save_submission(self.payload())
        self.assertTrue(result['duplicate'])

    def test_api_errors_do_not_report_saved(self):
        with patch('bot.save_submission',side_effect=RuntimeError('storage unavailable')):
            result=app.test_client().post('/test/leads',json=self.payload())
        self.assertEqual(result.status_code,503)
        self.assertNotIn('storage unavailable',result.get_data(as_text=True))

    def test_summary_window_restricted(self):
        self.assertEqual(app.test_client().get('/test/analytics?days=999').status_code,400)


if __name__=='__main__': unittest.main()
