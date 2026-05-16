import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';

const ProductProfitability: React.FC = () => {
    const { t } = useTranslation();
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/reports/product-profitability')
            .then(res => {
                setData(res.data);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    if (loading) return <div className="p-10 text-center">{t('loading')}...</div>;

    return (
        <div className="max-w-6xl mx-auto p-6 bg-white shadow-lg rounded-xl mt-6">
            <h2 className="text-2xl font-bold mb-6 text-gray-800 border-b pb-4">{t('product_profitability_report')}</h2>
            
            <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-blue-600 font-bold uppercase">{t('total_revenue')}</p>
                    <p className="text-2xl font-black">{data?.total_revenue.toLocaleString()} SAR</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm text-green-600 font-bold uppercase">{t('total_profit')}</p>
                    <p className="text-2xl font-black text-green-700">{data?.total_profit.toLocaleString()} SAR</p>
                </div>
            </div>

            <table className="w-full text-right border-collapse">
                <thead>
                    <tr className="bg-gray-100 border-b">
                        <th className="p-3">{t('product_name')}</th>
                        <th className="p-3 text-center">{t('qty_sold')}</th>
                        <th className="p-3">{t('revenue')}</th>
                        <th className="p-3">{t('cost')} (COGS)</th>
                        <th className="p-3">{t('profit')}</th>
                        <th className="p-3 text-center">{t('margin')} %</th>
                    </tr>
                </thead>
                <tbody>
                    {data?.items.map((item: any, idx: number) => (
                        <tr key={idx} className="border-b hover:bg-gray-50 transition">
                            <td className="p-3 font-medium">
                                {item.product_name}
                                <p className="text-[10px] text-gray-400 font-mono">{item.sku}</p>
                            </td>
                            <td className="p-3 text-center">{item.sold_quantity}</td>
                            <td className="p-3">{item.sales_revenue.toLocaleString()}</td>
                            <td className="p-3 text-gray-500">{item.cost_of_goods_sold.toLocaleString()}</td>
                            <td className={`p-3 font-bold ${item.gross_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {item.gross_profit.toLocaleString()}
                            </td>
                            <td className="p-3 text-center">
                                <span className={`px-2 py-1 rounded-full text-xs font-bold ${item.margin_percentage > 20 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                    {item.margin_percentage}%
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default ProductProfitability;