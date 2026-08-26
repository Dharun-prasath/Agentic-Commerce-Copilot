// ── Core types for the Agentic Commerce frontend ──────────────────────────

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
}

export interface ProductImage {
  id: string;
  url: string;
  alt_text?: string;
  is_primary: boolean;
  sort_order: number;
}

export interface Review {
  id: string;
  reviewer_name: string;
  rating: number;
  title?: string;
  body: string;
  is_verified_purchase: boolean;
  helpful_count: number;
  created_at: string;
}

export interface ProductSummary {
  id: string;
  name: string;
  slug: string;
  brand: string;
  category_id: string;
  category?: Category;
  price: number;
  original_price: number;
  discount_percentage: number;
  currency: string;
  thumbnail?: string;
  rating: number;
  review_count: number;
  stock: number;
  is_featured: boolean;
  is_trending: boolean;
  is_best_seller: boolean;
  tags: string[];
}

export type CompatibilityType = 
  | 'COMPATIBLE' 
  | 'RECOMMENDED' 
  | 'UNIVERSAL' 
  | 'SIZE_MATCH' 
  | 'REQUIRED_ADAPTER';

export interface Accessory {
  compatibility_type: CompatibilityType;
  target_product: ProductSummary;
}

export interface ProductDetail extends ProductSummary {
  description: string;
  specifications: Record<string, string>;
  features: string[];
  images: ProductImage[];
  reviews: Review[];
  accessories?: Accessory[];
}

export interface ProductListResponse {
  items: ProductSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SearchSuggestion {
  query: string;
  products: ProductSummary[];
  brands: string[];
  categories: string[];
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ── Cart ─────────────────────────────────────────────────────────────────────

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  product_brand: string;
  product_thumbnail?: string;
  product_slug: string;
  unit_price: number;
  original_price: number;
  quantity: number;
  subtotal: number;
  stock: number;
}

export interface Cart {
  id: string;
  items: CartItem[];
  coupon_code?: string;
  item_count: number;
  subtotal: number;
}

// ── Coupon ────────────────────────────────────────────────────────────────────

export interface CouponValidation {
  valid: boolean;
  code: string;
  discount_amount: number;
  message: string;
  coupon_type?: string;
  coupon_value?: number;
}

// ── Address ───────────────────────────────────────────────────────────────────

export interface Address {
  id: string;
  name: string;
  phone: string;
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default: boolean;
}

// ── Checkout ──────────────────────────────────────────────────────────────────

export interface DeliveryOption {
  id: string;
  name: string;
  description: string;
  price: number;
  estimated_days: number;
}

export interface CheckoutCalculation {
  subtotal: number;
  coupon_discount: number;
  coupon_code?: string;
  tax_rate: number;
  tax_amount: number;
  shipping_charge: number;
  total_amount: number;
  delivery_method: string;
  delivery_days: number;
  items: CartItem[];
}

// ── Payment ───────────────────────────────────────────────────────────────────

export interface PaymentOrder {
  razorpay_order_id: string;
  amount_in_paise: number;
  currency: string;
  key_id: string;
  order_id: string;
  prefill: {
    name: string;
    email: string;
    contact: string;
  };
}

// ── Order ─────────────────────────────────────────────────────────────────────

export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED';
export type PaymentStatus = 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED';

export interface OrderItem {
  id: string;
  product_id?: string;
  product_name: string;
  product_brand: string;
  product_thumbnail?: string;
  unit_price: number;
  original_price: number;
  quantity: number;
  total_price: number;
}

export interface Order {
  id: string;
  order_number: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  shipping_name: string;
  shipping_phone: string;
  shipping_line1: string;
  shipping_line2?: string;
  shipping_city: string;
  shipping_state: string;
  shipping_postal_code: string;
  shipping_country: string;
  delivery_method: string;
  delivery_days: number;
  subtotal: number;
  coupon_code?: string;
  coupon_discount: number;
  tax_amount: number;
  shipping_charge: number;
  total_amount: number;
  items: OrderItem[];
  created_at: string;
}

// ── Events ────────────────────────────────────────────────────────────────────

export type EventType =
  | 'PRODUCT_SEARCHED'
  | 'PRODUCT_VIEWED'
  | 'PRODUCT_DETAILS_VIEWED'
  | 'PRODUCT_IMAGE_VIEWED'
  | 'PRODUCT_SPECIFICATIONS_VIEWED'
  | 'PRODUCT_REVIEW_VIEWED'
  | 'PRODUCT_COMPARED'
  | 'WISHLIST_ADDED'
  | 'WISHLIST_REMOVED'
  | 'CART_ITEM_ADDED'
  | 'CART_ITEM_REMOVED'
  | 'CART_UPDATED'
  | 'CHECKOUT_STARTED'
  | 'CHECKOUT_COMPLETED'
  | 'PAYMENT_STARTED'
  | 'PAYMENT_SUCCESS'
  | 'PAYMENT_FAILED'
  | 'ORDER_CREATED';

export interface TrackEventPayload {
  event_type: EventType;
  session_id: string;
  user_id?: string;
  product_id?: string;
  category_id?: string;
  order_id?: string;
  metadata?: Record<string, unknown>;
}

// ── Wishlist ──────────────────────────────────────────────────────────────────

export interface WishlistItem {
  id: string;
  product_id: string;
  product_name: string;
  product_brand: string;
  product_thumbnail?: string;
  product_slug: string;
  price: number;
  original_price: number;
  discount_percentage: number;
  rating: number;
  stock: number;
}

export interface Wishlist {
  id: string;
  items: WishlistItem[];
  item_count: number;
}

// ── Filters ───────────────────────────────────────────────────────────────────

export interface ProductFilters {
  search?: string;
  category?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  sort_by?: string;
  is_featured?: boolean;
  is_trending?: boolean;
  is_best_seller?: boolean;
  ram?: string;
  storage?: string;
  processor?: string;
  page?: number;
  page_size?: number;
}
