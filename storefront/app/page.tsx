"use client";
import { useState } from "react";
import Link from "next/link";
import {
  ShoppingCart, Star, Zap, Shield, Package,
  TrendingUp, ArrowRight, CheckCircle, Clock, Tag
} from "lucide-react";
import { formatCurrency } from "@/lib/utils";

/* ─── Product Data ─────────────────────────────────────────── */
const PRODUCTS = [
  {
    id: "prod-001",
    name: "ShopFlow Pro Plan",
    tagline: "Complete e-commerce suite for growing businesses",
    price: 4999,
    originalPrice: 7999,
    category: "Subscription",
    rating: 4.8,
    reviews: 2341,
    badge: "BESTSELLER",
    badgeColor: "badge-success",
    emoji: "🚀",
    features: [
      "Unlimited products",
      "Advanced analytics",
      "Priority support 24/7",
      "Custom domain + SSL",
    ],
    gradient: "from-indigo-500/20 to-purple-500/20",
    borderColor: "rgba(99, 102, 241, 0.3)",
    iconColor: "#6366f1",
  },
  {
    id: "prod-002",
    name: "AI Inventory Manager",
    tagline: "Predict stockouts before they happen with ML",
    price: 2499,
    originalPrice: 3999,
    category: "Add-on",
    rating: 4.6,
    reviews: 891,
    badge: "NEW",
    badgeColor: "badge-info",
    emoji: "🧠",
    features: [
      "AI demand forecasting",
      "Auto reorder alerts",
      "Supplier management",
      "99.2% accuracy rate",
    ],
    gradient: "from-cyan-500/20 to-blue-500/20",
    borderColor: "rgba(34, 211, 238, 0.3)",
    iconColor: "#22d3ee",
  },
  {
    id: "prod-003",
    name: "Payment Shield Plus",
    tagline: "Enterprise fraud detection with zero false positives",
    price: 1999,
    originalPrice: 2999,
    category: "Security",
    rating: 4.9,
    reviews: 1204,
    badge: "HOT",
    badgeColor: "badge-error",
    emoji: "🔐",
    features: [
      "ML fraud detection",
      "Chargeback protection",
      "PCI DSS compliant",
      "Real-time alerts",
    ],
    gradient: "from-emerald-500/20 to-teal-500/20",
    borderColor: "rgba(16, 185, 129, 0.3)",
    iconColor: "#10b981",
  },
];

/* ─── Cart State (simple localStorage) ──────────────────────── */
function useCart() {
  const addToCart = (product: typeof PRODUCTS[0]) => {
    const cart = JSON.parse(localStorage.getItem("shopflow-cart") || "[]");
    const existing = cart.findIndex((i: { id: string }) => i.id === product.id);
    if (existing >= 0) {
      cart[existing].qty += 1;
    } else {
      cart.push({ ...product, qty: 1 });
    }
    localStorage.setItem("shopflow-cart", JSON.stringify(cart));
    return true;
  };
  return { addToCart };
}

/* ─── Toast ──────────────────────────────────────────────────── */
function Toast({ message, type, onClose }: { message: string; type: "success" | "error"; onClose: () => void }) {
  return (
    <div className={type === "success" ? "toast-success" : "toast-error"}
      role="alert" aria-live="assertive">
      <div className="flex-shrink-0 mt-0.5">
        {type === "success"
          ? <CheckCircle className="w-5 h-5 text-emerald-400" />
          : <Zap className="w-5 h-5 text-red-400" />}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-white">{message}</p>
      </div>
      <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors ml-2 text-lg leading-none">×</button>
    </div>
  );
}

/* ─── Product Card ───────────────────────────────────────────── */
function ProductCard({ product, onAddToCart }: { product: typeof PRODUCTS[0]; onAddToCart: (p: typeof PRODUCTS[0]) => void }) {
  const [adding, setAdding] = useState(false);

  const handleAdd = async () => {
    setAdding(true);
    await new Promise(r => setTimeout(r, 400));
    onAddToCart(product);
    setAdding(false);
  };

  const discount = Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100);

  return (
    <article
      id={`product-${product.id}`}
      className="product-card group animate-slide-up"
      style={{
        background: `linear-gradient(135deg, ${product.gradient.replace("from-", "").replace("to-", "").replace("/20", "").split(" ").map(c => `rgba(${hexToRgb(product.iconColor)}, 0.04)`)[0]}, rgba(0,0,0,0))`,
      }}
    >
      {/* Badge + Emoji */}
      <div className="flex items-start justify-between">
        <span className={product.badgeColor}>
          {product.badge}
        </span>
        <span className="text-4xl">{product.emoji}</span>
      </div>

      {/* Product info */}
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1 flex items-center gap-1">
          <Tag className="w-3 h-3" />
          {product.category}
        </p>
        <h2 className="text-lg font-bold text-white">{product.name}</h2>
        <p className="text-sm text-gray-400 mt-1">{product.tagline}</p>
      </div>

      {/* Rating */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-0.5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              className="w-3.5 h-3.5"
              fill={i < Math.floor(product.rating) ? "#fbbf24" : "transparent"}
              style={{ color: "#fbbf24" }}
            />
          ))}
        </div>
        <span className="text-xs text-gray-400">{product.rating} ({product.reviews.toLocaleString()} reviews)</span>
      </div>

      {/* Features */}
      <ul className="space-y-1.5">
        {product.features.map((f) => (
          <li key={f} className="flex items-center gap-2 text-xs text-gray-300">
            <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" style={{ color: product.iconColor }} />
            {f}
          </li>
        ))}
      </ul>

      {/* Price */}
      <div className="flex items-end justify-between mt-auto">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-white">{formatCurrency(product.price)}</span>
            <span className="text-xs font-medium px-1.5 py-0.5 rounded-md"
              style={{ background: "rgba(16,185,129,0.12)", color: "#34d399", border: "1px solid rgba(16,185,129,0.2)" }}>
              -{discount}%
            </span>
          </div>
          <span className="text-xs text-gray-500 line-through">{formatCurrency(product.originalPrice)}</span>
        </div>
        <span className="text-xs text-gray-500 flex items-center gap-1">
          <Clock className="w-3 h-3" /> /month
        </span>
      </div>

      {/* Add to Cart Button */}
      <button
        id={`add-to-cart-${product.id}`}
        onClick={handleAdd}
        disabled={adding}
        className="btn-primary w-full mt-2"
        style={adding ? { opacity: 0.7 } : {}}
        aria-label={`Add ${product.name} to cart`}
      >
        {adding ? (
          <>
            <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Adding...
          </>
        ) : (
          <>
            <ShoppingCart className="w-4 h-4" />
            Add to Cart
          </>
        )}
      </button>
    </article>
  );
}

// Helper to avoid TS error — not actually needed but keeps hex colors consistent
function hexToRgb(_hex: string) { return "99, 102, 241"; }

/* ─── Main Page ──────────────────────────────────────────────── */
export default function HomePage() {
  const { addToCart } = useCart();
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const handleAddToCart = (product: typeof PRODUCTS[0]) => {
    addToCart(product);
    setToast({ message: `${product.name} added to cart!`, type: "success" });
    setTimeout(() => setToast(null), 3500);
  };

  return (
    <>
      {/* Toast */}
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}

      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Hero */}
        <section className="text-center mb-16 animate-fade-in">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium mb-6"
            style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#a5b4fc" }}>
            <TrendingUp className="w-3.5 h-3.5" />
            Over 50,000 businesses trust ShopFlow
          </div>
          <h1 className="text-5xl font-bold text-white mb-4 leading-tight">
            The smarter way to<br />
            <span style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6, #22d3ee)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              run your store
            </span>
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
            Premium e-commerce tools with AI-powered insights. Zero complexity, maximum growth.
          </p>

          <div className="flex items-center justify-center gap-4">
            <Link href="/cart" id="view-cart-hero" className="btn-primary">
              <ShoppingCart className="w-4 h-4" />
              View Cart
            </Link>
            <Link href="/orders" id="view-orders-hero" className="btn-secondary">
              <Package className="w-4 h-4" />
              My Orders
            </Link>
          </div>
        </section>

        {/* Trust badges */}
        <div className="flex flex-wrap items-center justify-center gap-8 mb-14 animate-fade-in">
          {[
            { icon: Shield, text: "PCI DSS Compliant" },
            { icon: Zap, text: "99.9% Uptime SLA" },
            { icon: Star, text: "4.8★ Average Rating" },
            { icon: Clock, text: "24/7 Support" },
          ].map(({ icon: Icon, text }) => (
            <div key={text} className="flex items-center gap-2 text-gray-400 text-sm">
              <Icon className="w-4 h-4" style={{ color: "#6366f1" }} />
              {text}
            </div>
          ))}
        </div>

        {/* Products Grid */}
        <section id="products">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white">Featured Plans</h2>
              <p className="text-sm text-gray-500 mt-1">All plans include 14-day free trial. No credit card required.</p>
            </div>
            <span className="badge-info">{PRODUCTS.length} plans available</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PRODUCTS.map((product, i) => (
              <div key={product.id} style={{ animationDelay: `${i * 100}ms` }}>
                <ProductCard product={product} onAddToCart={handleAddToCart} />
              </div>
            ))}
          </div>
        </section>

        {/* Bottom CTA */}
        <section className="mt-20 text-center glass p-12 animate-fade-in"
          style={{ background: "rgba(99,102,241,0.04)", borderColor: "rgba(99,102,241,0.15)" }}>
          <h3 className="text-2xl font-bold text-white mb-3">Ready to scale?</h3>
          <p className="text-gray-400 mb-6 max-w-lg mx-auto">
            Join 50,000+ businesses already using ShopFlow to power their e-commerce operations.
          </p>
          <Link href="/cart" id="get-started-cta" className="btn-primary">
            Get started today
            <ArrowRight className="w-4 h-4" />
          </Link>
        </section>
      </div>
    </>
  );
}
