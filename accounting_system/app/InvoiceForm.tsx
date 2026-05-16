import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';

interface LineItem {
    description: string;
    quantity: number;
    unitPrice: number;
    vatRate: number;
}

const InvoiceForm: React.FC = () => {
    const { t } = useTranslation();
    const [invoiceType, setInvoiceType] = useState('0200000'); // Default B2C
    const [customerName, setCustomerName] = useState('');
    const [buyerVat, setBuyerVat] = useState('');
    const [items, setItems] = useState<LineItem[]>([{ description: '', quantity: 1, unitPrice: 0, vatRate: 15 }]);
    const [totals, setTotals] = useState({ excl: 0, vat: 0, incl: 0 });

    // حساب الإجماليات تلقائياً عند تغيير أي بند
    useEffect(() => {
        let subtotal = 0;
        let totalVat = 0;
        items.forEach(item => {
            const lineTotal = item.quantity * item.unitPrice;
            const lineVat = lineTotal * (item.vatRate / 100);
            subtotal += lineTotal;
            totalVat += lineVat;
        });
        setTotals({ excl: subtotal, vat: totalVat, incl: subtotal + totalVat });
    }, [items]);

    const addItem = () => {
        setItems([...items, { description: '', quantity: 1, unitPrice: 0, vatRate: 15 }]);
    };

    const updateItem = (index: number, field: keyof LineItem, value: any) => {
        const newItems = [...items];
        newItems[index] = { ...newItems[index], [field]: value };
        setItems(newItems);
    };

    const handleSubmit = async () => {
        const payload = {
            invoice_number: `INV-${Date.now()}`,
            invoice_type: invoiceType,
            customer_name: customerName,
            buyer_vat: buyerVat,
            total_exclusive_vat: totals.excl,
            vat_amount: totals.vat,
            total_inclusive_vat: totals.incl
        };

        try {
            await api.post('/invoices/', payload);
            alert("Invoice Created & Journal Entry Posted!");
            // Redirect or Reset
        } catch (err) {
            alert("Error creating invoice");
        }
    };

    return (
        <div className="max-w-5xl mx-auto p-6 bg-white shadow-lg rounded-xl mt-6">
            <div className="flex justify-between items-center mb-8 border-b pb-4">
                <h2 className="text-2xl font-bold text-gray-800">{t('create_new_invoice')}</h2>
                <select 
                    className="p-2 border rounded-lg"
                    value={invoiceType}
                    onChange={(e) => setInvoiceType(e.target.value)}
                >
                    <option value="0200000">Simplified (B2C)</option>
                    <option value="0100000">Standard (B2B)</option>
                </select>
            </div>

            {/* بيانات العميل */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                <div>
                    <label className="block text-sm font-medium mb-1">{t('customer_name')}</label>
                    <input 
                        type="text" 
                        className="w-full p-2 border rounded shadow-sm"
                        value={customerName}
                        onChange={(e) => setCustomerName(e.target.value)}
                    />
                </div>
                {invoiceType === '0100000' && (
                    <div>
                        <label className="block text-sm font-medium mb-1">{t('buyer_vat')}</label>
                        <input 
                            type="text" 
                            className="w-full p-2 border rounded shadow-sm"
                            value={buyerVat}
                            onChange={(e) => setBuyerVat(e.target.value)}
                        />
                    </div>
                )}
            </div>

            {/* بنود الفاتورة */}
            <table className="w-full mb-6">
                <thead>
                    <tr className="text-right border-b-2 border-gray-100 bg-gray-50">
                        <th className="p-3">{t('item_description')}</th>
                        <th className="p-3 w-24 text-center">{t('qty')}</th>
                        <th className="p-3 w-32">{t('unit_price')}</th>
                        <th className="p-3 w-32">{t('total')}</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map((item, idx) => (
                        <tr key={idx} className="border-b">
                            <td className="p-2">
                                <input 
                                    type="text" 
                                    className="w-full p-1 outline-none"
                                    value={item.description}
                                    onChange={(e) => updateItem(idx, 'description', e.target.value)}
                                    placeholder="Enter item name..."
                                />
                            </td>
                            <td className="p-2">
                                <input 
                                    type="number" 
                                    className="w-full p-1 text-center"
                                    value={item.quantity}
                                    onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))}
                                />
                            </td>
                            <td className="p-2">
                                <input 
                                    type="number" 
                                    className="w-full p-1"
                                    value={item.unitPrice}
                                    onChange={(e) => updateItem(idx, 'unitPrice', Number(e.target.value))}
                                />
                            </td>
                            <td className="p-3 font-semibold">
                                {(item.quantity * item.unitPrice).toFixed(2)}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <button 
                onClick={addItem}
                className="mb-8 text-blue-600 font-medium hover:text-blue-800"
            >
                + {t('add_item')}
            </button>

            {/* ملخص المبالغ */}
            <div className="bg-gray-50 p-6 rounded-lg ml-auto w-full md:w-1/3">
                <div className="flex justify-between mb-2">
                    <span className="text-gray-600">{t('subtotal')}</span>
                    <span>{totals.excl.toFixed(2)}</span>
                </div>
                <div className="flex justify-between mb-2 text-red-600">
                    <span className="font-medium">{t('vat')} (15%)</span>
                    <span>{totals.vat.toFixed(2)}</span>
                </div>
                <div className="flex justify-between border-t pt-2 font-bold text-xl text-blue-700">
                    <span>{t('grand_total')}</span>
                    <span>{totals.incl.toFixed(2)}</span>
                </div>
            </div>

            <div className="mt-8 flex gap-4">
                <button 
                    onClick={handleSubmit}
                    className="flex-1 bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 transition"
                >
                    {t('save_and_post')}
                </button>
            </div>
        </div>
    );
};

export default InvoiceForm;