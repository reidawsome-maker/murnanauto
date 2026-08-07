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
    # Strip out accidental code artifacts
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
# Bulletproof Category Engine 
# ---------------------------------------------------------
def determine_category(title, raw_cat):
    t = str(title).lower()
    c = str(raw_cat).strip().lower()

    # 1. HARDWARE KEYWORD OVERRIDES (Highest Priority)
    if any(k in t for k in ['wastegate', 'wg40', 'wg45', 'compgate', 'hypergate', 'genv']):
        return 'Wastegates', 'External Wastegates'
    
    if any(k in t for k in ['bov', 'blow off', 'diverter', 'kompact']):
        return 'Blow Off Valves', 'BOV & Diverter Valves'
        
    if any(k in t for k in ['boost controller', 'boost tee', 'eboost']):
        return 'Boost Controllers', 'Manual & Electronic Controllers'
        
    if any(k in t for k in ['fpr', 'fuel pressure regulator']):
        return 'Fuel Systems', 'Fuel Pressure Regulators'
        
    if 'gauge' in t:
        return 'Gauges', 'Monitoring'
        
    if 'turbo kit' in t or 'twin turbo' in t:
        return 'Turbos', 'Complete Turbo Kits'
        
    if 'turbocharger' in t or 'turbo ' in t or t.startswith('turbo'):
        if 'drain' not in t and 'feed' not in t and 'bov' not in t:
            return 'Turbos', 'Turbochargers'
            
    if 'muffler' in t or 'exhaust' in t:
        return 'Exhaust', 'Mufflers & Hardware'

    if 'clamp' in t or 'v-band' in t:
        if 'separator' not in t:
            return 'Hardware', 'Clamps & V-Bands'

    # 2. EXACT COLORFITTINGS DICTIONARY MATCHES
    subcat_mapping = {
        'adapters and unions': ('AN Adapters', 'AN Adapters & Specialty'),
        'orb adapters': ('AN Adapters', 'ORB Adapters'),
        'npt adapters': ('AN Adapters', 'NPT Adapters'),
        'hardline adapters': ('AN Adapters', 'Hardline Adapters'),
        'metric adapters': ('AN Adapters', 'Metric Adapters'),
        'sae fittings': ('AN Adapters', 'SAE Fittings'),
        'brake fittings': ('AN Adapters', 'Brake Fittings'),
        'efi/ls-connector/quick-connector': ('AN Adapters', 'EFI Quick Connectors'),
        'specialty fitting & pcv delete': ('AN Adapters', 'Specialty Fittings'),
        'weld-on bungs': ('AN Adapters', 'Weld-On Bungs'),
        'barb fittings': ('AN Adapters', 'Barb Fittings'),
        'caps, plugs, and blockoffs': ('AN Adapters', 'Plugs & Blockoffs'),
        'an fittings': ('AN Fittings', 'AN Hose Ends & Fittings'),
        'hose fittings': ('AN Fittings', 'AN Hose Ends & Fittings'),
        'ptfe hose fittings': ('AN Fittings', 'PTFE Hose Ends'),
        'push-loc hose ends': ('AN Fittings', 'Push-Loc Hose Ends'),
        'ptfe hose': ('PTFE Hose', 'PTFE Hose & Lines'),
        'nylon hose': ('Nylon Hose', 'Nylon Braided Hose'),
        'hose & line': ('Nylon Hose', 'Nylon Braided Hose'),
        'hose clamps & separators': ('Hose Clamps', 'Hose Separators & Clamps'),
        'hose separators': ('Hose Clamps', 'Hose Separators & Clamps'),
        'fitting assembly tools': ('Tools', 'Hand Tools & Specialty'),
        'fitting sockets': ('Tools', 'Hand Tools & Specialty'),
        'tools': ('Tools', 'Hand Tools & Specialty'),
        'fuel filters': ('Fuel Systems', 'Fuel Filters'),
        'oil cooler parts': ('Oil Coolers', 'Oil Coolers'),
        'radiators': ('Radiators', 'Radiators')
    }
    
    if c in subcat_mapping:
        return subcat_mapping[c]
        
    # 3. CSV FALLBACK (If CSV has a valid category, use it)
    if c and c not in ['nan', 'none', '', 'universal']:
        return str(raw_cat).strip().title(), 'General'
        
    # 4. ABSOLUTE DEFAULT
    return 'Performance Hardware', 'Universal'

def generate_smart_description(title, raw_desc, vendor):
    t = str(title).lower()
    clean_body = clean_text(raw_desc)
    
    lead = f"The <b>{title}</b> is a premium high-performance component engineered for rigorous fluid and boost applications."
    specs = []
    
    if "turbosmart" in str(vendor).lower() or 'ts-' in t:
        specs.append("<b>Brand & Engineering:</b> Genuine Turbosmart high-performance motorsport hardware.")
        specs.append("<b>Construction:</b> Precision CNC-machined billet aluminum housing with hard-anodized finish.")
    else:
        specs.append("<b>Construction:</b> Precision CNC-machined in the USA. (6061-T6 Billet Aluminum for fittings)")

    # Auto-detect specs
    if 'wastegate' in t or 'wg40' in t or 'wg45' in t:
        specs.append("<b>Thermal Management:</b> Integrated liquid cooling ports and 360-degree actuator cap positioning.")
    if 'bov' in t or 'kompact' in t:
        specs.append("<b>Response:</b> Fast-acting piston mechanism prevents compressor surge under sudden throttle lift.")
    if 'fpr' in t or 'fuel pressure' in t:
        specs.append("<b>Ratio:</b> 1:1 manifold pressure reference for linear fuel delivery under boost.")
    
    angle_match = re.search(r'(\d+)\s*(Degree|Deg|\°)', t, re.IGNORECASE)
    if angle_match:
        specs.append(f"<b>Flow Configuration:</b> {angle_match.group(1)}° mandrel-bent profile for maximum velocity.")
    
    if 'ptfe' in t:
        specs.append("<b>Compatibility:</b> Engineered for PTFE hose. Impervious to E85, race gas, methanol, and power steering fluid.")
    if 'orb' in t:
        specs.append("<b>Sealing Type:</b> Viton O-Ring Boss (ORB) positive seal.")

    spec_html = "<br><br><b>Technical Specifications:</b><br>• " + "<br>• ".join(specs)
    
    if clean_body:
        return f"{lead} {clean_body}{spec_html}"
    return f"{lead}{spec_html}"

def find_col(df_cols, possible_names):
    col_map = {str(c).lower().strip(): c for c in df_cols}
    for name in possible_names:
        if name in col_map:
            return col_map[name]
    return None

# ---------------------------------------------------------
# Main Execution: Scan and Build
# ---------------------------------------------------------
print("Scanning repository for all CSV files...")
csv_files = glob.glob('**/*.csv', recursive=True) + glob.glob('**/*.CSV', recursive=True)
csv_files = list(set(csv_files))

for csv_path in csv_files:
    try:
        df = pd.read_csv(csv_path)
        cols = df.columns.tolist()
        
        # Map columns dynamically based on any CSV structure
        title_col = find_col(cols, ['title', 'name', 'product name', 'item name'])
        sku_col = find_col(cols, ['variation sku', 'sku', 'part number', 'item number'])
        price_col = find_col(cols, ['map_price', 'price', 'retail price', 'msrp', 'variant price'])
        img_col = find_col(cols, ['variation image link', 'image_url', 'image', 'picture', 'image src'])
        cat_col = find_col(cols, ['category', 'product type', 'type', 'category name'])
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
            
            # Exclude stock tracking artifacts
            first_sku = str(group.iloc[0][sku_col]).lower() if sku_col else ""
            if 'stock' in first_sku and 'out of' in title_str.lower():
                continue
                
            slug = re.sub(r'[^a-z0-9]+', '-', title_str.lower()).strip('-')
            first_row = group.iloc[0]
            
            # Category Processing
            raw_cat = str(first_row[cat_col]) if cat_col else ""
            cat, subcat = determine_category(title_str, raw_cat)
            
            # Vendor & Description Processing
            vendor_name = str(first_row[vendor_col]) if vendor_col else ""
            if not vendor_name or vendor_name.lower() == 'nan':
                vendor_name = "Turbosmart" if "TS-" in first_sku.upper() else "Aftermarket"
            
            raw_desc = str(first_row[desc_col]) if desc_col else ""
            description = generate_smart_description(title_str, raw_desc, vendor_name)
            
            main_img = str(first_row[img_col]).strip() if img_col and pd.notna(first_row[img_col]) else ""
            main_sku = str(first_row[sku_col]).strip() if sku_col and pd.notna(first_row[sku_col]) else ""

            variants = []
            prices = []
            for _, row in group.iterrows():
                p_val = safe_float(row[price_col]) if price_col else 0.0
                if p_val > 0: prices.append(p_val)
                
                v_name = str(row[color_col]) if color_col and pd.notna(row[color_col]) else "Standard"
                v_name = re.sub(r'\s*\[\+\$[0-9\.]+\]', '', v_name).strip()
                v_sku = str(row[sku_col]).strip() if sku_col and pd.notna(row[sku_col]) else main_sku
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
                "brand": vendor_name,
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
# Safe Compile into inventory.json 
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
                pass

with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Compilation Complete: {len(all_products)} products safely saved to inventory.json.")
