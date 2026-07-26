const express = require('express');
const cors = require('cors');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// 📦 LIVE INVENTORY BACKEND CATALOG
// Map categories to: Turbos, Intercoolers, Kits, Headers, Mufflers, Coilovers, etc.
let inventory = [
  {
    id: "MXP-300200016898",
    vendorSku: "GGT3582-JD-Z3",
    name: "GT3582 Street Billet Turbocharger",
    price: 375.30,
    stock: 12,
    category: "Turbos"
  },
  {
    id: "MXP-300200016899",
    vendorSku: "GGT3037GEN2-VL",
    name: "GT3076 / GT3037 T3 V-Band Turbocharger",
    price: 211.95,
    stock: 8,
    category: "Turbos"
  },
  {
    id: "MXP-300200016900",
    vendorSku: "GGT177275",
    name: "S300SX3 / S366 Twin Scroll Turbocharger",
    price: 407.70,
    stock: 5,
    category: "Turbos"
  },
  {
    id: "MXP-300200016901",
    vendorSku: "GGT3037-JD-Z3",
    name: "GT3076 / GT3037 Performance Turbocharger",
    price: 375.30,
    stock: 15,
    category: "Turbos"
  },
  {
    id: "MXP-300200016902",
    vendorSku: "GGT04E57-VL-Z3",
    name: "TO4E T3/T4 Stage III Turbocharger",
    price: 184.95,
    stock: 10,
    category: "Turbos"
  },
  {
    id: "MXP-300200016903",
    vendorSku: "ZLQ-27-7-25_PP-25-18",
    name: "Universal Front Mount Intercooler Kit",
    price: 209.25,
    stock: 6,
    category: "Intercoolers"
  },
  {
    id: "MXP-300200016904",
    vendorSku: "ZLQ-60030076-TF-VL_PP-25-18",
    name: "Universal Performance Intercooler Kit",
    price: 284.85,
    stock: 4,
    category: "Intercoolers"
  },
  {
    id: "MXP-300200016905",
    vendorSku: "GGT04E-KIT-N-VL-Z2",
    name: "Universal T3/T4 TO4E Complete Turbocharger Kit",
    price: 554.85,
    stock: 3,
    category: "Kits"
  },
  {
    id: "MXP-300200016906",
    vendorSku: "GGTLS2-K1",
    name: "5-Piece T3 TO4E 420HP Turbo Upgrade Kit",
    price: 320.00,
    stock: 7,
    category: "Kits"
  }
];

// 1. GET ALL PRODUCTS ENDPOINT
app.get('/api/products', (req, res) => {
  res.json(inventory);
});

// 2. CREATE STRIPE CHECKOUT SESSION ENDPOINT
app.post('/api/create-checkout-session', async (req, res) => {
  try {
    const { items } = req.body;

    if (!items || items.length === 0) {
      return res.status(400).json({ error: "Cart is empty" });
    }

    // Convert items into Stripe line_items format
    const lineItems = items.map(item => {
      // Find matching item in backend inventory to prevent price tampering
      const storeItem = inventory.find(p => p.id === item.id);
      const unitPrice = storeItem ? storeItem.price : item.price;

      return {
        price_data: {
          currency: 'usd',
          product_data: {
            name: item.name,
          },
          // Stripe requires price in cents as an integer
          unit_amount: Math.round(unitPrice * 100),
        },
        quantity: item.qty,
      };
    });

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: lineItems,
      mode: 'payment',
      // Automatic Kansas state and local sales tax collection
      automatic_tax: { enabled: true },
      shipping_address_collection: {
        allowed_countries: ['US'],
      },
      success_url: 'https://murnanauto.store/?status=success',
      cancel_url: 'https://murnanauto.store/?status=cancelled',
    });

    res.json({ url: session.url });
  } catch (error) {
    console.error("Stripe Error:", error.message);
    res.status(500).json({ error: error.message });
  }
});

// Start Server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Murnan Auto backend running on port ${PORT}`);
});
