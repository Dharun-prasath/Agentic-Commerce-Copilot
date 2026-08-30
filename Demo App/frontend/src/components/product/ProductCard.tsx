import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, ShoppingCart, Star } from 'lucide-react';
import type { ProductSummary } from '@/types';
import { useCartStore } from '@/store/cartStore';
import { useWishlistStore } from '@/store/wishlistStore';
import { useAuthStore } from '@/store/authStore';
import { trackEvent } from '@/services/tracker';
import { toast } from 'sonner';
import api from '@/services/api';

interface Props {
  product: ProductSummary;
  inWishlist?: boolean;
}

export default function ProductCard({ product, inWishlist: initialInWishlist }: Props) {
  const navigate = useNavigate();
  const { addItem, isLoading } = useCartStore();
  const { hasProduct: inWishlistStore, addId, removeId } = useWishlistStore();
  const { isAuthenticated } = useAuthStore();
  const [addingCart, setAddingCart] = useState(false);
  const [wishlistLoading, setWishlistLoading] = useState(false);

  const inWishlist = inWishlistStore(product.id);

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setAddingCart(true);
    try {
      await addItem(product.id, 1);
      toast.success(`${product.name} added to cart!`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to add to cart');
    } finally {
      setAddingCart(false);
    }
  };

  const handleWishlist = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      toast.error('Please sign in to add to wishlist');
      navigate('/login');
      return;
    }
    setWishlistLoading(true);
    try {
      if (inWishlist) {
        await api.delete(`/wishlist/items/${product.id}`);
        removeId(product.id);
        trackEvent('WISHLIST_REMOVED', { product_id: product.id });
        toast.info('Removed from wishlist');
      } else {
        await api.post('/wishlist/items', { product_id: product.id });
        addId(product.id);
        trackEvent('WISHLIST_ADDED', { product_id: product.id, category_id: product.category_id });
        toast.success('Added to wishlist');
      }
    } catch {
      toast.error('Failed to update wishlist');
    } finally {
      setWishlistLoading(false);
    }
  };

  const handleClick = () => {
    trackEvent('PRODUCT_VIEWED', {
      product_id: product.id,
      category_id: product.category_id,
      metadata: { source: 'product_card', brand: product.brand },
    });
  };

  return (
    <Link to={`/products/${product.slug}`} onClick={handleClick}>
      <div className="product-card group">
        {/* Image */}
        <div className="relative overflow-hidden bg-gradient-to-br from-slate-800 to-slate-900">
          <img
            src={product.thumbnail || 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400&q=80'}
            alt={product.name}
            className="product-card-image"
            loading="lazy"
          />
          {/* Badges */}
          <div className="absolute top-2 left-2 flex flex-col gap-1">
            {product.is_featured && <span className="badge badge-primary text-[10px]">Featured</span>}
            {product.is_trending && <span className="badge badge-warning text-[10px]">Trending</span>}
            {product.is_best_seller && <span className="badge badge-success text-[10px]">Best Seller</span>}
            {product.discount_percentage > 0 && (
              <span className="badge bg-slate-900/90 text-slate-900 border-0 text-[10px]">
                -{Math.round(product.discount_percentage)}%
              </span>
            )}
          </div>
          {/* Action buttons (visible on hover) */}
          <div className="absolute top-2 right-2 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <button
              onClick={handleWishlist}
              disabled={wishlistLoading}
              className={`w-8 h-8 rounded-full flex items-center justify-center backdrop-blur-sm transition-all ${
                inWishlist
                  ? 'bg-slate-900 text-slate-900'
                  : 'bg-white/80 text-slate-900 hover:bg-slate-900/80'
              }`}
            >
              <Heart className={`w-4 h-4 ${inWishlist ? 'fill-white' : ''}`} />
            </button>
          </div>
        </div>

        {/* Info */}
        <div className="p-4">
          <p className="text-xs text-blue-600 font-medium mb-1">{product.brand}</p>
          <h3 className="text-slate-900 text-sm font-semibold line-clamp-2 mb-2 group-hover:text-blue-700 transition-colors">
            {product.name}
          </h3>

          {/* Rating */}
          <div className="flex items-center gap-1 mb-3">
            {[1,2,3,4,5].map(i => (
              <Star
                key={i}
                className={`w-3 h-3 ${i <= Math.round(product.rating) ? 'fill-blue-600 text-blue-600' : 'text-slate-600'}`}
              />
            ))}
            <span className="text-xs text-slate-600 ml-1">({product.review_count})</span>
          </div>

          {/* Price */}
          <div className="flex items-end justify-between gap-2">
            <div>
              <p className="text-slate-900 font-bold text-lg">₹{product.price.toLocaleString('en-IN')}</p>
              {product.discount_percentage > 0 && (
                <p className="text-slate-500 text-xs line-through">₹{product.original_price.toLocaleString('en-IN')}</p>
              )}
            </div>
            <button
              onClick={handleAddToCart}
              disabled={addingCart || product.stock < 1}
              className="btn-primary text-xs px-3 py-2 shrink-0"
            >
              {product.stock < 1 ? 'Out of stock' : addingCart ? '...' : (
                <><ShoppingCart className="w-3 h-3" /> Add</>
              )}
            </button>
          </div>

          {product.stock <= 5 && product.stock > 0 && (
            <p className="text-blue-600 text-xs mt-2">Only {product.stock} left!</p>
          )}
        </div>
      </div>
    </Link>
  );
}
