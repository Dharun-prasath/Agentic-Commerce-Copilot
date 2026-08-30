import { useSearchParams, Link } from 'react-router-dom';
import { CheckCircle, Package, ArrowRight, ShoppingBag } from 'lucide-react';
import { motion } from 'framer-motion';

export default function PaymentSuccessPage() {
  const [params] = useSearchParams();
  const orderNumber = params.get('order_number') || 'N/A';
  const orderId = params.get('order_id') || '';

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full text-center"
      >
        <div className="glass-card p-10">
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2, type: 'spring' }}>
            <CheckCircle className="w-20 h-20 text-blue-600 mx-auto mb-6" />
          </motion.div>
          <h1 className="text-3xl font-black text-slate-900 mb-2">Payment Successful!</h1>
          <p className="text-slate-700 mb-2">Your order has been placed successfully.</p>
          <div className="glass-card p-4 my-6 text-left">
            <p className="text-slate-600 text-sm">Order Number</p>
            <p className="text-slate-900 font-bold text-lg">{orderNumber}</p>
          </div>
          <p className="text-slate-600 text-sm mb-6">
            A confirmation email has been sent to your registered email address.
          </p>
          <div className="flex flex-col gap-3">
            <Link to={`/orders/${orderId}`} className="btn-primary w-full justify-center">
              <Package className="w-4 h-4" /> Track Order
            </Link>
            <Link to="/products" className="btn-secondary w-full justify-center">
              <ShoppingBag className="w-4 h-4" /> Continue Shopping
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
