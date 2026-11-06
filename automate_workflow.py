"""Exercise the live receive-only webhook and verify generated answers in CloudWatch."""
import argparse
import html
import json
import os
from pathlib import Path
import time
import uuid
import boto3
import requests
from twilio.request_validator import RequestValidator
from conversation import run_workflow

SCENARIOS = [('Villas',['Hi','1']),('Apartments',['Hi','Apartments']),('Office Space',['Hi','3'])]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--region',default='ap-southeast-2')
    parser.add_argument('--log-group',required=True)
    parser.add_argument('--output-dir',default='outputs')
    args=parser.parse_args()
    token=os.environ['TWILIO_AUTH_TOKEN']
    # Refuse to exercise an endpoint unless its deployed Lambda is capture-only.
    cf=boto3.client('cloudformation',region_name=args.region)
    resources=cf.describe_stack_resources(StackName='property-whatsapp-bot')['StackResources']
    fn=next(x['PhysicalResourceId'] for x in resources if x['LogicalResourceId']=='PropertyBot')
    # Query only the non-secret transport field; do not print or persist environment values.
    transport=boto3.client('lambda',region_name=args.region).get_function_configuration(FunctionName=fn)['Environment']['Variables'].get('REPLY_TRANSPORT')
    if transport!='capture':
        raise RuntimeError('Live automation requires capture mode; no test messages were submitted')
    logs=boto3.client('logs',region_name=args.region)
    start=int(time.time()*1000)-1000
    cases=[]
    for title,inputs in SCENARIOS:
        turns=[]
        for message in inputs:
            sid='SMauto'+uuid.uuid4().hex
            data={'From':'whatsapp:+15555555555','To':'whatsapp:+17372508034','Body':message,'MessageSid':sid}
            signature=RequestValidator(token).compute_signature(args.url,data)
            r=requests.post(args.url,data=data,headers={'X-Twilio-Signature':signature},timeout=25)
            if r.status_code!=204:
                raise RuntimeError('Capture webhook returned HTTP '+str(r.status_code))
            turns.append({'user':message,'message_sid':sid,'expected':run_workflow(message),'http_status':r.status_code})
        cases.append({'scenario':title,'turns':turns})
    pending={turn['message_sid']:turn for case in cases for turn in case['turns']}
    deadline=time.monotonic()+90
    while pending and time.monotonic()<deadline:
        for page in logs.get_paginator('filter_log_events').paginate(logGroupName=args.log_group,startTime=start,filterPattern='"SMauto"'):
            for event in page['events']:
                raw=event['message'];begin=raw.find('{')
                if begin<0: continue
                try: record=json.loads(raw[begin:])
                except json.JSONDecodeError: continue
                sid=record.get('message_sid')
                if sid in pending:
                    turn=pending.pop(sid)
                    turn['actual']=record['workflow']
                    turn['delivery']=record['delivery']
                    turn['passed']=turn['expected']==turn['actual'] and record['delivery']=='captured_only'
        if pending: time.sleep(5)
    for turn in pending.values(): turn['passed']=False;turn['error']='CloudWatch capture not observed before timeout'
    passed=all(t.get('passed') for c in cases for t in c['turns'])
    report={'passed':passed,'mode':'capture; no WhatsApp messages sent','region':args.region,'scenarios':cases}
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'workflow-test-results.json').write_text(json.dumps(report,indent=2)+'\n')
    sections=[]
    for case in cases:
        turns=[]
        for t in case['turns']:
            response=t.get('actual',{}).get('response',t.get('error','No captured response'))
            turns.append('<div class="user"><b>User</b><p>'+html.escape(t['user'])+'</p></div><div class="bot"><b>Shraddha Properties</b><pre>'+html.escape(response)+'</pre></div>')
        sections.append('<section><h2>'+html.escape(case['scenario'])+'</h2>'+''.join(turns)+'</section>')
    body='''<!doctype html><html><head><meta charset="utf-8"><title>Shraddha Properties workflow</title><style>
    body{font:16px system-ui;background:#f4f6f8;color:#172b3a;max-width:1100px;margin:40px auto;padding:0 24px}
    h1{font-size:30px}.flow{padding:20px;background:#173b38;color:white;border-radius:12px;line-height:2}
    section{background:white;border-radius:16px;padding:24px;margin:24px 0}.user,.bot{padding:16px 20px;border-radius:12px;margin:12px 0}
    .user{background:#eef2f6;margin-left:25%}.bot{background:#e7f5ed;margin-right:8%}pre{font:inherit;white-space:pre-wrap;line-height:1.6}p{margin:8px 0}
    </style></head><body><h1>Shraddha Properties</h1><p>Automated conversation verification against the live AWS webhook in Sydney. All listings are fictional demo data.</p>
    <div class="flow">WhatsApp or signed test input → Validate signature → Generate menu or category response → Capture in CloudWatch → Verify response<br>Hi → Villas / Apartments / Office Space → Property details and price</div>'''
    body+='<p><b>'+('6 of 6 live turns verified' if passed else 'Verification incomplete')+'</b> · Capture mode · No WhatsApp messages sent</p>'+''.join(sections)+'</body></html>'
    (out/'shraddha-workflow-report.html').write_text(body)
    print('Live workflow verification:', 'PASS' if passed else 'FAIL')
    print('Verified turns:',sum(t.get('passed',False) for c in cases for t in c['turns']))
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
