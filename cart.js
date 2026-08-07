const CHECKOUT_API = 'https://murnan-checkout.murnanauto.workers.dev';

let inventory = [];
let cart = JSON.parse(localStorage.getItem('murnan_cart')) || [];

async function loadInventory() {
  inventory = [];

  try {
    // Direct fetch from root inventory.json
    const res = await fetch(`inventory.json?t=${Date.now()}`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        inventory = data.map(item => ({
          id: item.id || item.sku || 'N/A',
          sku: item.sku || item.id || 'N/A',
          name: item.title || item.name || 'Untitled Product',
          price: parseFloat(item.price) || 0,
          compare_price: parseFloat(item.compare_price || item.compare_at_price || item.msrp) || 0,
          weight: parseFloat(item.weight) || 0,
          stock: parseInt(item.stock, 10) || 0,
          image: item.image || '',
          description: item.description || '',
          category: item.category || 'Fluids',
          subcategory: item.subcategory || '',
          variants: item.variants || []
        }));
      }
    }
  } catch (err) {
    console.error('Error loading inventory.json:', err);
  }

  // Fallback to static products.json if inventory.json fails
  if (inventory.length === 0) {
    try {
      const res = await fetch('products.json', { cache: 'no-store' });
      if (res.ok) {
        const staticProds = await res.json();
        inventory.push(...staticProds);
      }
    } catch (err) {
      console.log('No static products.json fallback found.');
    }
  }

  // Always sort inventory alphabetically
  inventory.sort((a, b) => (a.name || '').localeCompare(b.name || ''));

  // Expose globally for index.html and product.html
  window.inventory = inventory;

  return inventory;
}

function saveCart() {
  localStorage.setItem('murnan_cart', JSON.stringify(cart));
  updateCartUI();
}

function addToCart(id, variantOptions = null) {
  const product = inventory.find(p => p.id === id || p.sku === id);
  if (!product) return;
  if (product.stock <= 0) { alert("This item is currently out of stock."); return; }

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

  const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);
  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  const totalWeight = cart.reduce((sum, item) => sum + ((item.weight || 0) * item.qty), 0);

  const shippingCost = calculateShipping(subtotal, totalWeight);
  const finalTotal = subtotal + shippingCost;

  if (countEl) countEl.textContent = totalQty;
  if (totalEl) totalEl.textContent = `$${finalTotal.toFixed(2)}`;

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
