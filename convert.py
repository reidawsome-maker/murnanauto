import pandas as pd
import json, os, re

df = pd.read_csv('CF-Catalog-Filtered-6-8-10AN-EFI-Tools-Hose.csv')
os.makedirs('content/products', exist_ok=True)

subcat_mapping = {
    'Adapters and Unions': ('ANAdapters', 'AN Adapters & Specialty'),
    'ORB Adapters': ('ANAdapters', 'ORB Adapters'),
    'NPT Adapters': ('ANAdapters', 'NPT Adapters'),
    'Hardline Adapters': ('ANAdapters', 'Hardline Adapters'),
    'Metric adapters': ('ANAdapters', 'Metric Adapters'),
    'SAE Fittings': ('ANAdapters', 'SAE Fittings'),
    'Brake Fittings': ('ANAdapters', 'Brake Fittings'),
    'EFI/LS-Connector/Quick-Connector': ('ANAdapters', 'EFI Quick Connectors'),
    'Specialty Fitting & PCV Delete': ('ANAdapters', 'Specialty Fittings'),
    'Weld-On Bungs': ('ANAdapters', 'Weld-On Bungs'),
    'Barb Fittings': ('ANAdapters', 'Barb Fittings'),
    'Caps, Plugs, and Blockoffs': ('ANAdapters', 'Plugs & Blockoffs'),
    
    'AN Fittings': ('ANFittings', 'AN Hose Ends & Fittings'),
    'Hose Fittings': ('ANFittings', 'AN Hose Ends & Fittings'),
    'PTFE Hose Fittings': ('ANFittings', 'PTFE Hose Ends'),
    'Push-Loc Hose Ends': ('ANFittings', 'Push-Loc Hose Ends'),
    
    'PTFE Hose': ('PTFEHose', 'PTFE Hose & Lines'),
    'Nylon Hose': ('NylonHose', 'Nylon Braided Hose'),
    'Hose & Line': ('NylonHose', 'Nylon Braided Hose'),
    
    'Hose Clamps & Separators': ('HoseClamps', 'Hose Separators & Clamps'),
    'Hose Separators': ('HoseClamps', 'Hose Separators & Clamps'),
    
    'Fitting Assembly Tools': ('Tools', 'Hand Tools & Specialty'),
    'Fitting Sockets': ('Tools', 'Hand Tools & Specialty'),
    'Tools': ('Tools', 'Hand Tools & Specialty'),
    
    'Fuel Filters': ('FuelFilters', 'Fuel Filters'),
    'Oil Cooler Parts': ('OilCoolers', 'Oil Coolers'),
    'Radiators': ('Radiators', 'Radiators')
}

def extract_an_size_label(title):
    match = re.search(r'(-?\d+)\s*AN', str(title), re.IGNORECASE)
    if match:
        val = int(match.group(1).replace('-', ''))
        return f"{val}AN"
    return "Universal"

def get_an_size_num(title):
    match = re.search(r'(-?\d+)\s*AN', str(title), re.IGNORECASE)
    if match:
        return int(match.group(1).replace('-', ''))
    return 99

def is_keep_item(row):
    title = str(row['Title']).lower()
    cat = str(row['Category']).lower()

    if 'finisher' in title or 'worm' in title or 'hex / worm' in cat:
        return False
    if 'stainless steel' in title and ('hose' in title or 'line' in title):
        return False
    if 'per foot' in title or 'by the foot' in title or '1 foot' in title:
        return False

    if any(k in cat for k in ['tool', 'socket', 'filter', 'cooler', 'radiator']):
        return True

    size = get_an_size_num(row['Title'])
    if size in [6, 8, 10, 99]:
        return True

    return False

def determine_category(title, raw_cat):
    t = str(title).lower()
    c = str(raw_cat).replace('&amp;', '&').strip()

    # 1. Protect Forced Induction items
    if 'turbo kit' in t or 'twin turbo' in t or 'single turbo' in t:
        return ('Kits', 'Complete Turbo Kits')
    if 'turbocharger' in t or 'turbo ' in t or t.startswith('turbo'):
        return ('Turbos', 'Turbochargers')

    # 2. Strict V-Band Hardware Matching
    if 'v-band' in t or 'v-band' in c.lower():
        if 'clamp' in t or 'flange' in t or 'assembly' in t or 'set' in t:
            return ('V-Band', 'V-Bands & Clamps')

    # 3. Strict Cooling Distinction
    if 'oil cooler' in t or 'sandwich plate' in t or 'oil cooler parts' in c.lower():
        return ('OilCoolers', 'Oil Coolers')
    if 'radiator' in t:
        return ('Radiators', 'Radiators')

    # 4. Hose distinctions
    if 'ptfe' in t and 'fitting' not in t and 'end' not in t:
        return ('PTFEHose', 'PTFE Hose & Lines')
    if 'nylon' in t or 'braided hose' in t:
        return ('NylonHose', 'Nylon Braided Hose')

    return subcat_mapping.get(c, ('ANFittings', 'AN Hose Ends & Fittings'))

df_filtered = df[df.apply(is_keep_item, axis=1)].copy()
grouped = df_filtered.groupby('Title', sort=False)

all_products = []

for title, group in grouped:
    slug = re.sub(r'[^a-z0-9]+', '-', str(title).lower()).strip('-')
    first = group.iloc[0]
    title_str = str(title)
    
    category, subcategory = determine_category(title_str, first['Category'])
    an_size_label = extract_an_size_label(title_str)
    
    variants = []
    for _, row in group.iterrows():
        color_name = re.sub(r'\s*\[\+\$[0-9\.]+\]', '', str(row['Variation name (color)'])).strip()
        img_link = str(row['Variation Image Link']).strip()
        sku_val = str(row['Variation SKU']).strip()
        price_val = float(row['Price'])
        
        variants.append({
            'name': color_name,
            'sku': sku_val,
            'price': price_val,
            'image': img_link,
            'stock': 10
        })
        
    product = {
        'id': slug,
        'name': title_str,
        'title': title_str,
        'sku': str(first['Variation SKU']).strip(),
        'category': category,
        'subcategory': subcategory,
        'anSize': an_size_label,
        'price': float(group['Price'].min()),
        'description': str(first['Description']).split('\n')[0].strip(),
        'image': str(first['Variation Image Link']).strip(),
        'variants': variants
    }
    
    with open(f'content/products/{slug}.json', 'w') as f:
        json.dump(product, f, indent=2)
        
    all_products.append(product)

with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Cleaned catalog: generated {len(all_products)} products.")
