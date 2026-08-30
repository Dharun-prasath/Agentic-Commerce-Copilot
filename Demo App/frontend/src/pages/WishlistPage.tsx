import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Heart, ShoppingCart, Trash2 } from 'lucide-react';
import api from '@/services/api';
import type { Wishlist } from '@/types';
import { useCartStore } from '@/store/cartStore';
import { useWishlistStore } from '@/store/wishlistStore';
import { toast } from 'sonner';
import { trackEvent } from '@/services/tracker';

export default function WishlistPage() {
  const { addItem } = useCartStore();
  const { setWishlistIds, removeId } = useWishlistStore();

  const { data: wishlist, isLoading, refetch } = useQuery<Wishlist>({
    queryKey: ['wishlist'],
    queryFn: () => api.get('/wishlist').then(r => r.data),
  });

  useEffect(() => {
    if (wishlist) {
      setWishlistIds(wishlist.items.map(i => i.product_id));
    }
  }, [wishlist, setWishlistIds]);

  const handleRemove = async (productId: string) => {
    try {
      await api.delete(`/wishlist/items/${productId}`);
      removeId(productId);
      refetch();
      trackEvent('WISHLIST_REMOVED', { product_id: productId });
      toast.info('Removed from wishlist');
    } catch {
      toast.error('Failed to remove item');
    }
  };

  const handleAddToCart = async (productId: string) => {
    try {
      await addItem(productId, 1);
      toast.success('Added to cart');
    } catch {
      toast.error('Failed to add to cart');
    }
  };

  if (isLoading) {
    return <div className="max-w-6xl mx-auto px-4 py-16 text-center"><div className="skeleton h-96 rounded-2xl" /></div>;
  }

  if (!wishlist || wishlist.items.length === 0) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-24 text-center">
        <Heart className="w-24 h-24 text-slate-700 mx-auto mb-6" />
        <h2 className="text-slate-900 text-2xl font-bold mb-3">Your wishlist is empty</h2>
        <p className="text-slate-600 mb-8">Save items you love to review them later.</p>
        <Link to="/products" className="btn-primary">Explore Products</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-2">
        <Heart className="w-6 h-6 text-slate-900" /> My Wishlist ({wishlist.item_count})
      </h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {wishlist.items.map((item) => (
          <div key={item.id} className="glass-card overflow-hidden group">
            <div className="relative aspect-[4/3]">
              <img src={item.product_thumbnail || ''} alt={item.product_name} className="w-full h-full object-cover" />
              <button
                onClick={() => handleRemove(item.product_id)}
                className="absolute top-2 right-2 w-8 h-8 rounded-full bg-white/80 text-slate-900 flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-slate-900 transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              {item.discount_percentage > 0 && (
                <span className="absolute top-2 left-2 badge bg-slate-900/90 text-slate-900 border-0 text-[10px]">
                  -{Math.round(item.discount_percentage)}%
                </span>
              )}
            </div>
            <div className="p-4">
              <p className="text-blue-600 text-xs font-medium mb-1">{item.product_brand}</p>
              <h3 className="text-slate-900 text-sm font-semibold line-clamp-2 mb-2">
                <Link to={`/products/${item.product_slug}`} className="hover:text-blue-700 transition-colors">
                  {item.product_name}
                </Link>
              </h3>
              <div className="flex items-end gap-2 mb-4">
                <p className="text-slate-900 font-bold text-lg">₹{item.price.toLocaleString('en-IN')}</p>
                {item.original_price > item.price && (
                  <p className="text-slate-500 text-xs line-through mb-1">₹{item.original_price.toLocaleString('en-IN')}</p>
                )}
              </div>
              <button
                onClick={() => handleAddToCart(item.product_id)}
                disabled={item.stock < 1}
                className="btn-primary w-full text-xs py-2"
              >
                <ShoppingCart className="w-4 h-4" /> {item.stock < 1 ? 'Out of Stock' : 'Add to Cart'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
