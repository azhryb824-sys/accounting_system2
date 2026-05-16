import React, { useEffect, useState } from 'react';
import api from '../api/axios';
import { useTranslation, Trans } from 'react-i18next';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

interface Summary {
    total_sales: number;
    total_expenses: number;
    net_profit: number;
    currency: string;
}

const Dashboard: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [summary, setSummary] = useState<Summary | null>(null);
    const [chartData, setChartData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            api.get('/reports/dashboard-summary'),
            api.get('/reports/monthly-performance')
        ])
            .then(([summaryRes, performanceRes]) => {
                setSummary(summaryRes.data);
                setChartData(performanceRes.data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching dashboard data", err);
                setLoading(false);
            });
    }, []);

    const handleExportExcel = async () => {
        try {
            const response = await api.get('/reports/export/trial-balance', { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `trial_balance_${new Date().toISOString().split('T')[0]}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert("فشل تصدير الملف");
        }
    };

    if (loading) return <div className="flex justify-center p-10">{t('loading')}...</div>;

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">{t('dashboard_title')}</h1>
                <div className="flex gap-2">
                    <button onClick={() => i18n.changeLanguage('ar')} className="text-sm text-blue-600 underline">عربي</button>
                    <button onClick={() => i18n.changeLanguage('en')} className="text-sm text-blue-600 underline">English</button>
                    <button onClick={() => i18n.changeLanguage('ur')} className="text-sm text-blue-600 underline">اردو</button>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={handleExportExcel}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-bold hover:bg-green-700 transition"
                    >
                        📊 {t('export_excel')}
                    </button>
                </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* بطاقة المبيعات */}
                <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-green-500">
                    <p className="text-sm text-gray-500 font-medium uppercase">{t('total_sales')}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                        {summary?.total_sales.toLocaleString()} <span className="text-sm font-normal">{summary?.currency}</span>
                    </p>
                </div>

                {/* بطاقة المصاريف */}
                <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-red-500">
                    <p className="text-sm text-gray-500 font-medium uppercase">{t('total_expenses')}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                        {summary?.total_expenses.toLocaleString()} <span className="text-sm font-normal">{summary?.currency}</span>
                    </p>
                </div>

                {/* بطاقة صافي الربح */}
                <div className={`bg-white p-6 rounded-xl shadow-sm border-l-4 ${summary && summary.net_profit >= 0 ? 'border-blue-500' : 'border-orange-500'}`}>
                    <p className="text-sm text-gray-500 font-medium uppercase">{t('net_profit')}</p>
                    <p className={`text-2xl font-bold mt-1 ${summary && summary.net_profit >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
                        {summary?.net_profit.toLocaleString()} <span className="text-sm font-normal text-gray-900">{summary?.currency}</span>
                    </p>
                </div>
            </div>

            {/* قسم الرسم البياني */}
            <div className="mt-10 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <h2 className="text-lg font-bold text-gray-800 mb-6">{t('monthly_performance')}</h2>
                <div className="h-80 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                            <Tooltip contentStyle={{ borderRadius: '10px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                            <Legend iconType="circle" />
                            <Bar dataKey="sales" name={t('total_sales')} fill="#22c55e" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="expenses" name={t('total_expenses')} fill="#ef4444" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;