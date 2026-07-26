// Murnan Auto — shared cart logic
// Used by index.html and product.html so cart state stays consistent
// across pages (stored in the browser via localStorage).

const CHECKOUT_API = 'https://murnan-checkout.murnanauto.workers.dev';

let inventory = [];
let cart = JSON.parse(localStorage.getItem('murnan_cart')) || [];

async function loadInventory() {
  try {
    const res = await fetch('products.json', { cache: 'no-store' });
    inventory = await res.json();
  } catch (err) {
    console.error('Could not load products.json', err);
    inventory = [];
  }
  return inventory;
}

function saveCart() {
  localStorage.setItem('murnan_cart', JSON.stringify(cart));
  updateCartUI();
}

function addToCart(id) {
  const product = inventory.find(p => p.id === id);
  if (!product) return;
  if (product.stock <= 0) { alert("This item is currently out of stock."); return; }

  const existing = cart.find(item => item.id === id);
  if (existing) {
    if (existing.qty + 1 > product.stock) {
      alert(`Only ${product.stock} units available.`);
      return;
    }
    existing.qty += 1;
  } else {
    cart.push({ id: product.id, name: product.name, price: product.price, qty: 1 });
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

function updateCartUI() {
  const countEl = document.getElementById('cart-count');
  const totalEl = document.getElementById('cart-total');
  const listEl = document.getElementById('cart-items-list');
  const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);
  const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
  if (countEl) countEl.textContent = totalQty;
  if (totalEl) totalEl.textContent = `$${totalPrice.toFixed(2)}`;
  if (listEl) {
    if (cart.length === 0) {
      listEl.innerHTML = '<p style="color:var(--paper-dim); text-align:center; margin-top:40px;">Your cart is empty.</p>';
    } else {
      listEl.innerHTML = cart.map(item => `
        <div class="cart-item">
          <div>
            <div style="font-weight:600; font-size:0.9rem;">${item.name}</div>
            <div style="color:var(--paper-dim); font-size:0.8rem;">Qty: ${item.qty} × $${item.price.toFixed(2)}</div>
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
