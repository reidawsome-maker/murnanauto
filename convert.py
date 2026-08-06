import pandas as pd
import json, os, re

# Read CSV
df = pd.read_csv('CF-Catalog-Filtered-6-8-10AN-EFI-Tools-Hose.csv')
os.makedirs('content/products', exist_ok=True)

cat_mapping = {
    'Adapters and Unions': 'ANAdapters',
    'ORB Adapters': 'ANAdapters',
    'NPT Adapters': 'ANAdapters',
    'Hardline Adapters': 'ANAdapters',
    'Metric adapters': 'ANAdapters',
    'SAE Fittings': 'ANAdapters',
    'Brake Fittings': 'ANAdapters',
    'EFI/LS-Connector/Quick-Connector': 'ANAdapters',
    'Specialty Fitting & PCV Delete': 'ANAdapters',
    'Weld-On Bungs': 'ANAdapters',
    'Barb Fittings': 'ANAdapters',
    'Caps, Plugs, and Blockoffs': 'ANAdapters',
    
    'AN Fittings': 'ANFittings',
    'Hose Fittings': 'ANFittings',
    'PTFE Hose Fittings': 'ANFittings',
    'Push-Loc Hose Ends': 'ANFittings',
    
    'PTFE Hose': 'PTFEHose',
    'Nylon Hose': 'NylonHose',
    'Hose & Line': 'NylonHose',
    
    'Hose Clamps & Separators': 'HoseClamps',
    'Hose Separators': 'HoseClamps',
    'Hex / Worm-Clamp Hose Finishers Ends': 'HoseClamps',
    
    'Fitting Assembly Tools': 'Tools',
    'Fitting Sockets': 'Tools',
    'Tools': 'Tools',
    
    'Fuel Filters': 'FuelFilters',
    'Oil Cooler Parts': 'Radiators'
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
    cat = str(row['Category'])
    if any(k in cat for k in ['Tool', 'Socket', 'Filter', 'Cooler']):
        return True
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
    
    cat_raw = str(first['Category']).replace('&amp;', '&')
    category = cat_mapping.get(cat_raw, 'ANFittings')
    an_size_label = extract_an_size_label(title)
    
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
        'name': str(title),
        'title': str(title),
        'sku': str(first['Variation SKU']).strip(),
        'category': category,
        'anSize': an_size_label,
        'price': float(group['Price'].min()),
        'description': str(first['Description']).split('\n')[0].strip(),
        'image': str(first['Variation Image Link']).strip(),
        'variants': variants
    }
    
    # Save individual product file
    with open(f'content/products/{slug}.json', 'w') as f:
        json.dump(product, f, indent=2)
        
    all_products.append(product)

# ALSO save master compiled inventory.json
with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Successfully compiled {len(all_products)} products into inventory.json and content/products/")
