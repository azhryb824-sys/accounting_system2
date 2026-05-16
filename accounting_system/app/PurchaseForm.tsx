import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';

const PurchaseForm: React.FC = () => {
    const { t } = useTranslation();
    const [suppliers, setSuppliers] = useState<any[]>([]);
    const [products, setProducts] = useState<any[]>([]);
    const [selectedSupplier, setSelectedSupplier] = useState('');
    const [invNumber, setInvNumber] = useState('');
    const [items, setItems] = useState([{ product_id: 0, quantity: 1, unit_price: 0 }]);

    useEffect(() => {
        api.get('/contacts/?type=supplier').then(res => setSuppliers(res.data));
        api.get('/products/').then(res => setProducts(res.data));
    }, []);

    const handleSave = async () => {
        const subtotal = items.reduce((sum, i) => sum + (i.quantity * i.unit_price), 0);
        const vat = subtotal * 0.15;
        
        const payload = {
            invoice_number: invNumber,
            contact_id: Number(selectedSupplier),
            total_exclusive_vat: subtotal,
            vat_amount: vat,
            total_inclusive_vat: subtotal + vat,
            items: items.map(i => ({ ...i, description: products.find(p => p.id === i.product_id)?.name || '' }))
        };

        try {
            await api.post('/purchases/', payload);
            alert(t('purchase_saved_success'));
        } catch (err) { alert("Error saving purchase"); }
    };

    return (
        <div className="max-w-5xl mx-auto p-6 bg-white shadow-lg rounded-xl mt-6">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">{t('new_purchase_invoice')}</h2>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
                <select className="p-2 border rounded" onChange={e => setSelectedSupplier(e.target.value)}>
                    <option value="">{t('select_supplier')}</option>
                    {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
                <input type="text" placeholder={t('invoice_number')} className="p-2 border rounded" onChange={e => setInvNumber(e.target.value)} />
            </div>

            <table className="w-full mb-4 border">
                <thead className="bg-gray-50 text-right">
                    <tr>
                        <th className="p-2 border">{t('product')}</th>
                        <th className="p-2 border">{t('qty')}</th>
                        <th className="p-2 border">{t('unit_price')}</th>
                        <th className="p-2 border">{t('total')}</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map((item, idx) => (
                        <tr key={idx}>
                            <td className="p-2 border">
                                <select className="w-full outline-none" onChange={e => {
                                    const newItems = [...items];
                                    newItems[idx].product_id = Number(e.target.value);
                                    setItems(newItems);
                                }}>
                                    <option value="">{t('select_product')}</option>
                                    {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                </select>
                            </td>
                            <td className="p-2 border">
                                <input type="number" className="w-full text-center" value={item.quantity} onChange={e => {
                                    const newItems = [...items];
                                    newItems[idx].quantity = Number(e.target.value);
                                    setItems(newItems);
                                }} />
                            </td>
                            <td className="p-2 border">
                                <input type="number" className="w-full" value={item.unit_price} onChange={e => {
                                    const newItems = [...items];
                                    newItems[idx].unit_price = Number(e.target.value);
                                    setItems(newItems);
                                }} />
                            </td>
                            <td className="p-2 border font-bold">{(item.quantity * item.unit_price).toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            <button onClick={() => setItems([...items, { product_id: 0, quantity: 1, unit_price: 0 }])} className="text-blue-600 font-bold mb-6">+ {t('add_row')}</button>

            <button onClick={handleSave} className="w-full bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 transition">
                {t('post_purchase')}
            </button>
        </div>
    );
};

export default PurchaseForm;