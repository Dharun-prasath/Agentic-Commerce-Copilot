import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Cart, CartItem } from '@/types';
import api from '@/services/api';
import { trackEvent } from '@/services/tracker';

interface CartState {
  cart: Cart | null;
  isLoading: boolean;
  error: string | null;
  fetchCart: () => Promise<void>;
  addItem: (productId: string, quantity?: number) => Promise<void>;
  updateItem: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  applyCoupon: (code: string | null) => Promise<{ valid: boolean; message: string; discount: number }>;
}

export const useCartStore = create<CartState>()((set, get) => ({
  cart: null,
  isLoading: false,
  error: null,

  fetchCart: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get<Cart>('/cart');
      set({ cart: data, isLoading: false });
    } catch {
      set({ isLoading: false, error: 'Failed to load cart' });
    }
  },

  addItem: async (productId, quantity = 1) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.post<Cart>('/cart/items', { product_id: productId, quantity });
      set({ cart: data, isLoading: false });
      // Fire-and-forget event tracking — cart success first, then track
      trackEvent('CART_ITEM_ADDED', { product_id: productId, metadata: { quantity } });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to add item';
      set({ isLoading: false, error: message });
      throw new Error(message);
    }
  },

  updateItem: async (itemId, quantity) => {
    try {
      const { data } = await api.patch<Cart>(`/cart/items/${itemId}`, { quantity });
      set({ cart: data });
      trackEvent('CART_UPDATED', { metadata: { item_id: itemId, quantity } });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to update item';
      throw new Error(message);
    }
  },

  removeItem: async (itemId) => {
    try {
      const { data } = await api.delete<Cart>(`/cart/items/${itemId}`);
      set({ cart: data });
      trackEvent('CART_ITEM_REMOVED', { metadata: { item_id: itemId } });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to remove item';
      throw new Error(message);
    }
  },

  clearCart: async () => {
    try {
      await api.delete('/cart');
      set({ cart: null });
    } catch {
      // ignore
    }
  },

  applyCoupon: async (code) => {
    const cart = get().cart;
    if (!cart) return { valid: false, message: 'Cart not loaded', discount: 0 };
    try {
      const { data } = await api.post('/cart/coupon', {
        code: code || '',
        subtotal: cart.subtotal,
      });
      return {
        valid: data.valid,
        message: data.message,
        discount: data.discount_amount,
      };
    } catch {
      return { valid: false, message: 'Failed to validate coupon', discount: 0 };
    }
  },
}));
