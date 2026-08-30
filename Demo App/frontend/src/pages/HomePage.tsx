import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, Zap, Shield, Truck, Star, TrendingUp, Award, ChevronRight, Laptop } from 'lucide-react';
import api from '@/services/api';
import type { ProductListResponse, Category } from '@/types';
import ProductCard from '@/components/product/ProductCard';
import { motion } from 'framer-motion';

const HERO_PRODUCTS = [
  { title: 'Apple MacBook Pro M3', subtitle: 'Pro-level performance', tag: 'New Arrival', color: 'from-blue-700 to-blue-800' },
  { title: 'ASUS ROG Zephyrus G16', subtitle: 'Ultimate gaming beast', tag: 'Top Gaming', color: 'from-slate-900 to-slate-900' },
  { title: 'Dell XPS 15 OLED', subtitle: 'Breathtaking display', tag: 'Editor\'s Pick', color: 'from-blue-500 to-blue-700' },
];

export default function HomePage() {
  const navigate = useNavigate();
  const [heroIndex, setHeroIndex] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const timer = setInterval(() => setHeroIndex(i => (i + 1) % HERO_PRODUCTS.length), 5000);
    return () => clearInterval(timer);
  }, []);

  const { data: featuredData } = useQuery<ProductListResponse>({
    queryKey: ['featured-products'],
    queryFn: () => api.get('/products?is_featured=true&page_size=8').then(r => r.data),
  });

  const { data: trendingData } = useQuery<ProductListResponse>({
    queryKey: ['trending-products'],
    queryFn: () => api.get('/products?is_trending=true&page_size=4').then(r => r.data),
  });

  const { data: bestSellerData } = useQuery<ProductListResponse>({
    queryKey: ['bestseller-products'],
    queryFn: () => api.get('/products?is_best_seller=true&page_size=4').then(r => r.data),
  });

  const { data: categories } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => api.get('/products/categories').then(r => r.data),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) navigate(`/products?search=${encodeURIComponent(searchQuery.trim())}`);
  };

  const hero = HERO_PRODUCTS[heroIndex];

  return (
    <div className="min-h-screen">
      {/* ── Hero Section ─────────────────────────────────────────────────── */}
      <section className={`relative py-24 px-4 sm:px-6 lg:px-8 overflow-hidden transition-all duration-1000`}>
        <div className={`absolute inset-0 bg-gradient-to-br ${hero.color} opacity-20 transition-all duration-1000`} />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.15)_0%,transparent_70%)]" />
        
        <div className="relative max-w-7xl mx-auto text-center">
          <motion.div
            key={heroIndex}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="badge badge-primary mb-4 text-sm px-4 py-1">{hero.tag}</span>
            <h1 className="text-5xl sm:text-7xl font-black text-slate-900 mb-4 leading-tight">
              {hero.title.split(' ').slice(0, 2).join(' ')}{' '}
              <span className="gradient-text">{hero.title.split(' ').slice(2).join(' ')}</span>
            </h1>
            <p className="text-xl text-slate-700 mb-8">{hero.subtitle}</p>
          </motion.div>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex max-w-2xl mx-auto gap-3 mb-8">
            <input
              type="text"
              placeholder="Search for laptops, brands, specs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field flex-1 text-base"
            />
            <button type="submit" className="btn-primary px-8">
              Search <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Hero dots */}
          <div className="flex justify-center gap-2 mb-8">
            {HERO_PRODUCTS.map((_, i) => (
              <button
                key={i}
                onClick={() => setHeroIndex(i)}
                className={`w-2 h-2 rounded-full transition-all ${i === heroIndex ? 'w-6 bg-blue-600' : 'bg-white/30'}`}
              />
            ))}
          </div>

          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/products" className="btn-primary">
              Shop All Products <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/products?is_featured=true" className="btn-secondary">
              View Featured
            </Link>
          </div>
        </div>
      </section>

      {/* ── Trust Badges ──────────────────────────────────────────────────── */}
      <section className="py-8 border-y border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: Truck, title: 'Free Shipping', sub: 'On orders above ₹50,000' },
              { icon: Shield, title: 'Secure Payment', sub: 'Powered by Razorpay' },
              { icon: Award, title: 'Genuine Products', sub: '100% authentic' },
              { icon: Zap, title: 'Fast Delivery', sub: 'Express options available' },
            ].map(({ icon: Icon, title, sub }) => (
              <div key={title} className="flex items-center gap-3 glass-card p-4">
                <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-slate-900 font-semibold text-sm">{title}</p>
                  <p className="text-slate-600 text-xs">{sub}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Categories ────────────────────────────────────────────────────── */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="section-title">Shop by Category</h2>
          <p className="section-subtitle">Find your perfect tech companion</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {(categories || []).map((cat) => (
              <Link
                key={cat.id}
                to={`/products?category=${cat.slug}`}
                className="glass-card-hover p-4 text-center"
              >
                <div className="flex justify-center mb-3"><Laptop className="w-8 h-8 text-blue-600" /></div>
                <p className="text-slate-900 text-sm font-medium">{cat.name}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── Offers Banner ─────────────────────────────────────────────────── */}
      <section className="py-4 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card p-6 bg-gradient-to-r from-blue-50 to-blue-100 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-slate-900 font-bold text-xl">First Order Discount</h3>
              <p className="text-slate-700 text-sm mt-1">Use code <span className="text-blue-700 font-bold">WELCOME10</span> for 10% off on your first order!</p>
            </div>
            <Link to="/products" className="btn-primary whitespace-nowrap">
              Shop Now <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Featured Products ─────────────────────────────────────────────── */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="section-title">Featured Products</h2>
              <p className="section-subtitle">Handpicked for you</p>
            </div>
            <Link to="/products?is_featured=true" className="btn-ghost text-blue-600">
              View All <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {(featuredData?.items || []).slice(0, 4).map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
            {!featuredData && Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="glass-card h-80 skeleton" />
            ))}
          </div>
        </div>
      </section>

      {/* ── Trending ──────────────────────────────────────────────────────── */}
      {trendingData?.items && trendingData.items.length > 0 && (
        <section className="py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="section-title flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-blue-600" /> Trending Now
                </h2>
                <p className="section-subtitle">What everyone's buying</p>
              </div>
              <Link to="/products?is_trending=true" className="btn-ghost text-blue-600">
                View All <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {trendingData.items.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Best Sellers ──────────────────────────────────────────────────── */}
      {bestSellerData?.items && bestSellerData.items.length > 0 && (
        <section className="py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="section-title flex items-center gap-2">
                  <Star className="w-6 h-6 text-blue-600" /> Best Sellers
                </h2>
                <p className="section-subtitle">Most popular choices</p>
              </div>
              <Link to="/products?is_best_seller=true" className="btn-ghost text-blue-600">
                View All <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {bestSellerData.items.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── Bottom CTA ────────────────────────────────────────────────────── */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="glass-card p-12 hero-gradient">
            <h2 className="text-4xl font-black text-slate-900 mb-4">
              Find your <span className="gradient-text">Perfect Laptop</span> today
            </h2>
            <p className="text-slate-700 mb-8 max-w-2xl mx-auto">
              Explore our wide range of premium laptops and accessories.
            </p>
            <Link to="/products" className="btn-primary text-base px-8 py-4">
              Start Shopping
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

function GitCompare({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="18" cy="18" r="3"/>
      <circle cx="6" cy="6" r="3"/>
      <path d="M13 6h3a2 2 0 0 1 2 2v7"/>
      <line x1="6" y1="9" x2="6" y2="21"/>
    </svg>
  );
}
