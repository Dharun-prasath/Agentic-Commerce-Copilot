import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Package, Clock, CheckCircle, XCircle, Truck, Eye } from 'lucide-react';
import api from '@/services/api';
import type { Order } from '@/types';

export default function OrdersPage() {
  const { data: orders, isLoading } = useQuery<Order[]>({
    queryKey: ['orders'],
    queryFn: () => api.get('/orders').then(r => r.data),
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'DELIVERED': return <CheckCircle className="w-5 h-5 text-blue-600" />;
      case 'SHIPPED': return <Truck className="w-5 h-5 text-blue-600" />;
      case 'CANCELLED': return <XCircle className="w-5 h-5 text-slate-900" />;
      default: return <Clock className="w-5 h-5 text-blue-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DELIVERED': return 'text-blue-600 bg-blue-600/10 border-blue-600/20';
      case 'SHIPPED': return 'text-blue-600 bg-blue-600/10 border-blue-600/20';
      case 'CANCELLED': return 'text-slate-900 bg-slate-900/10 border-slate-900/20';
      default: return 'text-blue-600 bg-blue-600/10 border-blue-600/20';
    }
  };

  if (isLoading) {
    return <div className="max-w-6xl mx-auto px-4 py-16 text-center"><div className="skeleton h-96 rounded-2xl" /></div>;
  }

  if (!orders || orders.length === 0) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-24 text-center">
        <Package className="w-24 h-24 text-slate-700 mx-auto mb-6" />
        <h2 className="text-slate-900 text-2xl font-bold mb-3">No orders yet</h2>
        <p className="text-slate-600 mb-8">When you place an order, it will appear here.</p>
        <Link to="/products" className="btn-primary">Start Shopping</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-2">
        <Package className="w-6 h-6 text-blue-600" /> My Orders
      </h1>

      <div className="space-y-6">
        {orders.map((order) => (
          <div key={order.id} className="glass-card overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-200 p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-6">
                <div>
                  <p className="text-slate-600 text-xs mb-1">Order Number</p>
                  <p className="text-slate-900 font-bold">{order.order_number}</p>
                </div>
                <div>
                  <p className="text-slate-600 text-xs mb-1">Date</p>
                  <p className="text-slate-900 font-medium">{new Date(order.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-slate-600 text-xs mb-1">Total Amount</p>
                  <p className="text-slate-900 font-bold">₹{order.total_amount.toLocaleString('en-IN')}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border flex items-center gap-1 ${getStatusColor(order.status)}`}>
                  {getStatusIcon(order.status)} {order.status}
                </span>
                <Link to={`/orders/${order.id}`} className="btn-secondary text-xs px-3 py-1.5">
                  <Eye className="w-4 h-4" /> View Details
                </Link>
              </div>
            </div>
            
            <div className="p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row gap-4 overflow-x-auto pb-2">
                {order.items.slice(0, 3).map(item => (
                  <div key={item.id} className="flex gap-4 min-w-[250px]">
                    <img src={item.product_thumbnail || ''} alt={item.product_name} className="w-20 h-16 object-cover rounded-lg" />
                    <div>
                      <p className="text-slate-900 text-sm font-medium line-clamp-1 hover:text-blue-700">
                        <Link to={`/products/${item.product_id}`}>{item.product_name}</Link>
                      </p>
                      <p className="text-slate-600 text-xs mt-1">Qty: {item.quantity}</p>
                    </div>
                  </div>
                ))}
                {order.items.length > 3 && (
                  <div className="flex items-center justify-center min-w-[100px] h-16 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-blue-600 text-sm font-medium">+{order.items.length - 3} more</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
