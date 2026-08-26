import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Package, Clock, CheckCircle, XCircle, Truck, MapPin, CreditCard, ChevronLeft } from 'lucide-react';
import api from '@/services/api';
import type { Order } from '@/types';

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: order, isLoading } = useQuery<Order>({
    queryKey: ['order', id],
    queryFn: () => api.get(`/orders/${id}`).then(r => r.data),
    enabled: !!id,
  });

  if (isLoading) {
    return <div className="max-w-4xl mx-auto px-4 py-16 text-center"><div className="skeleton h-96 rounded-2xl" /></div>;
  }

  if (!order) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-24 text-center">
        <h2 className="text-slate-900 text-2xl font-bold mb-4">Order not found</h2>
        <Link to="/orders" className="btn-primary">Back to Orders</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/orders" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-6 text-sm font-medium">
        <ChevronLeft className="w-4 h-4" /> Back to Orders
      </Link>

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1 flex items-center gap-2">
            Order #{order.order_number}
          </h1>
          <p className="text-slate-600 text-sm">Placed on {new Date(order.created_at).toLocaleString()}</p>
        </div>
        <div className="flex gap-2">
          <span className="badge badge-primary">{order.status}</span>
          <span className={order.payment_status === 'PAID' ? 'badge badge-success' : 'badge badge-warning'}>
            Payment: {order.payment_status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6">
            <h2 className="text-slate-900 font-bold text-lg mb-4 flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-600" /> Items Ordered
            </h2>
            <div className="space-y-4">
              {order.items.map(item => (
                <div key={item.id} className="flex gap-4 p-3 bg-slate-50 rounded-xl">
                  <img src={item.product_thumbnail || ''} alt={item.product_name} className="w-16 h-12 object-cover rounded-lg" />
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-900 text-sm font-medium line-clamp-1">{item.product_name}</p>
                    <p className="text-slate-600 text-xs mt-1">Qty: {item.quantity} × ₹{item.unit_price.toLocaleString('en-IN')}</p>
                  </div>
                  <p className="text-slate-900 font-bold text-sm shrink-0">₹{item.total_price.toLocaleString('en-IN')}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6">
            <h2 className="text-slate-900 font-bold text-lg mb-4 flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-blue-600" /> Order Summary
            </h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between text-slate-700"><span>Subtotal</span><span>₹{order.subtotal.toLocaleString('en-IN')}</span></div>
              {order.coupon_discount > 0 && <div className="flex justify-between text-blue-600"><span>Discount ({order.coupon_code})</span><span>-₹{order.coupon_discount.toLocaleString('en-IN')}</span></div>}
              <div className="flex justify-between text-slate-700"><span>Tax</span><span>₹{Math.round(order.tax_amount).toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between text-slate-700"><span>Shipping</span><span className={order.shipping_charge === 0 ? 'text-blue-600' : ''}>{order.shipping_charge === 0 ? 'FREE' : `₹${order.shipping_charge}`}</span></div>
              <div className="divider" />
              <div className="flex justify-between text-slate-900 font-bold text-lg pt-1"><span>Total</span><span>₹{Math.round(order.total_amount).toLocaleString('en-IN')}</span></div>
            </div>
          </div>

          <div className="glass-card p-6">
            <h2 className="text-slate-900 font-bold text-lg mb-4 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-blue-600" /> Shipping Address
            </h2>
            <p className="text-slate-900 text-sm font-medium">{order.shipping_name}</p>
            <p className="text-slate-600 text-sm mt-1">{order.shipping_line1}</p>
            {order.shipping_line2 && <p className="text-slate-600 text-sm">{order.shipping_line2}</p>}
            <p className="text-slate-600 text-sm">{order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}</p>
            <p className="text-slate-600 text-sm mt-2">Phone: {order.shipping_phone}</p>
          </div>

          <div className="glass-card p-6">
            <h2 className="text-slate-900 font-bold text-lg mb-4 flex items-center gap-2">
              <Truck className="w-5 h-5 text-blue-600" /> Delivery Method
            </h2>
            <p className="text-slate-900 text-sm font-medium">{order.delivery_method}</p>
            <p className="text-slate-600 text-sm mt-1">Estimated delivery: {order.delivery_days} days</p>
          </div>
        </div>
      </div>
    </div>
  );
}
