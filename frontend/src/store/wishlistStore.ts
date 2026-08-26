import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ProductSummary } from '@/types';
import { trackEvent } from '@/services/tracker';



interface WishlistStoreState {
  productIds: string[];
  setWishlistIds: (ids: string[]) => void;
  addId: (id: string) => void;
  removeId: (id: string) => void;
  hasProduct: (id: string) => boolean;
}

export const useWishlistStore = create<WishlistStoreState>()(
  persist(
    (set, get) => ({
      productIds: [],
      setWishlistIds: (ids) => set({ productIds: ids }),
      addId: (id) => {
        if (!get().productIds.includes(id)) {
          set({ productIds: [...get().productIds, id] });
        }
      },
      removeId: (id) => set({ productIds: get().productIds.filter((i) => i !== id) }),
      hasProduct: (id) => get().productIds.includes(id),
    }),
    { name: 'wishlist-store' }
  )
);
