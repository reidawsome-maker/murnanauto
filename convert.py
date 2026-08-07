import pandas as pd
import json
import os
import re
import glob

os.makedirs('content/products', exist_ok=True)

# 1. Automatically locate and concatenate ALL CSV files in the project folder
csv_files = glob.glob('*.csv')
if not csv_files:
    print("No CSV files found in directory.")
    exit(1)

df_list = []
for f in csv_files:
    try:
        temp_df = pd.read_csv(f)
        df_list.append(temp_df)
    except Exception as e:
        print(f"Error loading {f}: {e}")

df = pd.concat(df_list, ignore_index=True)

# Helper function to flexibly fetch values across different vendor CSV column names
def get_col(row, column_options, default=''):
    for col in column_options:
        if col in row and not pd.isna(row[col]):
            return str(row[col]).strip()
    return default

EXCLUDE_EXACT_TITLES = [
    "cummins turbo drain tube adapter",
    "3/8\" ptc air fitting to 6 an adapter",
    "3/8\" ptc air fitting to -6 an adapter"
]

DELETED_KEYWORDS = ["per foot", "by the foot", "1 foot"]

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
    cat_str = get_col(row, ['Category', 'category', 'Category Name'])
    raw_desc = get_col(row, ['Description', 'description', 'Overview', 'Body'])

    # Hard-purge if string contains raw python code from prior pastes
    if "import pandas" in raw_desc or "def build_part_description" in raw_desc or "spec_block" in raw_desc:
        raw_desc = ""

    raw_desc = raw_desc.replace('\\n', '\n').replace('\r', '')
    
    # Strip out vendor boilerplate and external links
    raw_desc = re.sub(r'Founded in 2008, ColorFittings.*?\.\s*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)
    raw_desc = re.sub(r'Want to learn more.*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)
    raw_desc = re.sub(r'Looking to complete your system\?.*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)
    raw_desc = re.sub(r'Explore our full range.*', '', raw_desc, flags=re.DOTALL | re.IGNORECASE)

    # Neutralize third-person phrasing
    raw_desc = re.sub(r'\bwe\b', 'Color-Fittings', raw_desc, flags=re.IGNORECASE)
    raw_desc = re.sub(r'\bour\b', 'the', raw_desc, flags=re.IGNORECASE)
    raw_desc = re.sub(r'\bus\b', 'the manufacturer', raw_desc, flags=re.IGNORECASE)

    clean_paragraphs = [p.strip() for p in raw_desc.split('\n') if p.strip()]
    lead_body = f" {clean_paragraphs[0]}" if clean_paragraphs else ""

    # Parse specs
    angle_match = re.search(r'(\d+)\s*(Degree|Deg|\°)', title_str, re.IGNORECASE)
    angle = f"{angle_match.group(1)}°" if angle_match else None
    
    is_ptfe = 'ptfe' in title_str.lower() or 'ptfe' in cat_str.lower()
    is_orb = 'orb' in title_str.lower() or 'o-ring boss' in title_str.lower()
    is_npt = 'npt' in title_str.lower()
    is_efi = 'efi' in title_str.lower() or 'quick connect' in title_str.lower()

    specs = [
        "<b>Origin:</b> Precision CNC-machined in the USA.",
        "<b>Material & Finish:</b> Premium high-grade construction with corrosion-resistant coating."
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

def is_keep_item(row):
    title = get_col(row, ['Title', 'title', 'Name', 'product_name']).lower()
    if not title:
        return False

    if any(ex in title for ex in EXCLUDE_EXACT_TITLES):
        return False

    if any(k in title for k in DELETED_KEYWORDS):
        return False

    return True

def determine_category(title, raw_cat):
    t = str(title).lower()
    c = str(raw_cat).replace('&amp;', '&').strip()

    if 'muffler' in t or 'exhaust' in t:
        return ('Exhaust', 'Mufflers & Exhaust')
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

# Clear existing json products before compiling total catalog
if os.path.exists('content/products'):
    for f in os.listdir('content/products'):
        if f.endswith('.json'):
            os.remove(os.path.join('content/products', f))

# Normalize titles across compiled CSV data
df['Title_Clean'] = df.apply(lambda r: get_col(r, ['Title', 'title', 'Name', 'product_name']), axis=1)
df_filtered = df[df.apply(is_keep_item, axis=1)].copy()
grouped = df_filtered.groupby('Title_Clean', sort=False)

all_products = []

for title, group in grouped:
    if not title:
        continue
    slug = re.sub(r'[^a-z0-9]+', '-', str(title).lower()).strip('-')
    first = group.iloc[0]
    title_str = str(title)
    
    category, subcategory = determine_category(title_str, get_col(first, ['Category', 'category']))
    an_size_label = extract_an_size_label(title_str)
    
    cleaned_desc = build_part_description(first, title_str)
    
    variants = []
    prices = []
    for _, row in group.iterrows():
        color_name = get_col(row, ['Variation name (color)', 'Variation Name', 'Color', 'Option1 Value'], 'Standard')
        color_name = re.sub(r'\s*\[\+\$[0-9\.]+\]', '', color_name).strip()
        img_link = get_col(row, ['Variation Image Link', 'Image Link', 'Image Src', 'image'])
        sku_val = get_col(row, ['Variation SKU', 'SKU', 'sku'])
        price_val = safe_float(get_col(row, ['Price', 'price', 'Variant Price']))
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
        'sku': get_col(first, ['Variation SKU', 'SKU', 'sku']),
        'category': category,
        'subcategory': subcategory,
        'anSize': an_size_label,
        'price': min_price,
        'description': cleaned_desc,
        'image': get_col(first, ['Variation Image Link', 'Image Link', 'Image Src', 'image']),
        'variants': variants
    }
    
    with open(f'content/products/{slug}.json', 'w') as f:
        json.dump(product, f, indent=2)
        
    all_products.append(product)

with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Catalog compiled successfully. {len(all_products)} active products built across all CSV files.")
