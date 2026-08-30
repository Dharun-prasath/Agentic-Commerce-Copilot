import { Link } from 'react-router-dom';
import { XCircle, RefreshCw, ShoppingBag } from 'lucide-react';

export default function PaymentFailurePage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="glass-card p-10">
          <XCircle className="w-20 h-20 text-slate-900 mx-auto mb-6" />
          <h1 className="text-3xl font-black text-slate-900 mb-2">Payment Failed</h1>
          <p className="text-slate-700 mb-6">Don't worry! Your order was not placed and you won't be charged.</p>
          <div className="space-y-3">
            <Link to="/checkout" className="btn-primary w-full justify-center">
              <RefreshCw className="w-4 h-4" /> Try Again
            </Link>
            <Link to="/cart" className="btn-secondary w-full justify-center">
              <ShoppingBag className="w-4 h-4" /> Back to Cart
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
