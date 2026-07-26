const express = require('express');
const cors = require('cors');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const app = express();
app.use(express.json());
app.use(cors());

// 📦 INVENTORY DATABASE (In-memory store ready for vendor CSV updates)
let inventory = [
  { id: "MXP-300200016898", vendorSku: "GGT3582-JD-Z3", name: "GT3582 Street Billet Turbocharger", price: 375.30, stock: 10, category: "Turbos" },
  { id: "MXP-300200017093", vendorSku: "GGT3037GEN2-VL", name: "GT3076 / GT3037 T3 V-Band Turbocharger", price: 211.95, stock: 5, category: "Turbos" },
  { id: "MXP-300200016944", vendorSku: "GGT177275", name: "S300SX3 / S366 Twin Scroll Turbocharger", price: 407.70, stock: 12, category: "Turbos" },
  { id: "MXP-300200016896", vendorSku: "GGT3037-JD-Z3", name: "GT3076 / GT3037 Performance Turbocharger", price: 375.30, stock: 8, category: "Turbos" },
  { id: "MXP-300200016919", vendorSku: "GGT04E57-VL-Z3", name: "T04E T3/T4 Stage III Turbocharger", price: 184.95, stock: 15, category: "Turbos" },
  { id: "MXP-300200025602", vendorSku: "ZLQ-27-7-25_PP-25-18", name: "Universal Front Mount Intercooler Kit", price: 209.25, stock: 3, category: "Intercoolers" },
  { id: "MXP-300200024889", vendorSku: "ZLQ-60030076-TF-VL_PP-25-18", name: "Universal Performance Intercooler Kit", price: 284.85, stock: 7, category: "Intercoolers" },
  { id: "MXP-3002924451", vendorSku: "GGT04E-KIT-N-VL-Z2", name: "Universal T3/T4 T04E Complete Turbocharger Kit", price: 554.85, stock: 4, category: "Kits" },
  { id: "MXP-3002914100", vendorSku: "GGTLS2-K1", name: "5-Piece T3 T04E 420HP Turbo Upgrade Kit", price: 685.80, stock: 2, category: "Kits" }
];

// 1. GET ALL PRODUCTS / INVENTORY (Frontend pulls this to show live products & stock)
app.get('/api/products', (req, res) => {
  res.json(inventory);
});

// 2. BULK INVENTORY UPDATE (Endpoint to push vendor CSV inventory updates)
app.post('/api/inventory/update', (req, res) => {
  const newInventoryData = req.body; // Expects array of updated items/stock
  if (Array.isArray(newInventoryData)) {
    inventory = newInventoryData;
    return res.json({ message: "Inventory updated successfully", count: inventory.length });
  }
  res.status(400).json({ error: "Invalid inventory payload" });
});

// 3. CREATE STRIPE CHECKOUT SESSION (Validates stock before checkout)
app.post('/api/create-checkout-session', async (req, res) => {
  try {
    const { items } = req.body;

    const lineItems = items.map(cartItem => {
      const product = inventory.find(p => p.id === cartItem.id);
      
      if (!product) {
        throw new Error(`Product not found: ${cartItem.id}`);
      }
      if (product.stock < cartItem.qty) {
        throw new Error(`Sorry, ${product.name} is out of stock.`);
      }

      return {
        price_data: {
          currency: 'usd',
          product_data: {
            name: product.name,
            metadata: { vendorSku: product.vendorSku }
          },
          unit_amount: Math.round(product.price * 100), // Convert to cents for Stripe
        },
        quantity: cartItem.qty,
      };
    });

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: lineItems,
      mode: 'payment',
      shipping_address_collection: { allowed_countries: ['US'] },
      success_url: `${req.headers.origin}/?success=true`,
      cancel_url: `${req.headers.origin}/?canceled=true`,
    });

    res.json({ url: session.url });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
