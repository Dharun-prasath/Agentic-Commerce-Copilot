import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ShoppingCart, Heart, Search, User, LogOut, Package, X } from 'lucide-react';
import { useCartStore } from '@/store/cartStore';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'sonner';
import api from '@/services/api';

interface SuggestedProduct {
  id: string;
  name: string;
  slug: string;
  price: number;
  thumbnail?: string;
  brand: string;
}

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { cart, fetchCart } = useCartStore();
  const { user, isAuthenticated, logout } = useAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SuggestedProduct[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchCart();
  }, [isAuthenticated]);

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

  const fetchSuggestions = useCallback(async (q: string) => {
    // Cancel any previous in-flight request
    if (abortRef.current) {
      abortRef.current.abort();
    }

    if (!q.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    abortRef.current = new AbortController();
    setIsSearching(true);

    try {
      const { data } = await api.get(
        `/products/search/suggestions?q=${encodeURIComponent(q)}&limit=6`,
        { signal: abortRef.current.signal }
      );
      setSuggestions(data.products || []);
      setShowSuggestions(true);
    } catch (err: any) {
      if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
        setSuggestions([]);
      }
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchQuery(val);

    // Clear previous debounce
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!val.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    // Debounce 250ms
    debounceRef.current = setTimeout(() => {
      fetchSuggestions(val);
    }, 250);
  };

  const handleSearch = (q?: string) => {
    const query = (q || searchQuery).trim();
    if (query) {
      navigate(`/products?search=${encodeURIComponent(query)}`);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (slug: string) => {
    navigate(`/products/${slug}`);
    setShowSuggestions(false);
    setSearchQuery('');
    setSuggestions([]);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const handleLogout = async () => {
    await logout();
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
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
              <input
                type="text"
                placeholder="Search laptops, brands..."
                value={searchQuery}
                onChange={handleInputChange}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                onFocus={() => {
                  if (suggestions.length > 0) setShowSuggestions(true);
                }}
                className="input-field pl-10 pr-8 h-10 w-full"
                autoComplete="off"
              />
              {searchQuery && (
                <button
                  onClick={handleClearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Suggestions Dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-xl z-50 overflow-hidden">
                {suggestions.map((p) => (
                  <button
                    key={p.id}
                    onMouseDown={(e) => e.preventDefault()} // prevent blur before click
                    onClick={() => handleSuggestionClick(p.slug)}
                    className="flex items-center gap-3 w-full px-4 py-3 hover:bg-slate-50 transition-colors text-left border-b border-slate-100 last:border-0"
                  >
                    <div className="w-12 h-10 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0">
                      {p.thumbnail ? (
                        <img src={p.thumbnail} alt={p.name} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-400">
                          <Search className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-900 font-medium truncate">{p.name}</p>
                      <p className="text-xs text-slate-500">{p.brand} · ₹{p.price.toLocaleString('en-IN')}</p>
                    </div>
                  </button>
                ))}
                <button
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => handleSearch()}
                  className="w-full px-4 py-3 text-center text-sm text-blue-600 hover:bg-blue-50 transition-colors font-medium"
                >
                  View all results for "{searchQuery}"
                </button>
              </div>
            )}

            {/* Loading indicator */}
            {isSearching && searchQuery && (
              <div className="absolute top-full mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-xl z-50 px-4 py-3 text-sm text-slate-500">
                Searching...
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
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-blue-600 rounded-full text-[10px] font-bold text-white flex items-center justify-center">
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
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white text-xs font-bold">
                    {user?.name[0]?.toUpperCase()}
                  </div>
                </button>
                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-2 w-48 glass-card p-2 z-50">
                    <p className="px-3 py-2 text-sm text-slate-900 font-medium border-b border-slate-200 mb-1">{user?.name}</p>
                    <Link to="/orders" onClick={() => setUserMenuOpen(false)} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors">
                      <Package className="w-4 h-4" /> Orders
                    </Link>
                    <button onClick={handleLogout} className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors w-full">
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
