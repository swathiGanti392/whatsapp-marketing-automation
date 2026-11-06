"""Persist test submissions; return aggregate analytics without contact details."""
from collections import Counter
from datetime import datetime, timedelta, timezone, date
from functools import lru_cache
import hashlib
import os
import re
import time
import uuid
import boto3
from botocore.config import Config
from listings import load_catalog


@lru_cache(maxsize=1)
def table():
    name=os.environ.get('LEADS_TABLE')
    if not name: raise RuntimeError('Lead storage is not configured')
    return boto3.resource('dynamodb',region_name=os.getenv('AWS_REGION','ap-southeast-2'),
                          config=Config(connect_timeout=2,read_timeout=3,retries={'total_max_attempts':2})).Table(name)


def prepare_submission(payload):
    if not isinstance(payload,dict): raise ValueError('Provide a submission object.')
    try: identifier=str(uuid.UUID(payload.get('submission_id','')))
    except (ValueError,TypeError,AttributeError): raise ValueError('A valid submission ID is required.')
    kind=payload.get('kind')
    if kind not in ('lead','visit'): raise ValueError('Choose a lead or visit request.')
    property_id=payload.get('property_id')
    item=next((x for x in load_catalog()['listings'] if x['id']==property_id),None)
    if not item: raise ValueError('Choose an existing property.')
    name=str(payload.get('name','')).strip()
    contact=str(payload.get('contact','')).strip()
    if not 2<=len(name)<=80: raise ValueError('Enter your name (2–80 characters).')
    email=bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',contact))
    phone=bool(re.fullmatch(r'\+?[0-9 ()-]{8,24}',contact)) and len(re.sub(r'\D','',contact))>=8
    if len(contact)>120 or not (email or phone): raise ValueError('Enter a valid email address or phone number.')
    if payload.get('consent') is not True: raise ValueError('Consent is required to store contact details.')
    preferred=payload.get('preferred_date','')
    now=datetime.now(timezone.utc)
    if kind=='visit':
        try: selected=date.fromisoformat(preferred)
        except (ValueError,TypeError): raise ValueError('Choose a valid visit date.')
        if selected<now.date() or selected>now.date()+timedelta(days=365):
            raise ValueError('Choose a visit date within the next year.')
    else: preferred=''
    normalized=contact.casefold() if email else re.sub(r'\D','',contact)
    return {'id':identifier,'kind':kind,'property_id':property_id,'category':item.get('property_type','unknown'),
            'name':name,'contact':contact,'contact_hash':hashlib.sha256(normalized.encode()).hexdigest(),
            'preferred_date':preferred,'status':'new' if kind=='lead' else 'pending_confirmation',
            'source':'web_test','created_at':now.isoformat(),'day':now.date().isoformat(),
            'expires_at':int(time.time())+90*86400,'consent':True}


def save_submission(payload):
    record=prepare_submission(payload);store=table()
    try:
        store.put_item(Item=record,ConditionExpression='attribute_not_exists(id)')
        duplicate=False
    except store.meta.client.exceptions.ConditionalCheckFailedException:
        existing=store.get_item(Key={'id':record['id']},ConsistentRead=True).get('Item',{})
        if any(existing.get(k)!=record[k] for k in ('kind','property_id','contact_hash','preferred_date')):
            raise ValueError('Submission ID was already used. Start a new request.')
        duplicate=True
    return {'submission_id':record['id'],'kind':record['kind'],'status':record['status'],
            'source':'web_test','duplicate':duplicate,'delivery':'captured_only'}


def summarize(records,days):
    today=datetime.now(timezone.utc).date()
    dates=[(today-timedelta(days=n)).isoformat() for n in reversed(range(days))]
    records=[r for r in records if r.get('day') in dates and r.get('source')=='web_test' and int(r.get('expires_at',0))>time.time()]
    kinds=Counter(r['kind'] for r in records)
    daily=[{'day':d,'leads':sum(r['kind']=='lead' and r['day']==d for r in records),
            'visits':sum(r['kind']=='visit' and r['day']==d for r in records)} for d in dates]
    props=Counter(r['property_id'] for r in records)
    return {'days':days,'timezone':'UTC','source':'web_test','lead_submissions':kinds['lead'],
            'visit_requests':kinds['visit'],'unique_contacts':len({r['contact_hash'] for r in records}),
            'pending_visits':sum(r['kind']=='visit' and r['status']=='pending_confirmation' for r in records),
            'by_property':[{'property_id':p,'submissions':n} for p,n in props.most_common()],
            'daily':daily,'generated_at':datetime.now(timezone.utc).isoformat(),
            'note':'Test submissions only. No agent notification or confirmed booking. Contact details are excluded.'}


def analytics(days=7):
    store=table();records=[]
    client=store.meta.client
    today=datetime.now(timezone.utc).date()
    for n in range(days):
        day=(today-timedelta(days=n)).isoformat()
        for page in client.get_paginator('query').paginate(
                TableName=store.name,IndexName='ByDay',KeyConditionExpression='#d = :d',
                ExpressionAttributeNames={'#d':'day'},ExpressionAttributeValues={':d':day}):
            records.extend(page.get('Items',[]))
    return summarize(records,days)
