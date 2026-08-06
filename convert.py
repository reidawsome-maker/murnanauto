import pandas as pd
import json, os, re

# Read CSV
df = pd.read_csv('CF-Catalog-Filtered-6-8-10AN-EFI-Tools-Hose.csv')
os.makedirs('content/products', exist_ok=True)

# Comprehensive Category Mapping
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

# Helper to extract AN size for clean sorting/filtering
def get_an_size(title):
    match = re.search(r'(-?\d+)\s*AN', str(title), re.IGNORECASE)
    if match:
        val = int(match.group(1).replace('-', ''))
        return val
    return 99 # Tools and universal items

# Filter out non-target AN sizes (-4, -12, -16) unless it's a Tool or Universal item
def is_keep_item(row):
    cat = str(row['Category'])
    if 'Tool' in cat or 'Socket' in cat or 'Filter' in cat or 'Cooler' in cat:
        return True
    size = get_an_size(row['Title'])
    if size in [6, 8, 10, 99]:
        return True
    return False

df_filtered = df[df.apply(is_keep_item, axis=1)].copy()

# Add sorting helper columns
df_filtered['an_order'] = df_filtered['Title'].apply(get_an_size)
df_filtered['sort_title'] = df_filtered['Title'].str.lower()
df_filtered = df_filtered.sort_values(by=['an_order', 'sort_title'])

# Group by Title
grouped = df_filtered.groupby('Title', sort=False)

count = 0
for title, group in grouped:
    slug = re.sub(r'[^a-z0-9]+', '-', str(title).lower()).strip('-')
    first = group.iloc[0]
    
    cat_raw = str(first['Category']).replace('&amp;', '&')
    category = cat_mapping.get(cat_raw, 'ANFittings')
    
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
            'image': img_link,  # Crucial for dynamic image switching on color selection!
            'stock': 10
        })
        
    product = {
        'id': slug,
        'name': str(title),
        'sku': str(first['Variation SKU']).strip(),  # Main SKU
        'category': category,
        'price': float(group['Price'].min()),
        'description': str(first['Description']).split('\n')[0].strip(),
        'image': str(first['Variation Image Link']).strip(), # Default image
        'variants': variants
    }
    
    with open(f'content/products/{slug}.json', 'w') as f:
        json.dump(product, f, indent=2)
    count += 1

print(f"Successfully created {count} clean, organized product JSON files!")
