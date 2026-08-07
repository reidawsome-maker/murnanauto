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
    desc = re.sub(r'Founded in 2008.*?\\.\\s*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'Want to learn more.*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'Looking to complete your system\?.*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'\bwe\b', 'the manufacturer', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\bour\b', 'their', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\bus\b', 'the manufacturer', desc, flags=re.IGNORECASE)

    paragraphs = [p.strip() for p in desc.split('\n') if p.strip()]
    return "<br><br>".join(paragraphs) if paragraphs else ""

# ---------------------------------------------------------
# Bulletproof Category Engine 
# (Ensures Wastegates go to Wastegates, Turbos to Turbos, etc.)
# ---------------------------------------------------------
def auto_categorize(title, raw_cat=""):
    search_text = (str(title) + " " + str(raw_cat)).lower()
    
    # 1. Turbos & Wastegates
    if any(k in search_text for k in ['wastegate', 'wg40', 'wg45', 'compgate', 'hypergate', 'genv']):
        return 'Wastegates', 'External Wastegates'
    if 'turbo' in search_text and 'bov' not in search_text:
        return 'Turbos', 'Turbochargers & Accessories'
    
    # 2. Boost Control & Valves
    if any(k in search_text for k in ['bov', 'blow off', 'diverter', 'kompact']):
        return 'Blow Off Valves', 'BOV & Diverter Valves'
    if any(k in search_text for k in ['boost controller', 'boost tee', 'eboost']):
        return 'Boost Controllers', 'Manual & Electronic Controllers'
    
    # 3. Fuel & Exhaust
    if any(k in search_text for k in ['fpr', 'fuel pressure', 'regulator']):
        return 'Fuel Systems', 'Fuel Pressure Regulators'
    if 'muffler' in search_text or 'exhaust' in search_text:
        return 'Exhaust', 'Mufflers & Hardware'
    
    # 4. Fittings & Hoses
    if 'ptfe' in search_text:
        return 'PTFE Hose', 'Lines & Fittings'
    if 'nylon' in search_text or 'braided' in search_text:
        return 'Nylon Hose', 'Lines & Fittings'
    if any(k in search_text for k in ['fitting', 'adapter', 'orb', 'npt', 'union', 'bung', 'an ']):
        return 'AN Fittings', 'Adapters & Hose Ends'
    
    # 5. General / Hardware
    if 'gauge' in search_text:
        return 'Gauges', 'Monitoring'
    if 'cooler' in search_text or 'radiator' in search_text:
        return 'Cooling', 'Coolers & Radiators'
    
    # Fallback to provided category from CSV, otherwise Universal
    if raw_cat and str(raw_cat).lower() not in ['nan', '', 'none']:
        return str(raw_cat).title(), 'General'
        
    return 'Performance Hardware', 'Universal'

# ---------------------------------------------------------
# Dynamic Description Builder
# ---------------------------------------------------------
def generate_smart_description(title, raw_desc, vendor):
    t = str(title).lower()
    clean_body = clean_text(raw_desc)
    
    lead = f"The <b>{title}</b> is a high-performance component engineered for demanding automotive applications."
    specs = []
    
    if "turbosmart" in str(vendor).lower() or 'ts-' in t:
        specs.append("<b>Brand & Engineering:</b> Genuine Turbosmart high-performance motorsport hardware.")
        specs.append("<b>Construction:</b> Precision CNC-machined billet aluminum housing with hard-anodized finish.")
    else:
        specs.append("<b>Construction:</b> Precision machined for rigorous track and street applications.")

    # Auto-detect specs based on keywords
    if 'wastegate' in t or 'wg40' in t or 'wg45' in t:
        specs.append("<b>Thermal Management:</b> Integrated liquid cooling ports and 360-degree actuator cap positioning.")
    if 'bov' in t or 'kompact' in t:
        specs.append("<b>Response:</b> Fast-acting piston mechanism prevents compressor surge under sudden throttle lift.")
    if 'fpr' in t or 'fuel pressure' in t:
        specs.append("<b>Ratio:</b> 1:1 manifold pressure reference for linear fuel delivery under boost.")
    
    # Detect Angle
    angle_match = re.search(r'(\d+)\s*(Degree|Deg|\°)', t, re.IGNORECASE)
    if angle_match:
        specs.append(f"<b>Flow Configuration:</b> {angle_match.group(1)}° profile for maximum fluid velocity in tight spaces.")

    spec_html = "<br><br><b>Technical Specifications:</b><br>• " + "<br>• ".join(specs)
    
    if clean_body:
        return f"{lead} {clean_body}{spec_html}"
    return f"{lead}{spec_html}"

# ---------------------------------------------------------
# Flexible Column Finder (Handles any CSV layout)
# ---------------------------------------------------------
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
        
        # Identify columns dynamically
        title_col = find_col(cols, ['title', 'name', 'product name', 'item name'])
        sku_col = find_col(cols, ['variation sku', 'sku', 'part number', 'item number'])
        price_col = find_col(cols, ['map_price', 'price', 'retail price', 'msrp', 'variant price'])
        img_col = find_col(cols, ['variation image link', 'image_url', 'image', 'picture', 'image src'])
        cat_col = find_col(cols, ['category', 'product type', 'type'])
        desc_col = find_col(cols, ['description', 'body', 'overview'])
        color_col = find_col(cols, ['variation name (color)', 'color', 'option1 value', 'variant'])
        vendor_col = find_col(cols, ['vendor', 'brand', 'manufacturer'])

        # Fallback if no explicit title column exists (assume first column)
        if not title_col:
            title_col = cols[0]

        grouped = df.groupby(title_col, sort=False)
        
        for title, group in grouped:
            title_str = str(title).strip()
            if not title_str or title_str.lower() in ['nan', 'none']:
                continue
            
            # Skip invalid stock entries
            first_sku = str(group.iloc[0][sku_col]).lower() if sku_col else ""
            if 'stock' in first_sku and 'out of stock' in title_str.lower():
                continue
                
            slug = re.sub(r'[^a-z0-9]+', '-', title_str.lower()).strip('-')
            first_row = group.iloc[0]
            
            # Extract basic data
            raw_cat = str(first_row[cat_col]) if cat_col else ""
            cat, subcat = auto_categorize(title_str, raw_cat)
            
            vendor_name = str(first_row[vendor_col]) if vendor_col else "Unknown"
            raw_desc = str(first_row[desc_col]) if desc_col else ""
            description = generate_smart_description(title_str, raw_desc, vendor_name)
            
            main_img = str(first_row[img_col]).strip() if img_col and pd.notna(first_row[img_col]) else ""
            main_sku = str(first_row[sku_col]).strip() if sku_col else ""

            # Build Variants & Prices
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
                "brand": vendor_name if vendor_name.lower() != 'nan' else "Aftermarket",
                "category": cat,
                "subcategory": subcat,
                "anSize": "Universal",
                "price": round(min(prices), 2) if prices else 0.0,
                "description": description,
                "image": main_img,
                "variants": variants
            }
            
            # Save the individual JSON
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
