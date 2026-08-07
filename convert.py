import pandas as pd
import json
import os
import re
import glob

# Ensure content/products directory exists WITHOUT clearing existing files
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
    desc = re.sub(r'Founded in 2008, ColorFittings.*?\.\s*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'Want to learn more.*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'Looking to complete your system\?.*', '', desc, flags=re.DOTALL | re.IGNORECASE)
    desc = re.sub(r'Explore our full range.*', '', desc, flags=re.DOTALL | re.IGNORECASE)

    desc = re.sub(r'\bwe\b', 'Color-Fittings', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\bour\b', 'the', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\bus\b', 'the manufacturer', desc, flags=re.IGNORECASE)

    paragraphs = [p.strip() for p in desc.split('\n') if p.strip()]
    return "<br><br>".join(paragraphs) if paragraphs else ""

def generate_turbosmart_desc(sku, title):
    t = title.lower()
    specs = [
        "<b>Brand & Engineering:</b> Genuine Turbosmart high-performance motorsport hardware.",
        "<b>Construction:</b> Precision CNC-machined billet aluminum housing with hard-anodized finish."
    ]
    
    if 'boost tee' in t or 'boost controller' in t:
        lead = f"The <b>{title}</b> utilizes Turbosmart's proven gated boost control system to bring boost on faster and prevent premature wastegate opening."
        specs.append("<b>Control Type:</b> Detent adjustment system for precise, leak-free boost adjustments.")
        specs.append("<b>Flow Efficiency:</b> Gated feature minimizes wastegate creep and improves turbo spool response.")
    elif 'eboost' in t:
        lead = f"The <b>{title}</b> is an advanced electronic boost controller capable of handling high boost levels with multiple boost group settings and boost-by-gear control."
        specs.append("<b>Pressure Rating:</b> Rated up to 40psi for high-output turbocharged applications.")
        specs.append("<b>Feature Set:</b> Peak hold display, auxiliary output control, and programmable boost curve ramps.")
    elif 'bov' in t or 'kompact' in t:
        lead = f"The <b>{title}</b> provides direct plug-and-play upgrade capability over weak factory diverter valves, holding extreme boost pressure without leaking."
        specs.append("<b>Porting:</b> Dual-port configuration allows partial recirculation for ECU stability with atmospheric blow-off sound.")
        specs.append("<b>Response:</b> Fast-acting piston mechanism prevents compressor surge under sudden throttle lift.")
    elif 'fpr' in t or 'fuel pressure' in t:
        an_size = "-6AN" if "fpr6" in t else ("-8AN" if "fpr8" in t else ("-10AN" if "fpr10" in t else "1/8 NPT"))
        lead = f"The <b>{title}</b> delivers dead-accurate fuel pressure regulation across high-horsepower EFI applications running pump gas, race gas, or E85."
        specs.append(f"<b>Porting & Fittings:</b> Equipped for {an_size} high-flow feed and return lines with integrated gauge port.")
        specs.append("<b>Ratio:</b> 1:1 manifold pressure reference for linear fuel delivery under boost.")
    elif 'wg40' in t or 'wg45' in t or 'wastegate' in t:
        size = "40mm" if "wg40" in t else "45mm"
        lead = f"The <b>{title}</b> represents Turbosmart's GenV thermal engineering, featuring modular actuator housing and maximum flow efficiency."
        specs.append(f"<b>Valve Size:</b> {size} high-temp stainless steel valve assembly.")
        specs.append("<b>Cooling & Rotation:</b> Integrated liquid cooling ports and 360-degree actuator cap positioning.")
    else:
        lead = f"The <b>{title}</b> is engineered for extreme durability and precise pressure management in competition fluid and boost systems."

    spec_block = "<br><br><b>Technical Specifications:</b><br>• " + "<br>• ".join(specs)
    return f"{lead}{spec_block}"

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

    spec_block = "<br><br><b>Technical Specifications:</b><br>• " + "<br>• ".join(specs)
    return f"{lead}{spec_block}"

# Scan all CSV files in root and subdirectories
csv_files = glob.glob('**/*.csv', recursive=True)
print(f"Scanning repository CSV files: {csv_files}")

for csv_path in csv_files:
    try:
        temp_df = pd.read_csv(csv_path)
        cols = [str(c).lower().strip() for c in temp_df.columns]
        
        # 1. Turbosmart Format Matching
        if 'vendor' in cols and 'map_price' in cols:
            print(f"--> Building Turbosmart Catalog from: {csv_path}")
            valid_df = temp_df.dropna(subset=['SKU', 'Title'])
            valid_df = valid_df[~valid_df['SKU'].astype(str).str.lower().str.contains('stock')]
            
            for _, row in valid_df.iterrows():
                sku = str(row['SKU']).strip()
                title = str(row['Title']).strip()
                slug = re.sub(r'[^a-z0-9]+', '-', f"turbosmart-{sku}-{title}".lower()).strip('-')
                
                map_price = safe_float(row.get('MAP_Price'), safe_float(row.get('MSRP')))
                msrp_price = safe_float(row.get('MSRP'), map_price)
                
                t_lower = title.lower()
                if 'boost' in t_lower:
                    cat, subcat = 'Boost Controllers', 'Manual & Electronic Controllers'
                elif 'bov' in t_lower or 'kompact' in t_lower:
                    cat, subcat = 'Blow Off Valves', 'BOV & Diverter Valves'
                elif 'fpr' in t_lower or 'fuel pressure' in t_lower:
                    cat, subcat = 'Fuel Systems', 'Fuel Pressure Regulators'
                elif 'wg40' in t_lower or 'wg45' in t_lower or 'wastegate' in t_lower:
                    cat, subcat = 'Turbos', 'External Wastegates'
                elif 'gauge' in t_lower:
                    cat, subcat = 'Gauges', 'Boost & Pressure Gauges'
                else:
                    cat, subcat = 'Performance Hardware', 'Turbosmart'

                desc = generate_turbosmart_desc(sku, title)
                img = str(row.get('Image_URL', '')).strip() if pd.notna(row.get('Image_URL')) else ""

                product = {
                    "id": slug,
                    "name": title,
                    "title": title,
                    "sku": sku,
                    "brand": "Turbosmart",
                    "category": cat,
                    "subcategory": subcat,
                    "anSize": "Universal",
                    "price": round(map_price, 2),
                    "msrp": round(msrp_price, 2),
                    "description": desc,
                    "image": img,
                    "variants": [{
                        "name": "Standard",
                        "sku": sku,
                        "price": round(map_price, 2),
                        "image": img,
                        "stock": 10
                    }]
                }
                with open(f'content/products/{slug}.json', 'w') as f:
                    json.dump(product, f, indent=2)

        # 2. General Fittings / Fuel Hardware / Custom Vendor CSV Matching
        elif any(k in cols for k in ['title', 'variation sku', 'variation name (color)', 'price', 'name']):
            title_col = None
            for c in ['Title', 'title', 'Name', 'name', 'Product Name']:
                if c in temp_df.columns:
                    title_col = c
                    break
            if not title_col:
                title_col = temp_df.columns[0]
                
            print(f"--> Building Catalog from: {csv_path}")
            grouped = temp_df.groupby(title_col, sort=False)
            
            for title, group in grouped:
                title_str = str(title).strip()
                if not title_str or title_str.lower() in ['nan', 'title']:
                    continue
                
                slug = re.sub(r'[^a-z0-9]+', '-', title_str.lower()).strip('-')
                first = group.iloc[0]
                
                variants = []
                prices = []
                for _, row in group.iterrows():
                    p_val = safe_float(row.get('Price', row.get('price', row.get('MSRP', 0))))
                    prices.append(p_val)
                    c_name = str(row.get('Variation name (color)', row.get('color', row.get('Option1 Value', 'Standard'))))
                    c_name = re.sub(r'\s*\[\+\$[0-9\.]+\]', '', c_name).strip()
                    sku_val = str(row.get('Variation SKU', row.get('sku', row.get('SKU', '')))).strip()
                    img_val = str(row.get('Variation Image Link', row.get('image', row.get('Image_URL', '')))).strip()
                    
                    variants.append({
                        "name": c_name if c_name and c_name.lower() != 'nan' else "Standard",
                        "sku": sku_val,
                        "price": round(p_val, 2),
                        "image": img_val,
                        "stock": 10
                    })
                
                min_price = min(prices) if prices else 0.0
                raw_desc_val = first.get('Description', first.get('description', ''))
                desc = generate_colorfittings_desc(title_str, raw_desc_val)
                cat_val = str(first.get('Category', first.get('category', 'AN Fittings')))
                img_main = str(first.get('Variation Image Link', first.get('image', first.get('Image_URL', '')))).strip()
                
                product = {
                    "id": slug,
                    "name": title_str,
                    "title": title_str,
                    "sku": str(first.get('Variation SKU', first.get('sku', first.get('SKU', '')))).strip(),
                    "category": cat_val if cat_val and cat_val.lower() != 'nan' else 'AN Fittings',
                    "price": round(min_price, 2),
                    "description": desc,
                    "image": img_main,
                    "variants": variants
                }
                with open(f'content/products/{slug}.json', 'w') as f:
                    json.dump(product, f, indent=2)

    except Exception as e:
        print(f"Error processing {csv_path}: {e}")

# 3. ABSOLUTE CRITICAL STEP: Build inventory.json by scanning ALL JSON files in content/products/
# This ensures ANY existing product (Turbosmart, ColorFittings, Maxpeedingrods, Evil Energy, APG, manual JSONs) is retained.
all_products = []
if os.path.exists('content/products'):
    for fname in os.listdir('content/products'):
        if fname.endswith('.json'):
            filepath = os.path.join('content/products', fname)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    all_products.append(data)
            except Exception as e:
                print(f"Error loading {fname}: {e}")

with open('inventory.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"Compilation Complete: {len(all_products)} total products saved to inventory.json.")
