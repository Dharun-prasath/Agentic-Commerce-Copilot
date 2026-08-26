import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ShoppingCart, Heart, Search, User, LogOut, Package, Menu, X, Zap } from 'lucide-react';
import { useCartStore } from '@/store/cartStore';
import { useAuthStore } from '@/store/authStore';
import { useWishlistStore } from '@/store/wishlistStore';
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import type { SearchSuggestion } from '@/types';
import { toast } from 'sonner';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { cart, fetchCart } = useCartStore();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchCart();
  }, [isAuthenticated]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data: suggestions } = useQuery<SearchSuggestion>({
    queryKey: ['search-suggestions', debouncedQuery],
    queryFn: () => api.get(`/products/search/suggestions?q=${debouncedQuery}&limit=5`).then(r => r.data),
    enabled: debouncedQuery.length >= 2,
  });

  // Close suggestions on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSearch = (q?: string) => {
    const query = q || searchQuery;
    if (query.trim()) {
      navigate(`/products?search=${encodeURIComponent(query.trim())}`);
      setShowSuggestions(false);
      setSearchQuery(query);
    }
  };

  const handleLogout = () => {
    logout();
    setUserMenuOpen(false);
    toast.success('Logged out successfully');
    navigate('/');
  };

  const cartCount = cart?.item_count || 0;

  return (
    <nav className="sticky top-0 z-50 glass-card border-x-0 border-t-0 rounded-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <img src="/brand.png" alt="Dextro Logo" className="w-10 h-10 object-contain" />
            <span className="font-bold text-slate-900 text-lg hidden sm:block">
              Dex<span className="gradient-text">tro</span>
            </span>
          </Link>

          {/* Search */}
          <div ref={searchRef} className="relative flex-1 max-w-2xl">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
              <input
                type="text"
                placeholder="Search laptops, brands..."
                value={searchQuery}
                onChange={(e) => { setSearchQuery(e.target.value); setShowSuggestions(true); }}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                onFocus={() => searchQuery.length >= 2 && setShowSuggestions(true)}
                className="input-field pl-10 pr-4 h-10"
              />
            </div>
            {/* Search suggestions dropdown */}
            {showSuggestions && suggestions && suggestions.products.length > 0 && (
              <div className="absolute top-full mt-2 w-full glass-card p-2 z-50">
                {suggestions.products.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => { navigate(`/products/${p.slug}`); setShowSuggestions(false); }}
                    className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-slate-100 transition-colors text-left"
                  >
                    <img src={p.thumbnail || ''} alt={p.name} className="w-10 h-8 object-cover rounded" />
                    <div>
                      <p className="text-sm text-slate-900 font-medium line-clamp-1">{p.name}</p>
                      <p className="text-xs text-slate-600">₹{p.price.toLocaleString()}</p>
                    </div>
                  </button>
                ))}
                <button
                  onClick={() => handleSearch()}
                  className="w-full p-2 text-center text-sm text-blue-600 hover:text-blue-700 transition-colors"
                >
                  View all results for "{debouncedQuery}"
                </button>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1">


            {/* Wishlist */}
            {isAuthenticated && (
              <Link to="/wishlist" className="btn-ghost">
                <Heart className="w-5 h-5" />
              </Link>
            )}

            {/* Cart */}
            <Link to="/cart" className="relative btn-ghost">
              <ShoppingCart className="w-5 h-5" />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-blue-600 rounded-full text-[10px] font-bold text-slate-900 flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </Link>

            {/* User Menu */}
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="btn-ghost"
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-slate-900 text-xs font-bold">
                    {user?.name[0]?.toUpperCase()}
                  </div>
                </button>
                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-2 w-48 glass-card p-2 z-50">
                    <p className="px-3 py-2 text-sm text-slate-900 font-medium border-b border-slate-200 mb-1">{user?.name}</p>
                    <Link to="/orders" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors">
                      <Package className="w-4 h-4" /> Orders
                    </Link>
                    <button onClick={handleLogout} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-900 hover:text-slate-700 hover:bg-slate-900/10 rounded-lg transition-colors w-full">
                      <LogOut className="w-4 h-4" /> Logout
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link to="/login" className="btn-primary text-xs px-4 py-2">
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
