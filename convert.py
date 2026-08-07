import pandas as pd
import json
import os
import re
import glob

# Ensure product directory exists (Never clears or deletes files)
os.makedirs('content/products', exist_ok=True)

def safe_float(val, default=0.0):
    try:
        cleaned = re.sub(r'[^0-9.]', '', str(val))
        return float(cleaned) if cleaned else default
    except Exception:
        return default

def clean_text(raw_desc):
    if not isinstance(raw_desc, str) or pd.isna(raw_desc):
        return ""
    if "import pandas" in raw_desc or "def build" in raw_desc or "spec_block" in raw_desc:
        return ""
    
    desc = raw_desc.replace('\\n', '\n').replace('\r', '')
    desc = re.sub(r'Founded in 2008.*?\.\s*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'Want to learn more.*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'Looking to complete your system\?.*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'\bwe\b', 'the manufacturer', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\bour\b', 'their', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\bus\b', 'the manufacturer', desc, flags=re.IGNORECASE)

    paragraphs = [p.strip() for p in desc.split('\n') if p.strip()]
    return "<br><br>".join(paragraphs) if paragraphs else ""

# ---------------------------------------------------------
# Exact Mapping Dictionary for AN & Fluid Hardware
# ---------------------------------------------------------
subcat_mapping = {
    'Adapters and Unions': ('AN Adapters', 'AN Adapters & Specialty'),
    'ORB Adapters': ('AN Adapters', 'ORB Adapters'),
    'NPT Adapters': ('AN Adapters', 'NPT Adapters'),
    'Hardline Adapters': ('AN Adapters', 'Hardline Adapters'),
    'Metric adapters': ('AN Adapters', 'Metric Adapters'),
    'SAE Fittings': ('AN Adapters', 'SAE Fittings'),
    'Brake Fittings': ('AN Adapters', 'Brake Fittings'),
    'EFI/LS-Connector/Quick-Connector': ('AN Adapters', 'EFI Quick Connectors'),
    'Specialty Fitting & PCV Delete': ('AN Adapters', 'Specialty Fittings'),
    'Weld-On Bungs': ('AN Adapters', 'Weld-On Bungs'),
    'Barb Fittings': ('AN Adapters', 'Barb Fittings'),
    'Caps, Plugs, and Blockoffs': ('AN Adapters', 'Plugs & Blockoffs'),
    
    'AN Fittings': ('AN Fittings', 'AN Hose Ends & Fittings'),
    'Hose Fittings': ('AN Fittings', 'AN Hose Ends & Fittings'),
    'PTFE Hose Fittings': ('AN Fittings', 'PTFE Hose Ends'),
    'Push-Loc Hose Ends': ('AN Fittings', 'Push-Loc Hose Ends'),
    
    'PTFE Hose': ('PTFE Hose', 'PTFE Hose & Lines'),
    'Nylon Hose': ('Nylon Hose', 'Nylon Braided Hose'),
    'Hose & Line': ('Nylon Hose', 'Nylon Braided Hose'),
    
    'Hose Clamps & Separators': ('Hose Clamps', 'Hose Separators & Clamps'),
    'Hose Separators': ('Hose Clamps', 'Hose Separators & Clamps'),
    
    'Fitting Assembly Tools': ('Tools', 'Hand Tools & Specialty'),
    'Fitting Sockets': ('Tools', 'Hand Tools & Specialty'),
    'Tools': ('Tools', 'Hand Tools & Specialty'),
    
    'Fuel Filters': ('Fuel Systems', 'Fuel Filters'),
    'Oil Cooler Parts': ('Oil Coolers', 'Oil Coolers'),
    'Radiators': ('Radiators', 'Radiators')
}

# ---------------------------------------------------------
# Bulletproof Category Engine 
# ---------------------------------------------------------
def determine_category(title, raw_cat=""):
    t = str(title).lower()
    c = str(raw_cat).replace('&amp;', '&').strip()
    
    # 1. Turbos & Wastegates
    if any(k in t for k in ['wastegate', 'wg40', 'wg45', 'compgate', 'hypergate', 'genv']):
        return ('Wastegates', 'External Wastegates')
    if 'turbo kit' in t or 'twin turbo' in t:
        return ('Turbos', 'Complete Turbo Kits')
    if 'turbocharger' in t or 'turbo ' in t or t.startswith('turbo'):
        if 'bov' not in t and 'drain' not in t:
            return ('Turbos', 'Turbochargers')
        
    # 2. Boost Control & Valves
    if any(k in t for k in ['bov', 'blow off', 'diverter', 'kompact']):
        return ('Blow Off Valves', 'BOV & Diverter Valves')
    if any(k in t for k in ['boost controller', 'boost tee', 'eboost']):
        return ('Boost Controllers', 'Manual & Electronic Controllers')
        
    # 3. Fuel & Exhaust
    if any(k in t for k in ['fpr', 'fuel pressure regulator']):
        return ('Fuel Systems', 'Fuel Pressure Regulators')
    if 'muffler' in t or 'exhaust' in t:
        return ('Exhaust', 'Mufflers & Hardware')
        
    # 4. Gauges & Monitoring
    if 'gauge' in t:
        return ('Gauges', 'Monitoring')
        
    # 5. Exact Dictionary Match (For ColorFittings / Fluid Hardware)
    if c in subcat_mapping:
        return subcat_mapping[c]
        
    # 6. Fallback
    if c and c.lower() not in ['nan', 'none', '']:
        return (c.title(), 'General')
        
    return ('Performance Hardware', 'Universal')

# ---------------------------------------------------------
# Dynamic Description Builders
# ---------------------------------------------------------
def generate_turbosmart_desc(sku, title):
    t = str(title).lower()
    specs = [
        "<b>Brand & Engineering:</b> Genuine Turbosmart high-performance motorsport hardware.",
        "<b>Construction:</b> Precision CNC-machined billet aluminum housing with hard-anodized finish."
    ]
    
    if 'boost tee' in t or 'boost controller' in t:
        lead = f"The <b>{title}</b> utilizes Turbosmart's proven gated boost control system to bring boost on faster and prevent premature wastegate opening."
        specs.append("<b>Control Type:</b> Detent adjustment system for precise, leak-free boost adjustments.")
    elif 'eboost' in t:
        lead = f"The <b>{title}</b> is an advanced electronic boost controller capable of handling high boost levels with multiple boost group settings and boost-by-gear control."
        specs.append("<b>Pressure Rating:</b> Rated up to 40psi for high-output turbocharged applications.")
    elif 'bov' in t or 'kompact' in t:
        lead = f"The <b>{title}</b> provides direct plug-and-play upgrade capability over weak factory diverter valves, holding extreme boost pressure without leaking."
        specs.append("<b>Response:</b> Fast-acting piston mechanism prevents compressor surge under sudden throttle lift.")
    elif 'fpr' in t or 'fuel pressure' in t:
        lead = f"The <b>{title}</b> delivers dead-accurate fuel pressure regulation across high-horsepower EFI applications running pump gas, race gas, or E85."
        specs.append("<b>Ratio:</b> 1:1 manifold pressure reference for linear fuel delivery under boost.")
    elif 'wg40' in t or 'wg45' in t or 'wastegate' in t:
        size = "40mm" if "wg40" in t else "45mm"
        lead = f"The <b>{title}</b> represents Turbosmart's GenV thermal engineering, featuring modular actuator housing and maximum flow efficiency."
        specs.append(f"<b>Valve Size:</b> {size} high-temp stainless steel valve assembly.")
        specs.append("<b>Cooling & Rotation:</b> Integrated liquid cooling ports and 360-degree actuator cap positioning.")
    else:
        lead = f"The <b>{title}</b> is engineered for extreme durability and precise pressure management in competition fluid and boost systems."

    return f"{lead}<br><br><b>Technical Specifications:</b><br>• " + "<br>• ".join(specs)

def generate_colorfittings_desc(title, row_desc):
    title_str = str(title).strip()
    angle_match = re.search(r'(\d+)\s*(Degree|Deg|\°)', title_str, re.IGNORECASE)
    angle = f"{angle_match.group(1)}°" if angle_match else None
    
    is_ptfe = 'ptfe' in title_str.lower()
    is_orb = 'orb' in title_str.lower() or 'o-ring boss' in title_str.lower()
    is_npt = 'npt' in title_str.lower()
    is_efi = 'efi' in title_str.lower() or 'quick connect' in title_str.lower()

    clean_body = clean_text(row_desc)
    lead = f"The <b>{title_str}</b> is engineered for high-demand automotive fluid systems. {clean_body}".strip()

    specs = [
        "<b>Origin:</b> Precision CNC-machined in the USA.",
        "<b>Material & Finish:</b> 6061-T6 Billet Aluminum with hard anodized protective finish."
    ]
    if angle:
        specs.append(f"<b>Flow Configuration:</b> {angle} mandrel-bent profile for maximum fluid velocity in tight engine bays.")
    if is_ptfe:
        specs.append("<b>Compatibility:</b> Engineered specifically for PTFE hose. Impervious to E85, race gas, methanol, and power steering fluid.")
    if is_orb:
        specs.append("<b>Sealing Type:</b> Viton O-Ring Boss (ORB) positive seal to prevent thread sealant contamination.")
    if is_npt:
        specs.append("<b>Thread Pitch:</b> Precision NPT tapered threads for leak-free sealing in blocks and cells.")
    if is_efi:
        specs.append("<b>Quick Connect:</b> High-pressure fuel rail latch mechanism.")

    return f"{lead}<br><br><b>Technical Specifications:</b><br>• " + "<br>• ".join(specs)

# ---------------------------------------------------------
# Main Execution: Scan and Build
# ---------------------------------------------------------
def find_col(df_cols, possible_names):
    col_map = {str(c).lower().strip(): c for c in df_cols}
    for name in possible_names:
        if name in col_map:
            return col_map[name]
    return None

print("Scanning repository for all CSV files...")
csv_files = glob.glob('**/*.csv', recursive=True) + glob.glob('**/*.CSV', recursive=True)
csv_files = list(set(csv_files))

for csv_path in csv_files:
    try:
        df = pd.read_csv(csv_path)
        cols = df.columns.tolist()
        
        title_col = find_col(cols, ['title', 'name', 'product name', 'item name'])
        sku_col = find_col(cols, ['variation sku', 'sku', 'part number', 'item number'])
        price_col = find_col(cols, ['map_price', 'price', 'retail price', 'msrp', 'variant price'])
        img_col = find_col(cols, ['variation image link', 'image_url', 'image', 'picture', 'image src'])
        cat_col = find_col(cols, ['category', 'product type', 'type'])
        desc_col = find_col(cols, ['description', 'body', 'overview'])
        color_col = find_col(cols, ['variation name (color)', 'color', 'option1 value', 'variant'])
        vendor_col = find_col(cols, ['vendor', 'brand', 'manufacturer'])

        if not title_col:
            title_col = cols[0]

        grouped = df.groupby(title_col, sort=False)
        
        for title, group in grouped:
            title_str = str(title).strip()
            if not title_str or title_str.lower() in ['nan', 'none']:
                continue
            
            first_sku = str(group.iloc[0][sku_col]).lower() if sku_col else ""
            if 'stock' in first_sku and 'out of stock' in title_str.lower():
                continue
                
            slug = re.sub(r'[^a-z0-9]+', '-', title_str.lower()).strip('-')
            first_row = group.iloc[0]
            
            raw_cat = str(first_row[cat_col]) if cat_col else ""
            cat, subcat = determine_category(title_str, raw_cat)
            
            vendor_name = str(first_row[vendor_col]) if vendor_col else "Unknown"
            raw_desc = str(first_row[desc_col]) if desc_col else ""
            
            if "turbosmart" in vendor_name.lower() or "map_price" in [str(c).lower() for c in cols]:
                description = generate_turbosmart_desc(first_sku, title_str)
                brand_val = "Turbosmart"
            else:
                description = generate_colorfittings_desc(title_str, raw_desc)
                brand_val = vendor_name if vendor_name.lower() != 'nan' else "Aftermarket"
            
            main_img = str(first_row[img_col]).strip() if img_col and pd.notna(first_row[img_col]) else ""
            main_sku = str(first_row[sku_col]).strip() if sku_col else ""

            variants = []
            prices = []
            for _, row in group.iterrows():
                p_val = safe_float(row[price_col]) if price_col else 0.0
                prices.append(p_val)
                
                v_name = str(row[color_col]) if color_col and pd.notna(row[color_col]) else "Standard"
                v_name = re.sub(r'\s*\[\+\$[0-9\.]+\]', '', v_name).strip()
                v_sku = str(row[sku_col]).strip() if sku_col else main_sku
                v_img = str(row[img_col]).strip() if img_col and pd.notna(row[img_col]) else main_img
                
                variants.append({
                    "name": v_name if v_name.lower() != 'nan' else "Standard",
                    "sku": v_sku,
                    "price": round(p_val, 2),
                    "image": v_img,
                    "stock": 10
                })

            product = {
                "id": slug,
                "name": title_str,
                "title": title_str,
                "sku": main_sku,
                "brand": brand_val,
                "category": cat,
                "subcategory": subcat,
                "anSize": "Universal",
                "price": round(min(prices), 2) if prices else 0.0,
                "description": description,
                "image": main_img,
                "variants": variants
            }
            
            with open(f'content/products/{slug}.json', 'w') as f:
                json.dump(product, f, indent=2)

    except Exception as e:
        print(f"Error processing CSV {csv_path}: {e}")

# ---------------------------------------------------------
# Compile everything into inventory.json 
# ---------------------------------------------------------
all_products = []
if os.path.exists('content/products'):
    for fname in os.listdir('content/products'):
        if fname.endswith('.json'):
            filepath = os.path.join('content/products', fname)
            try:
                with open(filepath, 'r') as f:
                    all_products.append(json.load(f))
            except Exception as e:
                print(f"Error reading {fname}: {e}")

with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Compilation Complete: {len(all_products)} products saved to inventory.json.")
