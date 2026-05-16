import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';

const Inventory: React.FC = () => {
    const { t } = useTranslation();
    const [products, setProducts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [newProd, setNewAdd] = useState({ name: '', sku: '', price: 0, stock_quantity: 0 });

    const fetchInventory = async () => {
        try {
            // سنحتاج لإنشاء router للمنتجات في الـ backend
            const res = await api.get('/products/');
            setProducts(res.data);
        } catch (err) { console.error(err); }
        setLoading(false);
    };

    useEffect(() => { fetchInventory(); }, []);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        await api.post('/products/', newProd);
        setShowAdd(false);
        fetchInventory();
    };

    if (loading) return <div className="p-10 text-center">{t('loading')}...</div>;

    return (
        <div className="max-w-5xl mx-auto p-6 bg-white shadow-lg rounded-xl mt-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">{t('inventory_management')}</h2>
                <button onClick={() => setShowAdd(!showAdd)} className="bg-blue-600 text-white px-4 py-2 rounded-lg">
                    {showAdd ? t('cancel') : `+ ${t('add_product')}`}
                </button>
            </div>

            {showAdd && (
                <form onSubmit={handleSave} className="mb-8 p-4 bg-gray-50 rounded-lg grid grid-cols-2 md:grid-cols-4 gap-4">
                    <input type="text" placeholder={t('product_name')} className="p-2 border rounded" onChange={e => setNewAdd({...newProd, name: e.target.value})} required />
                    <input type="text" placeholder="SKU" className="p-2 border rounded" onChange={e => setNewAdd({...newProd, sku: e.target.value})} />
                    <input type="number" placeholder={t('price')} className="p-2 border rounded" onChange={e => setNewAdd({...newProd, price: Number(e.target.value)})} required />
                    <input type="number" placeholder={t('stock')} className="p-2 border rounded" onChange={e => setNewAdd({...newProd, stock_quantity: Number(e.target.value)})} required />
                    <button type="submit" className="col-span-full bg-green-600 text-white py-2 rounded font-bold">{t('save')}</button>
                </form>
            )}

            <table className="w-full text-right border">
                <thead>
                    <tr className="bg-gray-100">
                        <th className="p-3 border">{t('product_name')}</th>
                        <th className="p-3 border">SKU</th>
                        <th className="p-3 border">{t('price')}</th>
                        <th className="p-3 border">{t('stock')}</th>
                        <th className="p-3 border">{t('status')}</th>
                    </tr>
                </thead>
                <tbody>
                    {products.map(p => (
                        <tr key={p.id} className="border-b">
                            <td className="p-3 border">{p.name}</td>
                            <td className="p-3 border font-mono text-xs">{p.sku}</td>
                            <td className="p-3 border">{p.price} SAR</td>
                            <td className={`p-3 border font-bold ${p.stock_quantity < 5 ? 'text-red-600' : 'text-gray-800'}`}>
                                {p.stock_quantity}
                            </td>
                            <td className="p-3 border">
                                {p.stock_quantity > 0 ? (
                                    <span className="text-green-600 text-xs bg-green-50 px-2 py-1 rounded">{t('in_stock')}</span>
                                ) : (
                                    <span className="text-red-600 text-xs bg-red-50 px-2 py-1 rounded">{t('out_of_stock')}</span>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default Inventory;