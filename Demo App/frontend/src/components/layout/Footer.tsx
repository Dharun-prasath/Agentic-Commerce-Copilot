import { Link } from 'react-router-dom';
import { Zap } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center">
                <Zap className="w-4 h-4 text-slate-900" />
              </div>
              <span className="font-bold text-slate-900 text-lg">Dex<span className="gradient-text">tro</span></span>
            </Link>
            <p className="text-slate-600 text-sm leading-relaxed max-w-sm">
              Premium laptops and laptop accessories. The merchant application for Agentic Commerce Copilot —
              ready for seamless conversational commerce integration.
            </p>
          </div>
          <div>
            <h4 className="text-slate-900 font-semibold mb-4 text-sm">Shop</h4>
            <ul className="space-y-2">
              {['Laptops', 'Gaming Laptops', 'Ultrabooks', 'Workstations', 'Monitors'].map(cat => (
                <li key={cat}>
                  <Link to={`/products?category=${cat.toLowerCase().replace(' ', '-')}`} className="text-slate-600 hover:text-slate-900 text-sm transition-colors">
                    {cat}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-slate-900 font-semibold mb-4 text-sm">Account</h4>
            <ul className="space-y-2">
              {[['My Orders', '/orders'], ['Wishlist', '/wishlist'], ['Cart', '/cart'], ['Login', '/login']].map(([label, path]) => (
                <li key={label}>
                  <Link to={path} className="text-slate-600 hover:text-slate-900 text-sm transition-colors">{label}</Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-8 border-t border-slate-200 flex items-center justify-between">
          <p className="text-slate-500 text-xs">© 2026 Dextro - All Copyright Reserved</p>
          <p className="text-slate-500 text-xs">Built for Razorpay Buildathon 2026</p>
        </div>
      </div>
    </footer>
  );
}
