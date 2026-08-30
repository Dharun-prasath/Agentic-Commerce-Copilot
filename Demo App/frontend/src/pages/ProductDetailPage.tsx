import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Star, Heart, ShoppingCart, ChevronLeft, ChevronRight, Truck, Shield, Award, Check, X, SearchX } from 'lucide-react';
import api from '@/services/api';
import type { ProductDetail } from '@/types';
import ProductCard from '@/components/product/ProductCard';
import { useCartStore } from '@/store/cartStore';
import { useWishlistStore } from '@/store/wishlistStore';
import { useAuthStore } from '@/store/authStore';
import { trackEvent } from '@/services/tracker';
import { toast } from 'sonner';

export default function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { addItem } = useCartStore();

  const { hasProduct: inWishlist, addId, removeId } = useWishlistStore();
  const { isAuthenticated } = useAuthStore();

  const [selectedImage, setSelectedImage] = useState(0);
  const [activeTab, setActiveTab] = useState<'specs' | 'features' | 'reviews'>('specs');
  const [addingToCart, setAddingToCart] = useState(false);
  const [wishlistLoading, setWishlistLoading] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [viewStartTime] = useState(Date.now());

  const { data: product, isLoading, error } = useQuery<ProductDetail>({
    queryKey: ['product', slug],
    queryFn: () => api.get(`/products/${slug}`).then(r => r.data),
    enabled: !!slug,
  });

  // Track product view
  useEffect(() => {
    if (product) {
      trackEvent('PRODUCT_DETAILS_VIEWED', {
        product_id: product.id,
        category_id: product.category_id,
        metadata: { brand: product.brand, price: product.price },
      });
      return () => {
        const duration = Math.round((Date.now() - viewStartTime) / 1000);
        trackEvent('PRODUCT_VIEW_DURATION', {
          product_id: product.id,
          category_id: product.category_id,
          metadata: { duration_seconds: duration },
        });
      };
    }
  }, [product?.id]);

  const handleAddToCart = async (buyNow = false) => {
    if (!product) return;
    setAddingToCart(true);
    try {
      await addItem(product.id, quantity);
      toast.success(`${product.name} added to cart!`);
      if (buyNow) navigate('/cart');
    } catch (err: any) {
      toast.error(err.message || 'Failed to add to cart');
    } finally {
      setAddingToCart(false);
    }
  };

  const handleWishlist = async () => {
    if (!isAuthenticated) { toast.error('Please sign in'); navigate('/login'); return; }
    if (!product) return;
    setWishlistLoading(true);
    try {
      if (inWishlist(product.id)) {
        await api.delete(`/wishlist/items/${product.id}`);
        removeId(product.id);
        trackEvent('WISHLIST_REMOVED', { product_id: product.id });
        toast.info('Removed from wishlist');
      } else {
        await api.post('/wishlist/items', { product_id: product.id });
        addId(product.id);
        trackEvent('WISHLIST_ADDED', { product_id: product.id, category_id: product.category_id });
        toast.success('Added to wishlist!');
      }
    } catch { toast.error('Failed to update wishlist'); }
    finally { setWishlistLoading(false); }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="skeleton h-96 rounded-2xl" />
          <div className="space-y-4">
            <div className="skeleton h-8 w-3/4 rounded-lg" />
            <div className="skeleton h-6 w-1/2 rounded-lg" />
            <div className="skeleton h-16 rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-24 text-center">
        <SearchX className="w-16 h-16 text-slate-400 mb-4 mx-auto" />
        <h2 className="text-slate-900 text-2xl font-bold mb-4">Product not found</h2>
        <Link to="/products" className="btn-primary">Browse Products</Link>
      </div>
    );
  }

  const images = product.images.length > 0 ? product.images : [{ url: product.thumbnail || '', alt_text: product.name, id: '0', is_primary: true, sort_order: 0 }];
  const avgRating = product.rating;

  const savedAmount = product.original_price - product.price;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-slate-600 mb-6">
        <Link to="/" className="hover:text-slate-900">Home</Link> /
        <Link to="/products" className="hover:text-slate-900">Products</Link> /
        <Link to={`/products?category=${product.category?.slug}`} className="hover:text-slate-900">{product.category?.name}</Link> /
        <span className="text-slate-700 truncate">{product.name}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
        {/* ── Image Gallery ──────────────────────────────────────────────── */}
        <div className="space-y-4">
          <div className="glass-card overflow-hidden aspect-[4/3] relative group">
            <img
              src={images[selectedImage]?.url || ''}
              alt={images[selectedImage]?.alt_text || product.name}
              className="w-full h-full object-cover"
              onClick={() => trackEvent('PRODUCT_IMAGE_VIEWED', { product_id: product.id, metadata: { image_index: selectedImage } })}
            />
            {images.length > 1 && (
              <>
                <button onClick={() => setSelectedImage(i => Math.max(0, i - 1))} className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 glass-card rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronLeft className="w-5 h-5 text-slate-900" />
                </button>
                <button onClick={() => setSelectedImage(i => Math.min(images.length - 1, i + 1))} className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 glass-card rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronRight className="w-5 h-5 text-slate-900" />
                </button>
              </>
            )}
          </div>
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {images.map((img, i) => (
                <button
                  key={img.id}
                  onClick={() => setSelectedImage(i)}
                  className={`shrink-0 w-20 h-16 rounded-xl overflow-hidden border-2 transition-all ${i === selectedImage ? 'border-blue-600' : 'border-slate-200 hover:border-slate-400'}`}
                >
                  <img src={img.url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ── Product Info ───────────────────────────────────────────────── */}
        <div className="space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="badge badge-primary">{product.brand}</span>
              <span className="badge bg-slate-100 text-slate-700">{product.category?.name}</span>
              {product.is_best_seller && <span className="badge badge-success">Best Seller</span>}
            </div>
            <h1 className="text-3xl font-bold text-slate-900 leading-tight mb-3">{product.name}</h1>

            {/* Rating */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                {[1,2,3,4,5].map(i => (
                  <Star key={i} className={`w-5 h-5 ${i <= Math.round(avgRating) ? 'fill-blue-600 text-blue-600' : 'text-slate-600'}`} />
                ))}
              </div>
              <span className="text-slate-900 font-semibold">{avgRating}</span>
              <span className="text-slate-600 text-sm">({product.review_count} reviews)</span>
            </div>
          </div>

          {/* Price */}
          <div className="glass-card p-4">
            <div className="flex items-end gap-4 mb-1">
              <span className="text-4xl font-black text-slate-900">₹{product.price.toLocaleString('en-IN')}</span>
              {product.discount_percentage > 0 && (
                <span className="text-slate-500 text-xl line-through mb-1">₹{product.original_price.toLocaleString('en-IN')}</span>
              )}
            </div>
            {savedAmount > 0 && (
              <p className="text-blue-600 text-sm font-semibold">
                You save ₹{savedAmount.toLocaleString('en-IN')} ({Math.round(product.discount_percentage)}% off)
              </p>
            )}
          </div>

          {/* Stock Status */}
          <div className="flex items-center gap-2">
            {product.stock > 0 ? (
              <>
                <span className="w-2 h-2 rounded-full bg-blue-600" />
                <span className="text-blue-600 text-sm font-medium">In Stock</span>
                {product.stock <= 5 && <span className="text-blue-600 text-sm">(Only {product.stock} left!)</span>}
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-slate-900" />
                <span className="text-slate-900 text-sm font-medium">Out of Stock</span>
              </>
            )}
          </div>

          {/* Quantity */}
          {product.stock > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-slate-600 text-sm">Quantity:</span>
              <div className="flex items-center glass-card rounded-xl overflow-hidden">
                <button onClick={() => setQuantity(q => Math.max(1, q - 1))} className="w-10 h-10 flex items-center justify-center hover:bg-slate-100 text-slate-900 transition-colors">-</button>
                <span className="w-12 text-center text-slate-900 font-medium">{quantity}</span>
                <button onClick={() => setQuantity(q => Math.min(product.stock, q + 1))} className="w-10 h-10 flex items-center justify-center hover:bg-slate-100 text-slate-900 transition-colors">+</button>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => handleAddToCart(false)}
              disabled={addingToCart || product.stock < 1}
              className="btn-secondary flex-1 py-3"
            >
              <ShoppingCart className="w-5 h-5" />
              {addingToCart ? 'Adding...' : 'Add to Cart'}
            </button>
            <button
              onClick={() => handleAddToCart(true)}
              disabled={addingToCart || product.stock < 1}
              className="btn-primary flex-1 py-3"
            >
              Buy Now
            </button>
          </div>

          <div className="flex gap-3">
            <button onClick={handleWishlist} disabled={wishlistLoading} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl border transition-all ${inWishlist(product.id) ? 'bg-slate-900/20 border-slate-900/30 text-slate-900' : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100'}`}>
              <Heart className={`w-4 h-4 ${inWishlist(product.id) ? 'fill-slate-900' : ''}`} />
              {inWishlist(product.id) ? 'Wishlisted' : 'Add to Wishlist'}
            </button>
          </div>

          {/* Delivery Info */}
          <div className="glass-card p-4 space-y-2">
            <div className="flex items-center gap-3 text-sm">
              <Truck className="w-5 h-5 text-blue-600 shrink-0" />
              <div><span className="text-slate-900 font-medium">Free Shipping</span><span className="text-slate-600"> on orders above ₹50,000</span></div>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Shield className="w-5 h-5 text-blue-600 shrink-0" />
              <div><span className="text-slate-900 font-medium">Secure Payment</span><span className="text-slate-600"> via Razorpay</span></div>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Award className="w-5 h-5 text-blue-600 shrink-0" />
              <div><span className="text-slate-900 font-medium">Genuine Product</span><span className="text-slate-600"> with manufacturer warranty</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Tabs: Specs / Features / Reviews ─────────────────────────────── */}
      <div className="glass-card p-6">
        <div className="flex gap-1 mb-6 border-b border-slate-200 pb-4">
          {(['specs', 'features', 'reviews'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                const evtMap = { specs: 'PRODUCT_SPECIFICATIONS_VIEWED', features: 'PRODUCT_DETAILS_VIEWED', reviews: 'PRODUCT_REVIEW_VIEWED' } as const;
                trackEvent(evtMap[tab], { product_id: product.id, metadata: { tab } });
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${activeTab === tab ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:text-slate-900'}`}
            >
              {tab} {tab === 'reviews' && `(${product.reviews.length})`}
            </button>
          ))}
        </div>

        {activeTab === 'specs' && (
          <div className="grid grid-cols-1 gap-6">
            {Object.entries(product.specifications).map(([key, value]) => (
              <div key={key} className="bg-slate-50 p-4 rounded-xl">
                <h3 className="text-slate-900 font-semibold mb-3 capitalize text-lg">{key.replace(/_/g, ' ')}</h3>
                {typeof value === 'object' && value !== null ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {Object.entries(value).map(([subKey, subValue]) => (
                      <div key={subKey} className="flex gap-2">
                        <span className="text-slate-600 text-sm capitalize shrink-0 w-32">{subKey.replace(/_/g, ' ')}</span>
                        <span className="text-slate-900 text-sm font-medium">{String(subValue)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-slate-700">{String(value)}</span>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'features' && (
          <div className="space-y-2">
            <p className="text-slate-700 text-sm leading-relaxed mb-4">{product.description}</p>
            {(product.features || []).map((feature, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
                <Check className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                <span className="text-slate-200 text-sm">{feature}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'reviews' && (
          <div className="space-y-4">
            {product.reviews.length === 0 ? (
              <p className="text-slate-600 text-center py-8">No reviews yet. Be the first to review!</p>
            ) : (
              product.reviews.map((review) => (
                <div key={review.id} className="p-4 bg-slate-50 rounded-xl">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-slate-900 font-semibold text-sm">{review.reviewer_name}</p>
                      {review.is_verified_purchase && (
                        <span className="text-blue-600 text-xs">✓ Verified Purchase</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      {[1,2,3,4,5].map(i => (
                        <Star key={i} className={`w-3 h-3 ${i <= review.rating ? 'fill-blue-600 text-blue-600' : 'text-slate-600'}`} />
                      ))}
                    </div>
                  </div>
                  {review.title && <p className="text-slate-900 font-medium text-sm mb-1">{review.title}</p>}
                  <p className="text-slate-700 text-sm">{review.body}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* ── Compatible Accessories ─────────────────────────────────────────── */}
      {product.accessories && product.accessories.length > 0 && (
        <div className="mt-12 mb-8">
          <h2 className="text-2xl font-bold text-slate-900 mb-6">Compatible Accessories</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {product.accessories.map((acc, idx) => (
              <div key={`${acc.target_product.id}-${idx}`} className="relative">
                <ProductCard product={acc.target_product} />
                <div className="absolute top-2 right-2 z-10">
                  <span className={`badge ${
                    acc.compatibility_type === 'COMPATIBLE' ? 'badge-primary' :
                    acc.compatibility_type === 'RECOMMENDED' ? 'badge-success' :
                    acc.compatibility_type === 'REQUIRED_ADAPTER' ? 'bg-orange-100 text-orange-800' :
                    'bg-slate-100 text-slate-800'
                  }`}>
                    {acc.compatibility_type.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
