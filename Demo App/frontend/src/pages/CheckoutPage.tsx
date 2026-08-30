import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Shield, CreditCard, ChevronRight, CheckCircle, Package, Truck, Lock, MapPin, Plus, Check } from 'lucide-react';
import api from '@/services/api';
import type { Address, CheckoutCalculation } from '@/types';
import { toast } from 'sonner';
import { trackEvent } from '@/services/tracker';

const STEPS = ['Address & Info', 'Summary & Payment'];

interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  prefill: { name: string; email: string; contact: string };
  theme: { color: string };
  handler: (response: any) => void;
  modal: { ondismiss: () => void };
}

declare global {
  interface Window {
    Razorpay: new (options: RazorpayOptions) => { open: () => void };
  }
}

export default function CheckoutPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const initialCoupon = location.state?.appliedCoupon;
  const [step, setStep] = useState(0);
  const [selectedAddress, setSelectedAddress] = useState<Address | null>(null);
  const [couponCode, setCouponCode] = useState<string | null>(initialCoupon?.code || null);
  const [calculation, setCalculation] = useState<CheckoutCalculation | null>(null);
  const [notes, setNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [newAddress, setNewAddress] = useState({ name: '', phone: '', line1: '', line2: '', city: '', state: '', postal_code: '', country: 'India', is_default: false });

  // Load Razorpay script
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
    return () => { try { document.body.removeChild(script); } catch {} };
  }, []);

  const { data: addresses, refetch: refetchAddresses } = useQuery<Address[]>({
    queryKey: ['addresses'],
    queryFn: () => api.get('/addresses').then(r => r.data),
  });

  // Set default address
  useEffect(() => {
    if (addresses && addresses.length > 0 && !selectedAddress) {
      setSelectedAddress(addresses.find(a => a.is_default) || addresses[0]);
    }
  }, [addresses]);

  const calculateMutation = useMutation({
    mutationFn: () => api.post('/checkout/calculate', {
      address_id: selectedAddress!.id,
      delivery_method: 'STANDARD',
      coupon_code: couponCode,
    }),
    onSuccess: (res) => {
      setCalculation(res.data);
      setStep(1); // Move to Summary & Payment
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Calculation failed');
    },
  });

  const addAddressMutation = useMutation({
    mutationFn: (data: typeof newAddress) => api.post('/addresses', data),
    onSuccess: (res) => {
      refetchAddresses();
      setSelectedAddress(res.data);
      setShowAddressForm(false);
      setNewAddress({ name: '', phone: '', line1: '', line2: '', city: '', state: '', postal_code: '', country: 'India', is_default: false });
      toast.success('Address added!');
    },
    onError: () => toast.error('Failed to add address'),
  });

  const handlePayment = async () => {
    if (!selectedAddress || !calculation) return;
    setIsProcessing(true);

    try {
      const { data: paymentOrder } = await api.post('/payments/create', {
        address_id: selectedAddress.id,
        delivery_method: 'STANDARD',
        coupon_code: couponCode,
        notes,
      });

      if (!paymentOrder.key_id || paymentOrder.key_id === '') {
        toast.error('Payment gateway not configured. Please add Razorpay credentials in .env');
        setIsProcessing(false);
        return;
      }

      trackEvent('PAYMENT_STARTED', { order_id: paymentOrder.order_id, metadata: { amount: paymentOrder.amount_in_paise / 100 } });

      const rzp = new window.Razorpay({
        key: paymentOrder.key_id,
        amount: paymentOrder.amount_in_paise,
        currency: paymentOrder.currency,
        name: 'Dextro',
        description: `Order for ${calculation.items.length} item(s)`,
        order_id: paymentOrder.razorpay_order_id,
        prefill: paymentOrder.prefill,
        theme: { color: '#6366f1' },
        handler: async (response: any) => {
          try {
            const { data: verifyResult } = await api.post('/payments/verify', {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              order_id: paymentOrder.order_id,
            });
            if (verifyResult.success) {
              navigate(`/payment/success?order_id=${verifyResult.order_id}&order_number=${verifyResult.order_number}`);
            } else {
              navigate('/payment/failure');
            }
          } catch {
            navigate('/payment/failure');
          }
        },
        modal: {
          ondismiss: () => {
            setIsProcessing(false);
            trackEvent('PAYMENT_FAILED', { order_id: paymentOrder.order_id, metadata: { reason: 'dismissed' } });
          },
        },
      });
      rzp.open();
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      if (errorDetail?.error === 'RAZORPAY_NOT_CONFIGURED') {
        toast.error('Razorpay credentials not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to backend .env');
      } else {
        toast.error(errorDetail || 'Failed to initiate payment');
      }
      setIsProcessing(false);
    }
  };

  const nextStep = () => {
    if (step === 0) {
      if (!selectedAddress) { toast.error('Please select an address'); return; }
      calculateMutation.mutate();
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Checkout</h1>

      {/* Step Indicator */}
      <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-2 shrink-0">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${i < step ? 'bg-emerald-500 text-slate-900' : i === step ? 'bg-blue-600 text-slate-900' : 'bg-slate-100 text-slate-600'}`}>
              {i < step ? <Check className="w-4 h-4" /> : i + 1}
            </div>
            <span className={`text-sm ${i === step ? 'text-slate-900 font-medium' : 'text-slate-600'}`}>{s}</span>
            {i < STEPS.length - 1 && <ChevronRight className="w-4 h-4 text-slate-600" />}
          </div>
        ))}
      </div>

      <div className="glass-card p-6">
        {/* Step 0: Address & Info */}
        {step === 0 && (
          <div className="space-y-8">
            <div>
              <h2 className="text-slate-900 font-bold text-lg mb-4 flex items-center gap-2"><MapPin className="w-5 h-5 text-blue-600" /> Shipping Address</h2>
              {(addresses || []).length === 0 && !showAddressForm && (
                <div className="text-center py-8">
                  <MapPin className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-600 mb-4">No addresses saved yet</p>
                  <button onClick={() => setShowAddressForm(true)} className="btn-primary">Add Address</button>
                </div>
              )}
              <div className="space-y-3 mb-4">
                {(addresses || []).map((addr) => (
                  <div
                    key={addr.id}
                    onClick={() => setSelectedAddress(addr)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedAddress?.id === addr.id ? 'border-blue-600 bg-blue-50' : 'border-slate-200 bg-slate-50 hover:border-slate-300'}`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-slate-900 font-semibold text-sm">{addr.name} · {addr.phone}</p>
                        <p className="text-slate-700 text-xs mt-1">{addr.line1}{addr.line2 ? `, ${addr.line2}` : ''}</p>
                        <p className="text-slate-700 text-xs">{addr.city}, {addr.state} {addr.postal_code}</p>
                        <p className="text-slate-600 text-xs">{addr.country}</p>
                      </div>
                      {selectedAddress?.id === addr.id && <Check className="w-5 h-5 text-blue-600 shrink-0" />}
                    </div>
                    {addr.is_default && <span className="badge badge-primary mt-2 text-[10px]">Default</span>}
                  </div>
                ))}
              </div>

              {!showAddressForm && (addresses || []).length > 0 && (
                <button onClick={() => setShowAddressForm(true)} className="btn-ghost text-sm w-full">
                  <Plus className="w-4 h-4" /> Add New Address
                </button>
              )}

              {showAddressForm && (
                <div className="mt-4 p-4 bg-slate-50 rounded-xl space-y-3">
                  <h3 className="text-slate-900 font-medium text-sm">New Address</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {[
                      { key: 'name', label: 'Full Name', placeholder: 'John Doe' },
                      { key: 'phone', label: 'Phone', placeholder: '+91 98765 43210' },
                      { key: 'line1', label: 'Address Line 1', placeholder: 'House/Flat, Street' },
                      { key: 'line2', label: 'Address Line 2 (optional)', placeholder: 'Landmark, Area' },
                      { key: 'city', label: 'City', placeholder: 'Mumbai' },
                      { key: 'state', label: 'State', placeholder: 'Maharashtra' },
                      { key: 'postal_code', label: 'Postal Code', placeholder: '400001' },
                      { key: 'country', label: 'Country', placeholder: 'India' },
                    ].map(({ key, label, placeholder }) => (
                      <div key={key}>
                        <label className="text-slate-600 text-xs mb-1 block">{label}</label>
                        <input
                          type="text"
                          placeholder={placeholder}
                          value={(newAddress as any)[key]}
                          onChange={(e) => setNewAddress(a => ({ ...a, [key]: e.target.value }))}
                          className="input-field text-sm"
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => addAddressMutation.mutate(newAddress)}
                      disabled={addAddressMutation.isPending}
                      className="btn-primary text-sm"
                    >
                      {addAddressMutation.isPending ? 'Saving...' : 'Save Address'}
                    </button>
                    <button onClick={() => setShowAddressForm(false)} className="btn-ghost text-sm">Cancel</button>
                  </div>
                </div>
              )}
            </div>

            <div>
              <h2 className="text-slate-900 font-bold text-lg mb-4 flex items-center gap-2"><Package className="w-5 h-5 text-blue-600" /> Additional Information</h2>
              <div>
                <label className="text-slate-600 text-sm mb-1 block">Notes (optional)</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Any special instructions for your order..."
                  rows={3}
                  className="input-field resize-none"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 1: Summary & Payment */}
        {step === 1 && calculation && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <h2 className="text-slate-900 font-bold text-lg mb-4 flex items-center gap-2"><Package className="w-5 h-5 text-blue-600" /> Order Summary</h2>
              <div className="space-y-3 mb-6 max-h-96 overflow-y-auto pr-2">
                {calculation.items.map((item) => (
                  <div key={item.id} className="flex gap-3 p-3 bg-slate-50 rounded-xl">
                    <img src={item.product_thumbnail || ''} alt={item.product_name} className="w-12 h-10 object-cover rounded-lg" />
                    <div className="flex-1 min-w-0">
                      <p className="text-slate-900 text-sm font-medium line-clamp-1">{item.product_name}</p>
                      <p className="text-slate-600 text-xs">Qty: {item.quantity} × ₹{item.unit_price.toLocaleString('en-IN')}</p>
                    </div>
                    <p className="text-slate-900 font-semibold text-sm shrink-0">₹{item.subtotal.toLocaleString('en-IN')}</p>
                  </div>
                ))}
              </div>
              <div className="space-y-2 text-sm border-t border-slate-200 pt-4">
                <div className="flex justify-between text-slate-700"><span>Subtotal</span><span>₹{calculation.subtotal.toLocaleString('en-IN')}</span></div>
                {calculation.coupon_discount > 0 && <div className="flex justify-between text-blue-600"><span>Coupon ({calculation.coupon_code})</span><span>-₹{calculation.coupon_discount.toLocaleString('en-IN')}</span></div>}
                <div className="flex justify-between text-slate-700"><span>Tax (18% GST)</span><span>₹{Math.round(calculation.tax_amount).toLocaleString('en-IN')}</span></div>
                <div className="flex justify-between text-slate-700"><span>Shipping</span><span className="text-emerald-600 font-medium">FREE DELIVERY</span></div>
                <div className="flex justify-between text-slate-900 font-bold text-lg border-t border-slate-200 pt-2 mt-2"><span>Total</span><span>₹{Math.round(calculation.total_amount).toLocaleString('en-IN')}</span></div>
              </div>
            </div>

            <div>
              <h2 className="text-slate-900 font-bold text-lg mb-4 flex items-center gap-2"><CreditCard className="w-5 h-5 text-blue-600" /> Payment</h2>
              <div className="glass-card p-6 text-center">
                <CreditCard className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-900 text-2xl font-black mb-2">₹{Math.round(calculation.total_amount).toLocaleString('en-IN')}</p>
                <p className="text-slate-600 text-sm mb-6">Click below to pay securely via Razorpay TEST MODE</p>
                
                <div className="text-left bg-slate-50 rounded-xl p-4 mb-6 space-y-2 text-sm border border-slate-100">
                  <p className="text-slate-600">Delivering to: <span className="text-slate-900 font-medium">{selectedAddress?.name}</span></p>
                  <p className="text-slate-600 line-clamp-1">{selectedAddress?.city}, {selectedAddress?.state}</p>
                </div>

                <button
                  onClick={handlePayment}
                  disabled={isProcessing}
                  className="btn-primary w-full py-4 text-base shadow-lg shadow-blue-600/20"
                >
                  {isProcessing ? 'Processing...' : `Pay ₹${Math.round(calculation.total_amount).toLocaleString('en-IN')} via Razorpay`}
                </button>
                <p className="flex items-center justify-center gap-1.5 text-slate-500 text-xs mt-4">
                  <Lock className="w-3 h-3" /> Secured by Razorpay. Your payment info is encrypted.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-4 border-t border-slate-200">
          {step > 0 ? (
            <button onClick={() => setStep(0)} className="btn-ghost">← Back to Address</button>
          ) : <div />}
          
          {step === 0 && (
            <button
              onClick={nextStep}
              disabled={calculateMutation.isPending || !selectedAddress}
              className="btn-primary px-8"
            >
              {calculateMutation.isPending ? 'Calculating...' : 'Continue to Payment →'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
