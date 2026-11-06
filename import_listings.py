"""Convert an Excel/Sheets CSV export to a validated, atomically replaced catalog."""
import argparse
import csv
import json
import os
from pathlib import Path
import tempfile
from listings import load_catalog


def convert(source, destination, demo=True):
    with open(source, encoding='utf-8-sig', newline='') as stream:
        records = list(csv.DictReader(stream))
    if not records:
        raise ValueError('CSV must contain at least one listing')
    for item in records:
        for key in item:
            item[key] = item[key].strip() if isinstance(item[key], str) else item[key]
        for key in ('price', 'area_sqft', 'bedrooms', 'bathrooms'):
            value = item.get(key, '')
            item[key] = float(value) if value else None
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False, encoding='utf-8') as stream:
            temp_path = Path(stream.name)
            json.dump({'demo': demo, 'listings': records}, stream, indent=2, allow_nan=False)
        load_catalog(temp_path)
        os.replace(temp_path, target)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file')
    parser.add_argument('--output', default='data/listings.json')
    parser.add_argument('--real-data', action='store_true', help='Remove DEMO warning only after replacing every sample row')
    args = parser.parse_args()
    convert(args.csv_file, args.output, demo=not args.real_data)
    print('Validated listing catalog saved.')


if __name__ == '__main__':
    main()
