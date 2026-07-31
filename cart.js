const CHECKOUT_API = 'https://murnan-checkout.murnanauto.workers.dev';

let inventory = [];
let cart = JSON.parse(localStorage.getItem('murnan_cart')) || [];

async function loadInventory() {
  inventory = [];

  // 1. Try loading legacy static products.json if present
  try {
    const res = await fetch('products.json', { cache: 'no-store' });
    if (res.ok) {
      const staticProds = await res.json();
      inventory.push(...staticProds);
    }
  } catch (err) {
    console.log('No static products.json found, loading Decap products...');
  }

  // 2. Fetch Decap CMS individual product JSON files from GitHub
  try {
    const ghRes = await fetch(`https://api.github.com/repos/reidawsome-maker/murnanauto/contents/content/products?t=${Date.now()}`);
    if (ghRes.ok) {
      const files = await ghRes.json();
      
      const jsonFiles = files.filter(file => file.name.endsWith('.json'));

      // Fetch all JSON files in parallel for fast loading
      const loadedProducts = await Promise.all(
        jsonFiles.map(async (file) => {
          const prodRes = await fetch(`${file.download_url}?t=${Date.now()}`);
          if (!prodRes.ok) return null;
          const item = await prodRes.json();

          return {
            id: file.name.replace('.json', ''), // Matches GitHub JSON filename
            sku: item.sku || 'N/A',
            name: item.title || item.name,
            price: parseFloat(item.price) || 0,
            weight: parseFloat(item.weight) || 0, // <-- MAPS WEIGHT FROM DECAP JSON
            stock: parseInt(item.stock, 10) || 0,
            image: item.image || '',
            description: item.description || '',
            category: item.category || 'Fluids',
            variants: item.variants || [] 
          };
        })
      );

      // Filter out failed fetches and avoid duplicate items
      for (const formattedProduct of loadedProducts) {
        if (formattedProduct && !inventory.some(p => p.id === formattedProduct.id)) {
          inventory.push(formattedProduct);
        }
      }
    }
  } catch (err) {
    console.error('Error fetching Decap CMS products:', err);
  }

  // Always sort inventory alphabetically
  inventory.sort((a, b) => (a.name || '').localeCompare(b.name || ''));

  return inventory;
}

function saveCart() {
  localStorage.setItem('murnan_cart', JSON.stringify(cart));
  updateCartUI();
}

function addToCart(id, variantOptions = null) {
  const product = inventory.find(p => p.id === id);
  if (!product) return;
  if (product.stock <= 0) { alert("This item is currently out of stock."); return; }

  // Use variant weight if selected, otherwise fallback to item weight
  let itemPrice = product.price;
  let itemWeight = product.weight;
  let itemId = product.id;

  if (variantOptions) {
    itemPrice = parseFloat(variantOptions.price) || itemPrice;
    itemWeight = parseFloat(variantOptions.weight) || itemWeight;
    itemId = `${product.id}-${variantOptions.sku || variantOptions.option}`;
  }

  const existing = cart.find(item => item.id === itemId);
  if (existing) {
    if (existing.qty + 1 > product.stock) {
      alert(`Only ${product.stock} units available.`);
      return;
    }
    existing.qty += 1;
  } else {
    cart.push({
      id: itemId,
      name: product.name + (variantOptions ? ` (${variantOptions.option})` : ''),
      price: itemPrice,
      weight: itemWeight, // <-- STORES WEIGHT IN CART
      qty: 1
    });
  }
  saveCart();
  const overlay = document.getElementById('cart-overlay');
  if (overlay) overlay.classList.add('open');
}

function removeFromCart(id) {
  cart = cart.filter(item => item.id !== id);
  saveCart();
}

function toggleCart() {
  const overlay = document.getElementById('cart-overlay');
  if (overlay) overlay.classList.toggle('open');
}

// Shipping Rate Calculation Rule
function calculateShipping(subtotal, totalWeight) {
  if (subtotal === 0) return 0;
  if (subtotal < 150) return 12.99; // Base standard shipping rate
  
  // Free shipping threshold logic
  if (subtotal >= 150 && totalWeight <= 35) return 0.00; // Free ground shipping
  if (totalWeight > 35 && totalWeight <= 60) return 29.99; // Tier 1 Heavy Freight (Dynalite/Drag Kits)
  return 49.99; // Tier 2 Heavy Freight (50+ lb twin-rotor/AERO kits)
}

function updateCartUI() {
  const countEl = document.getElementById('cart-count');
  const totalEl = document.getElementById('cart-total');
  const shippingEl = document.getElementById('cart-shipping');
  const listEl = document.getElementById('cart-items-list');

  const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);
  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  const totalWeight = cart.reduce((sum, item) => sum + ((item.weight || 0) * item.qty), 0);

  const shippingCost = calculateShipping(subtotal, totalWeight);
  const finalTotal = subtotal + shippingCost;

  if (countEl) countEl.textContent = totalQty;
  if (totalEl) totalEl.textContent = `$${finalTotal.toFixed(2)}`;

  // Display Shipping Breakdown line if element exists
  if (shippingEl) {
    if (cart.length === 0) {
      shippingEl.textContent = '$0.00';
    } else if (shippingCost === 0) {
      shippingEl.innerHTML = '<span style="color:#00e676;">FREE (Under 35 lbs)</span>';
    } else {
      shippingEl.textContent = `$${shippingCost.toFixed(2)} ${totalWeight > 35 ? '(Heavy Freight)' : ''}`;
    }
  }

  if (listEl) {
    if (cart.length === 0) {
      listEl.innerHTML = '<p style="color:var(--paper-dim); text-align:center; margin-top:40px;">Your cart is empty.</p>';
    } else {
      listEl.innerHTML = cart.map(item => `
        <div class="cart-item">
          <div>
            <div style="font-weight:600; font-size:0.9rem;">${item.name}</div>
            <div style="color:var(--paper-dim); font-size:0.8rem;">
              Qty: ${item.qty} × $${item.price.toFixed(2)} ${item.weight ? `(${item.weight * item.qty} lbs)` : ''}
            </div>
          </div>
          <button onclick="removeFromCart('${item.id}')" style="background:none; border:none; color:#ff5c5c; cursor:pointer; font-size:0.8rem;">Remove</button>
        </div>
      `).join('');
    }
  }
}

async function processCheckout() {
  if (cart.length === 0) { alert("Your cart is empty!"); return; }
  const btn = document.getElementById('cart-checkout-btn');
  if (btn) btn.textContent = "Loading Checkout...";
  try {
    const response = await fetch(CHECKOUT_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: cart })
    });
    const data = await response.json();
    if (data.url) {
      localStorage.removeItem('murnan_cart');
      window.location.href = data.url;
    } else {
      alert("Checkout error: " + (data.error || "Something went wrong"));
      if (btn) btn.textContent = "Proceed to Checkout";
    }
  } catch (err) {
    alert("Could not reach checkout. Please try again.");
    if (btn) btn.textContent = "Proceed to Checkout";
  }
}
