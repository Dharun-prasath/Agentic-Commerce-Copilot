import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { SlidersHorizontal, X, ChevronDown, Search, Grid3X3, List } from 'lucide-react';
import api from '@/services/api';
import type { ProductListResponse, Category, ProductFilters } from '@/types';
import ProductCard from '@/components/product/ProductCard';
import { trackEvent } from '@/services/tracker';

const SORT_OPTIONS = [
  { value: 'popularity', label: 'Most Popular' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'newest', label: 'Newest First' },
  { value: 'discount', label: 'Biggest Discount' },
];

const RAM_OPTIONS = ['8GB', '16GB', '32GB', '64GB'];
const STORAGE_OPTIONS = ['256GB', '512GB', '1TB', '2TB', '4TB'];

export default function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);

  const [filters, setFilters] = useState<ProductFilters>({
    search: searchParams.get('search') || undefined,
    category: searchParams.get('category') || undefined,
    brand: searchParams.get('brand') || undefined,
    min_price: undefined,
    max_price: undefined,
    min_rating: undefined,
    sort_by: 'popularity',
    is_featured: searchParams.get('is_featured') === 'true' ? true : undefined,
    is_trending: searchParams.get('is_trending') === 'true' ? true : undefined,
    is_best_seller: searchParams.get('is_best_seller') === 'true' ? true : undefined,
    ram: undefined,
    storage: undefined,
    page: 1,
    page_size: 20,
  });

  const [searchInput, setSearchInput] = useState(filters.search || '');
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search || '');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
      if (searchInput !== filters.search) {
        setFilters(f => ({ ...f, search: searchInput || undefined, page: 1 }));
        if (searchInput) trackEvent('PRODUCT_SEARCHED', { metadata: { query: searchInput } });
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Sync URL params on mount
  useEffect(() => {
    const search = searchParams.get('search');
    if (search) { setSearchInput(search); setDebouncedSearch(search); }
  }, []);

  const buildQuery = () => {
    const p = new URLSearchParams();
    if (filters.search) p.set('search', filters.search);
    if (filters.category) p.set('category', filters.category);
    if (filters.brand) p.set('brand', filters.brand);
    if (filters.min_price) p.set('min_price', String(filters.min_price));
    if (filters.max_price) p.set('max_price', String(filters.max_price));
    if (filters.min_rating) p.set('min_rating', String(filters.min_rating));
    if (filters.sort_by) p.set('sort_by', filters.sort_by);
    if (filters.is_featured) p.set('is_featured', 'true');
    if (filters.is_trending) p.set('is_trending', 'true');
    if (filters.is_best_seller) p.set('is_best_seller', 'true');
    if (filters.ram) p.set('ram', filters.ram);
    if (filters.storage) p.set('storage', filters.storage);
    p.set('page', String(filters.page || 1));
    p.set('page_size', String(filters.page_size || 20));
    return p.toString();
  };

  const { data, isLoading, isFetching } = useQuery<ProductListResponse>({
    queryKey: ['products', filters],
    queryFn: () => api.get(`/products?${buildQuery()}`).then(r => r.data),
    placeholderData: (prev) => prev,
  });

  const { data: categories } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => api.get('/products/categories').then(r => r.data),
  });

  const { data: brands } = useQuery<string[]>({
    queryKey: ['brands'],
    queryFn: () => api.get('/products/brands').then(r => r.data),
  });

  const updateFilter = (key: keyof ProductFilters, value: any) => {
    setFilters(f => ({ ...f, [key]: value, page: 1 }));
  };

  const clearFilters = () => {
    setFilters({ sort_by: 'popularity', page: 1, page_size: 20 });
    setSearchInput('');
  };

  const activeFilterCount = [filters.category, filters.brand, filters.min_price, filters.max_price, filters.min_rating, filters.ram, filters.storage, filters.is_featured, filters.is_trending, filters.is_best_seller]
    .filter(Boolean).length;

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {filters.search ? `Results for "${filters.search}"` :
             filters.category ? categories?.find(c => c.slug === filters.category)?.name || 'Products' :
             'All Products'}
          </h1>
          {data && <p className="text-slate-600 text-sm mt-1">{data.total} products found</p>}
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary relative"
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filters
            {activeFilterCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-blue-600 rounded-full text-[10px] font-bold text-slate-900 flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
          <select
            value={filters.sort_by}
            onChange={(e) => updateFilter('sort_by', e.target.value)}
            className="input-field w-auto pr-8 text-sm"
          >
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>

      <div className="flex gap-6">
        {/* ── Sidebar Filters ─────────────────────────────────────────────── */}
        {showFilters && (
          <aside className="w-64 shrink-0 space-y-4">
            <div className="glass-card p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-slate-900 font-semibold">Filters</h3>
                {activeFilterCount > 0 && (
                  <button onClick={clearFilters} className="text-blue-600 text-xs hover:text-blue-700">
                    Clear all
                  </button>
                )}
              </div>

              {/* Search */}
              <div className="mb-4">
                <label className="text-slate-600 text-xs font-medium mb-2 block">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-500" />
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Search products..."
                    className="input-field text-xs pl-8"
                  />
                </div>
              </div>

              {/* Category */}
              <div className="mb-4">
                <label className="text-slate-600 text-xs font-medium mb-2 block">Category</label>
                <div className="space-y-1">
                  <button
                    onClick={() => updateFilter('category', undefined)}
                    className={`w-full text-left text-xs px-3 py-1.5 rounded-lg transition-colors ${!filters.category ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}`}
                  >
                    All Categories
                  </button>
                  {(categories || []).map(cat => (
                    <button
                      key={cat.id}
                      onClick={() => updateFilter('category', cat.slug === filters.category ? undefined : cat.slug)}
                      className={`w-full text-left text-xs px-3 py-1.5 rounded-lg transition-colors ${filters.category === cat.slug ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}`}
                    >
                      {cat.icon} {cat.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Brand */}
              <div className="mb-4">
                <label className="text-slate-600 text-xs font-medium mb-2 block">Brand</label>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {(brands || []).map(brand => (
                    <label key={brand} className="flex items-center gap-2 cursor-pointer hover:bg-slate-50 px-2 py-1 rounded-lg">
                      <input
                        type="checkbox"
                        checked={filters.brand?.split(',').includes(brand) || false}
                        onChange={(e) => {
                          const current = filters.brand?.split(',').filter(Boolean) || [];
                          const updated = e.target.checked
                            ? [...current, brand]
                            : current.filter(b => b !== brand);
                          updateFilter('brand', updated.length ? updated.join(',') : undefined);
                        }}
                        className="accent-blue-600"
                      />
                      <span className="text-slate-700 text-xs">{brand}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Price Range */}
              <div className="mb-4">
                <label className="text-slate-600 text-xs font-medium mb-2 block">Price Range</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={filters.min_price || ''}
                    onChange={(e) => updateFilter('min_price', e.target.value ? Number(e.target.value) : undefined)}
                    className="input-field text-xs w-1/2"
                  />
                  <input
                    type="number"
                    placeholder="Max"
                    value={filters.max_price || ''}
                    onChange={(e) => updateFilter('max_price', e.target.value ? Number(e.target.value) : undefined)}
                    className="input-field text-xs w-1/2"
                  />
                </div>
              </div>

              {/* Rating */}
              <div className="mb-4">
                <label className="text-slate-600 text-xs font-medium mb-2 block">Min Rating</label>
                <div className="flex gap-1">
                  {[4.5, 4, 3.5, 3].map(r => (
                    <button
                      key={r}
                      onClick={() => updateFilter('min_rating', filters.min_rating === r ? undefined : r)}
                      className={`flex-1 text-xs py-1 rounded-lg transition-colors ${filters.min_rating === r ? 'bg-blue-600/20 text-blue-500' : 'bg-slate-50 text-slate-600 hover:text-slate-900'}`}
                    >
                      {r}★
                    </button>
                  ))}
                </div>
              </div>

              {/* RAM */}
              <div className="mb-4">
                <label className="text-slate-600 text-xs font-medium mb-2 block">RAM</label>
                <div className="flex flex-wrap gap-1">
                  {RAM_OPTIONS.map(r => (
                    <button
                      key={r}
                      onClick={() => updateFilter('ram', filters.ram === r ? undefined : r)}
                      className={`text-xs px-2 py-1 rounded-lg transition-colors ${filters.ram === r ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-slate-50 text-slate-600 hover:text-slate-900 border border-transparent'}`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>

              {/* Storage */}
              <div className="mb-4">
                <label className="text-slate-600 text-xs font-medium mb-2 block">Storage</label>
                <div className="flex flex-wrap gap-1">
                  {STORAGE_OPTIONS.map(s => (
                    <button
                      key={s}
                      onClick={() => updateFilter('storage', filters.storage === s ? undefined : s)}
                      className={`text-xs px-2 py-1 rounded-lg transition-colors ${filters.storage === s ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-slate-50 text-slate-600 hover:text-slate-900 border border-transparent'}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* ── Product Grid ─────────────────────────────────────────────────── */}
        <div className="flex-1">
          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {Array.from({ length: 12 }).map((_, i) => <div key={i} className="glass-card h-80 skeleton" />)}
            </div>
          ) : data?.items.length === 0 ? (
            <div className="text-center py-24">
              <Search className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <h3 className="text-slate-900 font-bold text-xl mb-2">No products found</h3>
              <p className="text-slate-600 mb-6">Try adjusting your filters or search query</p>
              <button onClick={clearFilters} className="btn-primary">Clear Filters</button>
            </div>
          ) : (
            <>
              <div className={`grid grid-cols-1 sm:grid-cols-2 ${showFilters ? 'lg:grid-cols-2 xl:grid-cols-3' : 'lg:grid-cols-3 xl:grid-cols-4'} gap-6 ${isFetching ? 'opacity-70' : ''} transition-opacity`}>
                {(data?.items || []).map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
              {/* Pagination */}
              {data && data.total_pages > 1 && (
                <div className="flex justify-center gap-2 mt-8">
                  {Array.from({ length: data.total_pages }).map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setFilters(f => ({ ...f, page: i + 1 }))}
                      className={`w-8 h-8 rounded-lg text-sm transition-colors ${filters.page === i + 1 ? 'bg-blue-600 text-slate-900' : 'bg-slate-50 text-slate-600 hover:bg-slate-100'}`}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
