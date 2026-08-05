import pandas as pd
import json, os, re

# Read CSV from repo root
df = pd.read_csv('CF-Catalog-Filtered-6-8-10AN-EFI-Tools-Hose.csv')
os.makedirs('content/products', exist_ok=True)

cat_mapping = {
    'Adapters and Unions': 'ANAdapters',
    'AN Fittings': 'ANFittings',
    'PTFE Hose': 'PTFEHose',
    'Nylon Hose': 'NylonHose',
    'Hose Clamps & Separators': 'HoseClamps',
    'ORB Adapters': 'ANAdapters',
    'NPT Adapters': 'ANAdapters',
    'Tools': 'Tools',
    'Fuel Filters': 'FuelFilters'
}

for title, group in df.groupby('Title'):
    slug = re.sub(r'[^a-z0-9]+', '-', str(title).lower()).strip('-')
    first = group.iloc[0]
    
    variants = []
    for _, row in group.iterrows():
        color = re.sub(r'\s*\[\+\$[0-9\.]+\]', '', str(row['Variation name (color)'])).strip()
        variants.append({
            'name': color,
            'sku': str(row['Variation SKU']),
            'price': float(row['Price']),
            'stock': 10
        })
        
    product = {
        'id': slug,
        'name': str(title),
        'category': cat_mapping.get(first['Category'], 'ANFittings'),
        'price': float(group['Price'].min()),
        'description': str(first['Description']).split('\n')[0].strip(),
        'image': str(first['Variation Image Link']),
        'variants': variants
    }
    
    with open(f'content/products/{slug}.json', 'w') as f:
        json.dump(product, f, indent=2)

print("Finished generating 392 JSON files in content/products/")
