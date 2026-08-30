import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Trash2, Plus, Minus, ShoppingBag, Tag, ArrowRight } from 'lucide-react';
import { useCartStore } from '@/store/cartStore';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'sonner';

export default function CartPage() {
  const { cart, fetchCart, updateItem, removeItem, applyCoupon, isLoading } = useCartStore();
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [couponInput, setCouponInput] = useState('');
  const [couponLoading, setCouponLoading] = useState(false);
  const [appliedCoupon, setAppliedCoupon] = useState<{ code: string; discount: number } | null>(null);

  useEffect(() => { fetchCart(); }, [isAuthenticated]);

  const handleApplyCoupon = async () => {
    if (!couponInput.trim()) return;
    setCouponLoading(true);
    const result = await applyCoupon(couponInput.trim());
    if (result.valid) {
      setAppliedCoupon({ code: couponInput.trim().toUpperCase(), discount: result.discount });
      toast.success(result.message);
    } else {
      toast.error(result.message);
    }
    setCouponLoading(false);
  };

  const handleCheckout = () => {
    if (!isAuthenticated) { toast.error('Please sign in to checkout'); navigate('/login'); return; }
    navigate('/checkout', { state: { appliedCoupon } });
  };

  if (isLoading && !cart) {
    return <div className="max-w-4xl mx-auto px-4 py-16 text-center"><div className="skeleton h-96 rounded-2xl" /></div>;
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-24 text-center">
        <ShoppingBag className="w-24 h-24 text-slate-700 mx-auto mb-6" />
        <h2 className="text-slate-900 text-2xl font-bold mb-3">Your cart is empty</h2>
        <p className="text-slate-600 mb-8">Explore our collection and add products you love!</p>
        <Link to="/products" className="btn-primary">Start Shopping</Link>
      </div>
    );
  }

  const subtotal = cart.subtotal;
  const discount = appliedCoupon?.discount || 0;
  const afterDiscount = subtotal - discount;
  const tax = afterDiscount * 0.18;
  const shipping = subtotal >= 50000 ? 0 : 99;
  const total = afterDiscount + tax + shipping;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Shopping Cart ({cart.item_count} items)</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {cart.items.map((item) => (
            <div key={item.id} className="glass-card p-4 flex gap-4">
              <Link to={`/products/${item.product_slug}`}>
                <img
                  src={item.product_thumbnail || 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=200&q=80'}
                  alt={item.product_name}
                  className="w-24 h-20 object-cover rounded-xl shrink-0"
                />
              </Link>
              <div className="flex-1 min-w-0">
                <Link to={`/products/${item.product_slug}`}>
                  <h3 className="text-slate-900 font-semibold text-sm hover:text-blue-700 transition-colors line-clamp-2">{item.product_name}</h3>
                </Link>
                <p className="text-slate-600 text-xs mt-0.5">{item.product_brand}</p>
                <div className="flex items-center justify-between mt-3 gap-4">
                  <div>
                    <p className="text-slate-900 font-bold">₹{item.unit_price.toLocaleString('en-IN')}</p>
                    {item.original_price > item.unit_price && (
                      <p className="text-slate-500 text-xs line-through">₹{item.original_price.toLocaleString('en-IN')}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center glass-card rounded-xl overflow-hidden">
                      <button
                        onClick={() => item.quantity > 1 ? updateItem(item.id, item.quantity - 1) : removeItem(item.id)}
                        className="w-8 h-8 flex items-center justify-center hover:bg-slate-100 text-slate-900 transition-colors text-sm"
                      >
                        {item.quantity === 1 ? <Trash2 className="w-3 h-3 text-slate-900" /> : <Minus className="w-3 h-3" />}
                      </button>
                      <span className="w-8 text-center text-slate-900 text-sm">{item.quantity}</span>
                      <button
                        onClick={() => item.quantity < item.stock && updateItem(item.id, item.quantity + 1)}
                        disabled={item.quantity >= item.stock}
                        className="w-8 h-8 flex items-center justify-center hover:bg-slate-100 text-slate-900 transition-colors disabled:opacity-30"
                      >
                        <Plus className="w-3 h-3" />
                      </button>
                    </div>
                    <button onClick={() => removeItem(item.id)} className="text-slate-900 hover:text-slate-700 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-blue-700 text-sm font-semibold mt-1">Subtotal: ₹{item.subtotal.toLocaleString('en-IN')}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="space-y-4">
          {/* Coupon */}
          <div className="glass-card p-4">
            <h3 className="text-slate-900 font-semibold mb-3 flex items-center gap-2"><Tag className="w-4 h-4 text-blue-600" /> Apply Coupon</h3>
            {appliedCoupon ? (
              <div className="flex items-center justify-between p-3 bg-blue-600/10 border border-blue-600/30 rounded-xl">
                <div>
                  <p className="text-blue-600 font-semibold text-sm">{appliedCoupon.code}</p>
                  <p className="text-blue-500 text-xs">-₹{appliedCoupon.discount.toLocaleString('en-IN')} saved!</p>
                </div>
                <button onClick={() => { setAppliedCoupon(null); setCouponInput(''); }} className="text-slate-900 hover:text-slate-700 text-xs">Remove</button>
              </div>
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Enter coupon code"
                  value={couponInput}
                  onChange={(e) => setCouponInput(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === 'Enter' && handleApplyCoupon()}
                  className="input-field flex-1 text-sm uppercase"
                />
                <button onClick={handleApplyCoupon} disabled={couponLoading} className="btn-secondary text-sm px-4">
                  {couponLoading ? '...' : 'Apply'}
                </button>
              </div>
            )}
            <div className="mt-3 text-xs text-slate-500">
              <p>Try: <span className="text-blue-600 cursor-pointer" onClick={() => setCouponInput('WELCOME10')}>WELCOME10</span>, <span className="text-blue-600 cursor-pointer" onClick={() => setCouponInput('SAVE500')}>SAVE500</span>, <span className="text-blue-600 cursor-pointer" onClick={() => setCouponInput('LAPTOP5')}>LAPTOP5</span></p>
            </div>
          </div>

          {/* Summary */}
          <div className="glass-card p-4 space-y-3">
            <h3 className="text-slate-900 font-semibold">Order Summary</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between text-slate-700">
                <span>Subtotal ({cart.item_count} items)</span>
                <span>₹{subtotal.toLocaleString('en-IN')}</span>
              </div>
              {discount > 0 && (
                <div className="flex justify-between text-blue-600">
                  <span>Coupon ({appliedCoupon?.code})</span>
                  <span>-₹{discount.toLocaleString('en-IN')}</span>
                </div>
              )}
              <div className="flex justify-between text-slate-700">
                <span>Tax (18% GST)</span>
                <span>₹{Math.round(tax).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-slate-700">
                <span>Shipping</span>
                <span className={shipping === 0 ? 'text-blue-600' : ''}>{shipping === 0 ? 'FREE' : `₹${shipping}`}</span>
              </div>
              <div className="divider pt-2" />
              <div className="flex justify-between text-slate-900 font-bold text-lg pt-2">
                <span>Total</span>
                <span>₹{Math.round(total).toLocaleString('en-IN')}</span>
              </div>
            </div>
            <button onClick={handleCheckout} className="btn-primary w-full py-3 mt-2">
              Proceed to Checkout <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
