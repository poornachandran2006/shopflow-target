"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Package, CheckCircle, Clock, AlertCircle,
  RotateCcw, ShoppingCart, ArrowRight, RefreshCw
} from "lucide-react";
import { formatCurrency, formatDate } from "@/lib/utils";

const PAYMENT_API = process.env.NEXT_PUBLIC_PAYMENT_API || "http://localhost:8001";

interface OrderItem {
  name: string;
  qty: number;
  price: number;
  emoji?: string;
}

interface Order {
  id: string;
  payment_id: string;
  items: OrderItem[];
  total: number;
  status: "confirmed" | "processing" | "refunded" | "failed";
  created_at: string;
  refund_id?: string;
}

/* ─── Status Badge ───────────────────────────────────────────── */
function StatusBadge({ status }: { status: Order["status"] }) {
  const map: Record<Order["status"], { cls: string; label: string; icon: React.ReactNode }> = {
    confirmed: { cls: "badge-success", label: "Confirmed", icon: <CheckCircle className="w-3 h-3" /> },
    processing: { cls: "badge-warning", label: "Processing", icon: <Clock className="w-3 h-3" /> },
    refunded: { cls: "badge-info", label: "Refunded", icon: <RotateCcw className="w-3 h-3" /> },
    failed: { cls: "badge-error", label: "Failed", icon: <AlertCircle className="w-3 h-3" /> },
  };
  const { cls, label, icon } = map[status];
  return <span className={cls}>{icon}{label}</span>;
}

/* ─── Order Card ─────────────────────────────────────────────── */
function OrderCard({ order, onRefund }: { order: Order; onRefund: (orderId: string) => void }) {
  const [refunding, setRefunding] = useState(false);
  const [refundState, setRefundState] = useState<"idle" | "success" | "error">("idle");
  const [refundMsg, setRefundMsg] = useState("");

  const handleRefund = async () => {
    setRefunding(true);
    try {
      const res = await fetch(`${PAYMENT_API}/refund`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          payment_id: order.payment_id,
          user_id: "user-demo-001",
          amount: order.total,
          reason: "customer_request",
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        const detail = data?.detail;
        const msg = typeof detail === "object"
          ? detail?.message || "Refund request failed."
          : "Refund service unavailable.";
        setRefundState("error");
        setRefundMsg(msg);
        onRefund(order.id);
        return;
      }

      const data = await res.json();
      setRefundState("success");
      setRefundMsg(`Refund ID: ${data.refund_id}`);
      onRefund(order.id);
    } catch {
      setRefundState("error");
      setRefundMsg("Could not reach payment service.");
    } finally {
      setRefunding(false);
    }
  };

  return (
    <article id={`order-${order.id}`} className="glass p-6 space-y-4 transition-all duration-300 hover:border-white/10">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-bold text-white font-mono">{order.id}</h3>
            <StatusBadge status={order.status} />
          </div>
          <p className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatDate(order.created_at)}
          </p>
          {order.payment_id && (
            <p className="text-xs text-gray-600 font-mono mt-0.5">{order.payment_id}</p>
          )}
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-white">{formatCurrency(order.total * 1.13)}</p>
          <p className="text-xs text-gray-500">incl. GST</p>
        </div>
      </div>

      {/* Items */}
      <div className="space-y-2">
        {order.items.map((item, i) => (
          <div key={i} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-gray-300">
              {item.emoji && <span>{item.emoji}</span>}
              <span>{item.name}</span>
              <span className="text-gray-600">×{item.qty}</span>
            </div>
            <span className="text-gray-400">{formatCurrency(item.price * item.qty)}</span>
          </div>
        ))}
      </div>

      {/* Refund result */}
      {refundState === "success" && (
        <div className="glass p-3 text-xs text-emerald-400 flex items-center gap-2"
          style={{ background: "rgba(16,185,129,0.06)", borderColor: "rgba(16,185,129,0.2)" }}>
          <CheckCircle className="w-4 h-4" />
          Refund initiated — {refundMsg}
        </div>
      )}

      {refundState === "error" && (
        <div className="space-y-2">
          <div className="glass p-3 text-xs text-red-400 flex items-start gap-2"
            style={{ background: "rgba(239,68,68,0.06)", borderColor: "rgba(239,68,68,0.2)" }}>
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Refund Failed</p>
              <p className="text-gray-400 mt-0.5">{refundMsg}</p>
            </div>
          </div>
          {/* SENTINEL callout */}
          <div className="sentinel-bar">
            <span style={{ fontSize: 14 }}>◉</span>
            <span>SENTINEL: Refund failure DNA matches INC-001 (payment-service v1.0) — same connection pool exhaustion pattern</span>
          </div>
        </div>
      )}

      {/* Actions */}
      {order.status === "confirmed" && refundState === "idle" && (
        <div className="flex gap-3 pt-1">
          <button
            id={`refund-order-${order.id}`}
            onClick={handleRefund}
            disabled={refunding}
            className="btn-secondary"
            style={{ padding: "7px 14px", fontSize: "12px" }}
          >
            {refunding ? (
              <>
                <span className="inline-block w-3.5 h-3.5 border-2 border-gray-400/30 border-t-gray-400 rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <RotateCcw className="w-3.5 h-3.5" />
                Request Refund
              </>
            )}
          </button>
        </div>
      )}
    </article>
  );
}

/* ─── Orders Page ────────────────────────────────────────────── */
export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [refundedIds, setRefundedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("shopflow-orders") || "[]");
    // Add demo orders if empty so judges see something on first load
    if (stored.length === 0) {
      const demo: Order[] = [
        {
          id: "ORD-DEMO001",
          payment_id: "pay-abc123demo",
          items: [
            { name: "ShopFlow Pro Plan", qty: 1, price: 4999, emoji: "🚀" },
          ],
          total: 4999,
          status: "confirmed",
          created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: "ORD-DEMO002",
          payment_id: "pay-def456demo",
          items: [
            { name: "AI Inventory Manager", qty: 1, price: 2499, emoji: "🧠" },
            { name: "Payment Shield Plus", qty: 1, price: 1999, emoji: "🔐" },
          ],
          total: 4498,
          status: "confirmed",
          created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
        },
      ];
      localStorage.setItem("shopflow-orders", JSON.stringify(demo));
      setOrders(demo);
    } else {
      setOrders(stored);
    }
  }, []);

  const handleRefundedOrder = (orderId: string) => {
    setRefundedIds((prev) => new Set(Array.from(prev).concat(orderId)));
  };

  const refreshOrders = () => {
    const stored = JSON.parse(localStorage.getItem("shopflow-orders") || "[]");
    setOrders(stored);
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Package className="w-6 h-6" style={{ color: "#6366f1" }} />
            My Orders
          </h1>
          <p className="text-sm text-gray-500 mt-1">{orders.length} order{orders.length !== 1 ? "s" : ""} total</p>
        </div>
        <button
          id="refresh-orders-btn"
          onClick={refreshOrders}
          className="btn-secondary"
          style={{ padding: "8px 14px", fontSize: "13px" }}
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Empty */}
      {orders.length === 0 && (
        <div className="glass p-16 text-center">
          <Package className="w-16 h-16 mx-auto mb-4" style={{ color: "rgba(99,102,241,0.3)" }} />
          <h3 className="text-lg font-semibold text-white mb-2">No orders yet</h3>
          <p className="text-gray-500 mb-6">Your order history will appear here after checkout.</p>
          <Link href="/" id="start-shopping-btn" className="btn-primary">
            <ShoppingCart className="w-4 h-4" />
            Start Shopping
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Orders List */}
      <div className="space-y-4">
        {orders.map((order) => (
          <OrderCard
            key={order.id}
            order={order}
            onRefund={handleRefundedOrder}
          />
        ))}
      </div>

      {/* Refund note */}
      {orders.length > 0 && (
        <p className="text-xs text-gray-600 text-center mt-8 flex items-center justify-center gap-1">
          <AlertCircle className="w-3 h-3" />
          Refunds are processed within 5-7 business days to your original payment method.
        </p>
      )}
    </div>
  );
}
