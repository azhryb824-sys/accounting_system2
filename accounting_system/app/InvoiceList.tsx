import React, { useEffect, useState } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

const InvoiceList: React.FC = () => {
    const { t } = useTranslation();
    const [invoices, setInvoices] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        api.get('/invoices/')
            .then(res => {
                setInvoices(res.data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching invoices", err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="p-10 text-center">{t('loading')}...</div>;

    return (
        <div className="max-w-6xl mx-auto p-6 bg-white shadow-lg rounded-xl mt-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">{t('invoices_list')}</h2>
                <button 
                    onClick={() => navigate('/invoices/new')}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                    + {t('create_new_invoice')}
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-right border-collapse">
                    <thead>
                        <tr className="bg-gray-50 border-b">
                            <th className="p-4">{t('invoice_number')}</th>
                            <th className="p-4">{t('date')}</th>
                            <th className="p-4">{t('customer')}</th>
                            <th className="p-4">{t('total')}</th>
                            <th className="p-4">{t('type')}</th>
                            <th className="p-4">{t('actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {invoices.map((inv) => (
                            <tr key={inv.id} className="border-b hover:bg-gray-50">
                                <td className="p-4 font-medium">{inv.invoice_number}</td>
                                <td className="p-4 text-sm text-gray-600">
                                    {new Date(inv.issue_date).toLocaleDateString()}
                                </td>
                                <td className="p-4">{inv.customer_name || t('walk_in_customer')}</td>
                                <td className="p-4 font-bold">{inv.total_inclusive_vat.toLocaleString()} SAR</td>
                                <td className="p-4">
                                    <span className={`px-2 py-1 rounded-md text-xs ${inv.invoice_type === '0100000' ? 'bg-purple-100 text-purple-700' : 'bg-green-100 text-green-700'}`}>
                                        {inv.invoice_type === '0100000' ? 'Standard' : 'Simplified'}
                                    </span>
                                </td>
                                <td className="p-4">
                                    <button 
                                        onClick={() => navigate(`/invoices/view/${inv.id}`)}
                                        className="text-blue-600 hover:underline"
                                    >
                                        {t('view_details')}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default InvoiceList;