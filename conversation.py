"""Shraddha Properties menu workflow shared by WhatsApp and automation."""
import re
from listings import load_catalog, display, answer_question

WELCOME = ('Hi, welcome to Shraddha Properties!\n'
           'Please let me know what you are looking for:\n'
           '1. Villas\n2. Apartments\n3. Office Space\n'
           'Reply with a number or the property type.')
OPTIONS = {'1': 'villa', '2': 'apartment', '3': 'office'}
ALIASES = {'villa':'villa','villas':'villa','apartment':'apartment',
           'apartments':'apartment','office':'office','office space':'office',
           'office spaces':'office'}


def property_card(item, demo, view='overview'):
    return {'id':item['id'],'title':item['title'],'category':item.get('property_type','apartment'),
            'location':item['location'],'price':display(item,'price'),'area':display(item,'area_sqft'),
            'bedrooms':item.get('bedrooms'),'bathrooms':item.get('bathrooms'),
            'furnishing':display(item,'furnishing'),'availability':display(item,'availability'),
            'amenities':[v.strip() for v in item.get('amenities','').split(';') if v.strip()],
            'parking':display(item,'parking'),'visit_notes':display(item,'visit_notes'),
            'updated_on':item['updated_on'],'demo':demo,'view':view,
            'actions':[{'label':'View brochure','message':'brochure '+item['id']},
                       {'label':'Price details','message':'price '+item['id']},
                       {'label':'Location & amenities','message':'location '+item['id']},
                       {'label':'Plan a site visit','message':'visit '+item['id']}]}


def run_workflow(message, catalog=None):
    catalog = catalog if catalog is not None else load_catalog()
    text = re.sub(r'[^\w\s-]', '', message.casefold()).strip()
    category = OPTIONS.get(text) or ALIASES.get(text)
    if text in ('hi','hello','hey','start','menu','restart',''):
        return {'stage':'choose_property_type','response':WELCOME,'options':['Villas','Apartments','Office Space'],
                'presentation':'welcome','intro':'Your next space starts with a conversation.',
                'actions':[{'label':'Villas','message':'1'},{'label':'Apartments','message':'2'},{'label':'Office Space','message':'3'}]}
    if category:
        matches = [p for p in catalog['listings'] if p.get('property_type') == category]
        label = {'villa':'Villas','apartment':'Apartments','office':'Office Space'}[category]
        lines = ['DEMO DATA - fictional properties.'] if catalog['demo'] else []
        lines.append('Here are our ' + label + ':')
        for p in matches[:5]:
            beds = f"{p['bedrooms']:g} bedrooms, " if p.get('bedrooms') is not None else ''
            lines.extend([f"\n{p['id']}: {p['title']}",p['location'],
                          beds + display(p,'area_sqft'),
                          'Price: ' + display(p,'price'),
                          'Availability: ' + display(p,'availability')])
        if not matches:
            lines.append('No listings are recorded in this category yet.')
        lines.append('\nInclude a property ID to ask for more details, or reply MENU to choose again.')
        return {'stage':'show_properties','category':category,'listing_ids':[p['id'] for p in matches[:5]],
                'response':'\n'.join(lines),'presentation':'property_collection',
                'intro':'Thank you for your interest! Explore our '+label.lower()+'.',
                'cards':[property_card(p,catalog['demo']) for p in matches[:5]]}
    command = re.fullmatch(r'(brochure|price|location|visit|details)\s+([a-z]+-\d+)',text)
    if command:
        action,listing_id=command.groups()
        item=next((p for p in catalog['listings'] if p['id'].casefold()==listing_id),None)
        if item:
            card=property_card(item,catalog['demo'],action)
            if action=='brochure':
                response=('Digital property overview for '+item['title']+'.\n'
                          'This preview is generated from recorded listing facts; an original PDF brochure has not been uploaded.')
            elif action=='visit':
                response=('We would love to help you explore '+item['title']+'.\n'
                          + display(item,'visit_notes')+'\nThis is a visit-planning preview, not a confirmed booking.')
            else:
                response=answer_question(('details' if action=='details' else action)+' '+item['id'],catalog)
            return {'stage':'property_followup','category':item.get('property_type'),
                    'response':response,'presentation':'property_detail','cards':[card],
                    'intro':{'brochure':'Your digital property brochure','price':'Let’s explore the price',
                             'location':'A closer look at the neighbourhood','visit':'Let’s plan your visit',
                             'details':'Here’s a closer look'}[action]}
    if re.search(r'\b[A-Za-z]+-\d+\b', message):
        return {'stage':'property_question','response':answer_question(message,catalog)}
    return {'stage':'choose_property_type','response':'Please select Villas, Apartments or Office Space.\n\n'+WELCOME,
            'options':['Villas','Apartments','Office Space']}
