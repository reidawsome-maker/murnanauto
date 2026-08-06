import pandas as pd
import json, os, re

df = pd.read_csv('CF-Catalog-Filtered-6-8-10AN-EFI-Tools-Hose.csv')
os.makedirs('content/products', exist_ok=True)

# Main & Subcategory Mapping
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
    'Oil Cooler Parts': ('Radiators', 'Oil Coolers')
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

    # 1. REMOVE: Worm clamp finishers
    if 'finisher' in title or 'worm' in title or 'hex / worm' in cat:
        return False
        
    # 2. REMOVE: Stainless Steel Exterior Hose
    if 'stainless steel' in title and ('hose' in title or 'line' in title):
        return False

    # 3. REMOVE: By the foot sales
    if 'per foot' in title or 'by the foot' in title or '1 foot' in title:
        return False

    # Keep tools/filters/coolers
    if any(k in cat for k in ['tool', 'socket', 'filter', 'cooler']):
        return True

    # Keep target sizes (-6, -8, -10)
    size = get_an_size_num(row['Title'])
    if size in [6, 8, 10, 99]:
        return True

    return False

df_filtered = df[df.apply(is_keep_item, axis=1)].copy()
grouped = df_filtered.groupby('Title', sort=False)

all_products = []

for title, group in grouped:
    slug = re.sub(r'[^a-z0-9]+', '-', str(title).lower()).strip('-')
    first = group.iloc[0]
    
    title_str = str(title)
    cat_raw = str(first['Category']).replace('&amp;', '&')
    
    # Precise PTFE vs Nylon re-sorting based on title text
    if 'ptfe' in title_str.lower() and 'fitting' not in title_str.lower() and 'end' not in title_str.lower():
        category, subcategory = ('PTFEHose', 'PTFE Hose & Lines')
    elif 'nylon' in title_str.lower() or 'braided hose' in title_str.lower():
        category, subcategory = ('NylonHose', 'Nylon Braided Hose')
    else:
        category, subcategory = subcat_mapping.get(cat_raw, ('ANFittings', 'AN Hose Ends & Fittings'))
        
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

# Save master compiled inventory.json
with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Successfully cleaned catalog: generated {len(all_products)} products.")
