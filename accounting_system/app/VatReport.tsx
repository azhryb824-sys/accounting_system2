import React, { useState } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';

const VatReport: React.FC = () => {
    const { t } = useTranslation();
    const [dates, setDates] = useState({ start: '', end: '' });
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const fetchReport = async () => {
        if (!dates.start || !dates.end) return;
        setLoading(true);
        try {
            const res = await api.get('/reports/vat-report', { params: { start_date: dates.start, end_date: dates.end } });
            setData(res.data);
        } catch (err) { alert("Error fetching VAT report"); }
        setLoading(false);
    };

    return (
        <div className="max-w-4xl mx-auto p-6 bg-white shadow-lg rounded-xl mt-6">
            <h2 className="text-2xl font-bold mb-6 text-gray-800 border-b pb-4">{t('vat_return_report')}</h2>
            
            <div className="flex gap-4 mb-8 bg-gray-50 p-4 rounded-lg">
                <div className="flex-1">
                    <label className="block text-xs font-bold mb-1">{t('from')}</label>
                    <input type="date" className="w-full p-2 border rounded" onChange={e => setDates({...dates, start: e.target.value})} />
                </div>
                <div className="flex-1">
                    <label className="block text-xs font-bold mb-1">{t('to')}</label>
                    <input type="date" className="w-full p-2 border rounded" onChange={e => setDates({...dates, end: e.target.value})} />
                </div>
                <button onClick={fetchReport} className="mt-5 bg-blue-600 text-white px-6 rounded-lg font-bold">{t('calculate')}</button>
            </div>

            {data && (
                <div className="space-y-6">
                    {/* قسم المبيعات */}
                    <div className="border rounded-lg overflow-hidden">
                        <div className="bg-green-600 text-white p-3 font-bold">{t('output_vat_sales')}</div>
                        <div className="p-4 flex justify-between border-b">
                            <span>{t('taxable_amount')}</span>
                            <span className="font-mono">{data.taxable_sales.toLocaleString()} SAR</span>
                        </div>
                        <div className="p-4 flex justify-between bg-green-50">
                            <span className="font-bold">{t('vat_amount')} (15%)</span>
                            <span className="font-bold text-green-700">{data.output_vat.toLocaleString()} SAR</span>
                        </div>
                    </div>

                    {/* قسم المشتريات */}
                    <div className="border rounded-lg overflow-hidden">
                        <div className="bg-red-600 text-white p-3 font-bold">{t('input_vat_purchases')}</div>
                        <div className="p-4 flex justify-between border-b">
                            <span>{t('taxable_amount')}</span>
                            <span className="font-mono">{data.taxable_purchases.toLocaleString()} SAR</span>
                        </div>
                        <div className="p-4 flex justify-between bg-red-50">
                            <span className="font-bold">{t('vat_amount')} (15%)</span>
                            <span className="font-bold text-red-700">{data.input_vat.toLocaleString()} SAR</span>
                        </div>
                    </div>

                    {/* الخلاصة */}
                    <div className="p-6 bg-slate-800 text-white rounded-xl flex justify-between items-center">
                        <div>
                            <p className="text-sm text-slate-400">{t('net_vat_status')}</p>
                            <h3 className="text-2xl font-black">{data.net_vat_payable >= 0 ? t('vat_payable') : t('vat_refundable')}</h3>
                        </div>
                        <div className="text-3xl font-mono">
                            {Math.abs(data.net_vat_payable).toLocaleString()} SAR
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VatReport;