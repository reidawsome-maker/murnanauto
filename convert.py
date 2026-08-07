import pandas as pd
import json
import os
import re

# Read CSV
df = pd.read_csv('your-master-catalog.csv')
os.makedirs('content/products', exist_ok=True)

# Explicit items and keywords to permanently purge
EXCLUDE_EXACT_TITLES = [
    "cummins turbo drain tube adapter",
    "3/8\" ptc air fitting to 6 an adapter",
    "3/8\" ptc air fitting to -6 an adapter"
]

DELETED_KEYWORDS = [
    "finisher", "worm", "hex / worm", "per foot", "by the foot", "1 foot"
]

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

def safe_float(val):
    try:
        cleaned = re.sub(r'[^0-9.]', '', str(val))
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0

def build_part_description(row, title):
    title_str = str(title).strip()
    cat_str = str(row.get('Category', '')).strip()
    
    # 1. Parse AN size, angle, and connection specs
    an_match = re.search(r'(-?\d+)\s*AN', title_str, re.IGNORECASE)
    
    angle_match = re.search(r'(\d+)\s*(Degree|Deg|\°)', title_str, re.IGNORECASE)
    angle = f"{angle_match.group(1)}°" if angle_match else None
    
    is_ptfe = 'ptfe' in title_str.lower() or 'ptfe' in cat_str.lower()
    is_orb = 'orb' in title_str.lower() or 'o-ring boss' in title_str.lower()
    is_npt = 'npt' in title_str.lower()
    is_efi = 'efi' in title_str.lower() or 'quick connect' in title_str.lower()

    # 2. Extract raw description & SANITIZE CORRUPTED PYTHON CODE TEXT
    raw_desc = str(row.get('Description', '')) if not pd.isna(row.get('Description', '')) else ""
    
    # Hard purge if string contains raw python code from earlier pastes
    if "import pandas" in raw_desc or "def build_part_description" in raw_desc or "spec_block" in raw_desc:
        raw_desc = ""

    raw_desc = raw_desc.replace('\\n', '\n').replace('\r', '')
    
    # Strip out vendor boilerplate and external links
    raw_desc = re.sub(r'Founded in 2008, ColorFittings.*?\.\s*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)
    raw_desc = re.sub(r'Want to learn more.*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)
    raw_desc = re.sub(r'Looking to complete your system\?.*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)
    raw_desc = re.sub(r'Explore our full range.*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)

    # 3. Third-person conversion
    raw_desc = re.sub(r'\bwe\b', 'Color-Fittings', raw_desc, flags=re.IGNORECASE)
    raw_desc = re.sub(r'\bour\b', 'the', raw_desc, flags=re.IGNORECASE)
    raw_desc = re.sub(r'\bus\b', 'the manufacturer', raw_desc, flags=re.IGNORECASE)

    clean_paragraphs = [p.strip() for p in raw_desc.split('\n') if p.strip()]
    lead_body = f" {clean_paragraphs[0]}" if clean_paragraphs else ""

    # 4. Construct Technical Specs
    specs = [
        "<b>Origin:</b> Precision CNC-machined in the USA.",
        "<b>Material & Finish:</b> 6061-T6 Billet Aluminum with an anodized finish for maximum corrosion resistance."
    ]
    
    if angle:
        specs.append(f"<b>Flow Configuration:</b> {angle} mandrel-bent profile for high velocity in tight engine bays.")
    if is_ptfe:
        specs.append("<b>Compatibility:</b> Engineered specifically for PTFE hose. Impervious to E85, race gas, methanol, and power steering fluid.")
    if is_orb:
        specs.append("<b>Sealing Type:</b> Viton O-Ring Boss (ORB) positive seal to prevent thread sealant contamination.")
    if is_npt:
        specs.append("<b>Thread Pitch:</b> Precision NPT tapered threads for leak-free sealing in blocks and cells.")
    if is_efi:
        specs.append("<b>Quick Connect:</b> High-pressure fuel rail latch mechanism.")

    spec_block = "<br><br><b>Technical Specifications:</b><br>• " + "<br>• ".join(specs)

    return f"The <b>{title_str}</b> is engineered for demanding high-performance automotive fluid systems.{lead_body}{spec_block}"

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
    title = str(row['Title']).lower().strip()
    cat = str(row['Category']).lower().strip()

    if any(ex in title for ex in EXCLUDE_EXACT_TITLES):
        return False

    if any(k in title or k in cat for k in DELETED_KEYWORDS):
        return False

    if ('line' in title or 'lines' in title) and 'hardline adapter' not in title:
        return False

    if 'stainless steel' in title and 'hose' in title:
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

    if 'turbo kit' in t or 'twin turbo' in t or 'single turbo' in t:
        return ('Kits', 'Complete Turbo Kits')
    if 'turbocharger' in t or 'turbo ' in t or t.startswith('turbo'):
        return ('Turbos', 'Turbochargers')

    if 'v-band' in t or 'v-band' in c.lower():
        if 'clamp' in t or 'flange' in t or 'assembly' in t or 'set' in t:
            return ('V-Band', 'V-Bands & Clamps')

    if 'oil cooler' in t or 'sandwich plate' in t or 'oil cooler parts' in c.lower():
        return ('OilCoolers', 'Oil Coolers')
    if 'radiator' in t:
        return ('Radiators', 'Radiators')

    if 'ptfe' in t and 'fitting' not in t and 'end' not in t:
        return ('PTFEHose', 'PTFE Hose & Lines')
    if 'nylon' in t or 'braided hose' in t:
        return ('NylonHose', 'Nylon Braided Hose')

    return subcat_mapping.get(c, ('ANFittings', 'AN Hose Ends & Fittings'))

# Clear existing json products before building clean catalog
if os.path.exists('content/products'):
    for f in os.listdir('content/products'):
        if f.endswith('.json'):
            os.remove(os.path.join('content/products', f))

df_filtered = df[df.apply(is_keep_item, axis=1)].copy()
grouped = df_filtered.groupby('Title', sort=False)

all_products = []

for title, group in grouped:
    slug = re.sub(r'[^a-z0-9]+', '-', str(title).lower()).strip('-')
    first = group.iloc[0]
    title_str = str(title)
    
    category, subcategory = determine_category(title_str, first['Category'])
    an_size_label = extract_an_size_label(title_str)
    
    cleaned_desc = build_part_description(first, title_str)
    
    variants = []
    prices = []
    for _, row in group.iterrows():
        color_name = re.sub(r'\s*\[\+\$[0-9\.]+\]', '', str(row['Variation name (color)'])).strip()
        img_link = str(row['Variation Image Link']).strip()
        sku_val = str(row['Variation SKU']).strip()
        price_val = safe_float(row['Price'])
        prices.append(price_val)
        
        variants.append({
            'name': color_name,
            'sku': sku_val,
            'price': price_val,
            'image': img_link,
            'stock': 10
        })
        
    min_price = min(prices) if prices else 0.0
    
    product = {
        'id': slug,
        'name': title_str,
        'title': title_str,
        'sku': str(first['Variation SKU']).strip(),
        'category': category,
        'subcategory': subcategory,
        'anSize': an_size_label,
        'price': min_price,
        'description': cleaned_desc,
        'image': str(first['Variation Image Link']).strip(),
        'variants': variants
    }
    
    with open(f'content/products/{slug}.json', 'w') as f:
        json.dump(product, f, indent=2)
        
    all_products.append(product)

with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Catalog generated successfully. {len(all_products)} active products.")
