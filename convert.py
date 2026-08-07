import pandas as pd
import json
import os
import re

# 1. Read the ColorFittings CSV
df = pd.read_csv('CF-Catalog-Filtered-6-8-10AN-EFI-Tools-Hose.csv')
os.makedirs('content/products', exist_ok=True)

# NOTE: We are NO LONGER deleting files in the products directory. 
# This keeps your existing Turbos, Mufflers, and APG inventory safe during the build.

def safe_float(val):
    try:
        cleaned = re.sub(r'[^0-9.]', '', str(val))
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0

def clean_text(raw_desc):
    raw_desc = str(raw_desc)
    # Catch corrupted python strings
    if "import pandas" in raw_desc or "def build" in raw_desc:
        return "Precision CNC-machined component engineered for demanding automotive fluid systems."
    
    # Scrub vendor fluff
    raw_desc = re.sub(r'Founded in 2008, ColorFittings.*?\.\s*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)
    raw_desc = re.sub(r'Want to learn more.*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove first-person framing
    raw_desc = re.sub(r'\bwe\b', 'Color-Fittings', raw_desc, flags=re.IGNORECASE)
    raw_desc = re.sub(r'\bour\b', 'the', raw_desc, flags=re.IGNORECASE)
    raw_desc = re.sub(r'\bus\b', 'the manufacturer', raw_desc, flags=re.IGNORECASE)

    return raw_desc.replace('\\n', '<br><br>').replace('\n', '<br><br>')

# Only exclude these exact bad listings
EXCLUDES = [
    "cummins turbo drain tube adapter", 
    "3/8\" ptc air fitting to 6 an adapter", 
    "3/8\" ptc air fitting to -6 an adapter"
]

grouped = df.groupby('Title', sort=False)

# 2. Update ONLY the ColorFittings JSON files
for title, group in grouped:
    title_str = str(title).strip()
    if any(ex in title_str.lower() for ex in EXCLUDES):
        continue
        
    slug = re.sub(r'[^a-z0-9]+', '-', title_str.lower()).strip('-')
    first = group.iloc[0]
    
    variants = []
    prices = []
    for _, row in group.iterrows():
        prices.append(safe_float(row.get('Price', 0)))
        variants.append({
            'name': str(row.get('Variation name (color)', 'Standard')).replace('[+$0.00]', '').strip(),
            'sku': str(row.get('Variation SKU', '')).strip(),
            'price': safe_float(row.get('Price', 0)),
            'image': str(row.get('Variation Image Link', '')).strip(),
            'stock': 10
        })
        
    product = {
        'id': slug,
        'name': title_str,
        'title': title_str,
        'sku': str(first.get('Variation SKU', '')).strip(),
        'category': str(first.get('Category', 'AN Fittings')),
        'price': min(prices) if prices else 0.0,
        'description': clean_text(first.get('Description', '')),
        'image': str(first.get('Variation Image Link', '')).strip(),
        'variants': variants
    }
    
    with open(f'content/products/{slug}.json', 'w') as f:
        json.dump(product, f, indent=2)

# 3. Rebuild the master inventory.json from EVERY file in the products folder
# This ensures turbos, mufflers, and all other manual/static parts are included in the storefront array.
all_products = []
for filename in os.listdir('content/products'):
    if filename.endswith('.json'):
        filepath = os.path.join('content/products', filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                all_products.append(data)
        except Exception as e:
            print(f"Skipping {filename}: {e}")

with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Success! Master inventory rebuilt with {len(all_products)} total products.")
