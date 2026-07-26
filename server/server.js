const express = require('express');
const cors = require('cors');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const app = express();
app.use(express.json());
app.use(cors());

// Your Curated Maxpeeding Products
const products = [
  { id: "MXP-300200016898", vendorSku: "GGT3582-JD-Z3", name: "GT3582 Street Billet Turbocharger", price: 37530, category: "Turbos" },
  { id: "MXP-300200017093", vendorSku: "GGT3037GEN2-VL", name: "GT3076 / GT3037 T3 V-Band Turbocharger", price: 21195, category: "Turbos" },
  { id: "MXP-300200016944", vendorSku: "GGT177275", name: "S300SX3 / S366 Twin Scroll Turbocharger", price: 40770, category: "Turbos" },
  { id: "MXP-300200016896", vendorSku: "GGT3037-JD-Z3", name: "GT3076 / GT3037 Performance Turbocharger", price: 37530, category: "Turbos" },
  { id: "MXP-300200016919", vendorSku: "GGT04E57-VL-Z3", name: "T04E T3/T4 Stage III Turbocharger", price: 18495, category: "Turbos" },
  { id: "MXP-300200025602", vendorSku: "ZLQ-27-7-25_PP-25-18", name: "Universal Front Mount Intercooler Kit", price: 20925, category: "Intercoolers" },
  { id: "MXP-300200024889", vendorSku: "ZLQ-60030076-TF-VL_PP-25-18", name: "Universal Performance Intercooler Kit", price: 28485, category: "Intercoolers" },
  { id: "MXP-3002924451", vendorSku: "GGT04E-KIT-N-VL-Z2", name: "Universal T3/T4 T04E Complete Turbocharger Kit", price: 55485, category: "Kits" },
  { id: "MXP-3002914100", vendorSku: "GGTLS2-K1", name: "5-Piece T3 T04E 420HP Turbo Upgrade Kit", price: 68580, category: "Kits" }
];

// 1. API Route to Fetch Products
app.get('/api/products', (req, res) => {
  res.json(products);
});

// 2. API Route to Create Stripe Checkout Session
app.post('/api/create-checkout-session', async (req, res) => {
  try {
    const { items } = req.body; // Expects [{ id: "MXP-...", quantity: 1 }]

    const lineItems = items.map(item => {
      const product = products.find(p => p.id === item.id);
      if (!product) throw new Error(`Product not found: ${item.id}`);

      return {
        price_data: {
          currency: 'usd',
          product_data: {
            name: product.name,
            metadata: { vendorSku: product.vendorSku }
          },
          unit_amount: product.price, // Stripe uses cents ($375.30 = 37530)
        },
        quantity: item.quantity,
      };
    });

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: lineItems,
      mode: 'payment',
      shipping_address_collection: { allowed_countries: ['US'] },
      success_url: `${req.headers.origin}/success.html`,
      cancel_url: `${req.headers.origin}/cart.html`,
    });

    res.json({ url: session.url });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
