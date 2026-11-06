"""Structured property answers. No invented facts or external model calls."""
import json
import math
import os
import re
from datetime import date
from pathlib import Path

DEFAULT_PATH = Path(__file__).with_name('data') / 'listings.json'
FIELDS = {
    'price': ('price', 'cost', 'rent', 'budget'),
    'area_sqft': ('area', 'size', 'sqft', 'square'),
    'bedrooms': ('bedroom', 'bedrooms', 'bhk'),
    'bathrooms': ('bathroom', 'bathrooms'),
    'furnishing': ('furnished', 'furnishing', 'unfurnished'),
    'parking': ('parking', 'garage'),
    'pets': ('pet', 'pets', 'dog', 'cat'),
    'amenities': ('amenities', 'facilities', 'gym', 'pool'),
    'availability': ('available', 'availability', 'possession', 'vacant'),
    'location': ('where', 'location', 'address'),
    'visit_notes': ('visit', 'viewing', 'tour', 'appointment'),
}


def load_catalog(path=None):
    catalog = json.loads(Path(path or os.getenv('LISTINGS_FILE', DEFAULT_PATH)).read_text())
    if not isinstance(catalog.get('demo'), bool) or not isinstance(catalog.get('listings'), list):
        raise ValueError('Catalog requires demo boolean and listings array')
    ids = set()
    for item in catalog['listings']:
        for key in ('id', 'title', 'location', 'currency', 'transaction', 'updated_on'):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError('Every listing requires ' + key)
        if item['id'].casefold() in ids:
            raise ValueError('Duplicate listing ID')
        ids.add(item['id'].casefold())
        if not re.fullmatch(r'[A-Za-z0-9-]+', item['id']):
            raise ValueError('IDs may contain only letters, digits and hyphens')
        if item['transaction'] not in ('rent', 'sale'):
            raise ValueError('transaction must be rent or sale')
        date.fromisoformat(item['updated_on'])
        for key in ('price', 'area_sqft', 'bedrooms', 'bathrooms'):
            value = item.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                raise ValueError('Invalid numeric field: ' + key)
    return catalog


def display(item, field):
    value = item.get(field)
    if value is None or value == '':
        return 'Not recorded; please confirm with the agent.'
    if field == 'price':
        period = '/month' if item['transaction'] == 'rent' else ' (sale)'
        return f"{item['currency']} {value:,.0f}{period}"
    if field == 'area_sqft':
        return f'{value:,.0f} sq ft'
    return str(value)


def answer_question(message, catalog=None):
    catalog = catalog if catalog is not None else load_catalog()
    prefix = 'DEMO DATA - fictional properties.\n' if catalog['demo'] else ''
    items = catalog['listings']
    if not items:
        return prefix + 'No property listings are loaded yet. Please contact the agent.'
    text = message.casefold().strip()
    tokens = set(re.findall(r'[\w-]+', text))
    ids = [x for x in items if x['id'].casefold() in tokens]
    if ids:
        matches = ids
    else:
        matches = [x for x in items if any(
            phrase.casefold() in text for phrase in (x['title'], x['location'])
        )]
    if len(matches) != 1:
        selected = matches or items
        heading = 'Please choose one property ID:' if matches else 'Please include a property ID in your question:'
        choices = '\n'.join(f"{x['id']}: {x['title']} - {x['location']}" for x in selected[:8])
        extra = '\nMore listings exist; ask the agent for the full catalog.' if len(selected) > 8 else ''
        return prefix + heading + '\n' + choices + extra + '\nExample: What is the price of ' + selected[0]['id'] + '?'
    item = matches[0]
    fields = [key for key, words in FIELDS.items() if tokens.intersection(words)]
    details = bool(tokens.intersection({'details', 'summary', 'about', 'tell'})) or text == item['id'].casefold()
    if not fields and not details:
        return prefix + f"{item['id']}: I don't have a recorded answer to that question. Please ask the agent, or ask about price, size, bedrooms, furnishing, parking, pets, amenities, availability or visits."
    fields = fields or ['location', 'price', 'bedrooms', 'area_sqft', 'availability']
    lines = [prefix + f"{item['id']}: {item['title']}"]
    lines += [f"{key.replace('_', ' ').capitalize()}: {display(item, key)}" for key in fields]
    lines.append('Listing updated: ' + item['updated_on'] + '. Confirm current details with the agent.')
    return '\n'.join(lines)[:1500]
