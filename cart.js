const CHECKOUT_API = 'https://murnan-checkout.murnanauto.workers.dev';

let inventory = [];
let cart = [];

// Safely load local storage cart without crashing on stale formats
try {
  const saved = localStorage.getItem('murnan_cart');
  if (saved) {
    cart = JSON.parse(saved);
    if (!Array.isArray(cart)) cart = [];
  }
} catch (e) {
  cart = [];
}

async function loadInventory() {
  inventory = [];

  // 1. Primary: Load root inventory.json (Fast path)
  try {
    const res = await fetch('inventory.json', { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        inventory = data;
        window.inventory = inventory;
        return inventory;
      }
    }
  } catch (err) {
    console.log('inventory.json fallback to Decap CMS folder...');
  }

  // 2. Secondary Fallback: Fetch individual JSON files from GitHub API
  try {
    const ghRes = await fetch(`https://api.github.com/repos/reidawsome-maker/murnanauto/contents/content/products?t=${Date.now()}`);
    if (ghRes.ok) {
      const files = await ghRes.json();
      const jsonFiles = files.filter(file => file.name.endsWith('.json'));

      const loadedProducts = await Promise.all(
        jsonFiles.map(async (file) => {
          const prodRes = await fetch(`${file.download_url}?t=${Date.now()}`);
          if (!prodRes.ok) return null;
          const item = await prodRes.json();

          return {
            id: file.name.replace('.json', ''),
            sku: item.sku || 'N/A',
            name: item.title || item.name,
            price: parseFloat(item.price) || 0,
            compare_price: parseFloat(item.compare_price || item.compare_at_price || item.msrp) || 0,
            weight: parseFloat(item.weight) || 0,
            stock: parseInt(item.stock, 10) || 10,
            image: item.image || '',
            description: item.description || '',
            category: item.category || 'ANFittings',
            subcategory: item.subcategory || '',
            anSize: item.anSize || '',
            tags: item.tags || [],
            variants: item.variants || []
          };
        })
      );

      for (const formattedProduct of loadedProducts) {
        if (formattedProduct && !inventory.some(p => p.id === formattedProduct.id)) {
          inventory.push(formattedProduct);
        }
      }
    }
  } catch (err) {
    console.error('Error fetching CMS products:', err);
  }

  inventory.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  window.inventory = inventory;
  return inventory;
}

function saveCart() {
  localStorage.setItem('murnan_cart', JSON.stringify(cart));
  updateCartUI();
}

function addToCart(id, variantOptions = null) {
  const product = (window.inventory || inventory).find(p => p.id === id);
  if (!product) {
    alert("Product not found in live inventory.");
    return;
  }

  let itemPrice = product.price;
  let itemWeight = product.weight;
  let itemId = product.id;
  let optionName = '';

  if (variantOptions) {
    itemPrice = parseFloat(variantOptions.price) || itemPrice;
    itemWeight = parseFloat(variantOptions.weight) || itemWeight;
    optionName = variantOptions.option || '';
    itemId = `${product.id}-${variantOptions.sku || optionName}`;
  }

  const existing = cart.find(item => item.id === itemId);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({
      id: itemId,
      baseId: product.id,
      name: (product.name || product.title) + (optionName ? ` (${optionName})` : ''),
      price: itemPrice,
      weight: itemWeight,
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

function calculateShipping(subtotal, totalWeight) {
  if (subtotal === 0) return 0;
  if (subtotal < 150) return 12.99;
  if (subtotal >= 150 && totalWeight <= 35) return 0.00;
  if (totalWeight > 35 && totalWeight <= 60) return 29.99;
  return 49.99;
}

function updateCartUI() {
  const countEl = document.getElementById('cart-count');
  const totalEl = document.getElementById('cart-total');
  const shippingEl = document.getElementById('cart-shipping');
  const listEl = document.getElementById('cart-items-list');

  const totalQty = cart.reduce((sum, item) => sum + (item.qty || 0), 0);
  const subtotal = cart.reduce((sum, item) => sum + ((item.price || 0) * (item.qty || 0)), 0);
  const totalWeight = cart.reduce((sum, item) => sum + (((item.weight || 0) * (item.qty || 0))), 0);

  const shippingCost = calculateShipping(subtotal, totalWeight);
  const finalTotal = subtotal + shippingCost;

  if (countEl) countEl.textContent = totalQty;
  if (totalEl) totalEl.textContent = `$${finalTotal.toFixed(2)}`;

  if (shippingEl) {
    if (cart.length === 0) {
      shippingEl.textContent = '$0.00';
    } else if (shippingCost === 0) {
      shippingEl.innerHTML = '<span style="color:#4ADE80;">FREE (Under 35 lbs)</span>';
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
            <div style="font-weight:600; font-size:0.9rem; color: var(--paper);">${item.name}</div>
            <div style="color:var(--paper-dim); font-size:0.8rem; margin-top: 2px;">
              Qty: ${item.qty} × $${(item.price || 0).toFixed(2)} ${item.weight ? `(${item.weight * item.qty} lbs)` : ''}
            </div>
          </div>
          <button onclick="removeFromCart('${item.id}')" style="background:none; border:none; color:#ff5c5c; cursor:pointer; font-size:0.8rem; font-weight:600;">Remove</button>
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
