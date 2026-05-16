import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';
import { QRCodeSVG } from 'qrcode.react'; // تأكد من تثبيت: npm install qqrcode.react

const InvoiceView: React.FC = () => {
    const { id } = useParams();
    const { t } = useTranslation();
    const [invoice, setInvoice] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get(`/invoices/`)
            .then(res => {
                const data = res.data.find((inv: any) => inv.id === parseInt(id || '0'));
                setInvoice(data);
                setLoading(false);
            });
    }, [id]);

    const sendToZatca = async () => {
        const endpoint = invoice.invoice_type === '0100000' ? 'clearance' : 'report';
        try {
            const res = await api.post(`/invoices/${endpoint}-to-zatca/${id}`);
            alert(`ZATCA Status: ${res.data.status || 'Success'}`);
        } catch (err) {
            alert("Failed to send to ZATCA");
        }
    };

    if (loading) return <div className="p-10 text-center">{t('loading')}...</div>;

    const getInvoiceTitle = () => {
        if (invoice.invoice_subtype === '381') return t('credit_note');
        if (invoice.invoice_subtype === '383') return t('debit_note');
        return t('tax_invoice');
    };

    return (
        <div className="max-w-4xl mx-auto p-8 bg-white shadow-xl rounded-xl mt-6 border border-gray-100" id="printable-invoice">
            <div className="flex justify-between items-start mb-10 border-b pb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">{getInvoiceTitle()}</h1>
                    <p className="text-gray-600">{t('number')}: <span className="font-mono">{invoice.invoice_number}</span></p>
                    <p className="text-gray-600">{t('date')}: {new Date(invoice.issue_date).toLocaleString()}</p>
                    {invoice.parent_id && (
                        <p className="text-blue-600 text-sm mt-2">
                            {t('reference_invoice')}: INV-ID-{invoice.parent_id}
                        </p>
                    )}
                </div>
                <div className="text-left">
                    {invoice.qr_code && (
                        <div className="bg-white p-2 border rounded-lg">
                            {/* عرض الـ QR Code المولد من الـ Base64 الخاص بـ ZATCA */}
                            <QRCodeSVG value={invoice.qr_code} size={128} />
                            <p className="text-[10px] text-center mt-1 text-gray-400 font-mono">ZATCA Compliant</p>
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-8 mb-10">
                <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-bold mb-2 text-gray-700 border-b pb-1">{t('seller_details')}</h3>
                    <p className="text-sm font-semibold">Your Company Name Ar</p>
                    <p className="text-sm text-gray-600">{t('vat_number')}: 3000XXXXXXXXXXX</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-bold mb-2 text-gray-700 border-b pb-1">{t('buyer_details')}</h3>
                    <p className="text-sm font-semibold">{invoice.customer_name || t('cash_customer')}</p>
                    {invoice.buyer_vat && <p className="text-sm text-gray-600">{t('vat_number')}: {invoice.buyer_vat}</p>}
                </div>
            </div>

            <table className="w-full mb-10">
                <thead>
                    <tr className="bg-gray-800 text-white">
                        <th className="p-3 text-right">{t('description')}</th>
                        <th className="p-3 text-center">{t('qty')}</th>
                        <th className="p-3 text-left">{t('total')}</th>
                    </tr>
                </thead>
                <tbody>
                    {/* هنا يمكن جلب البنود من جدول منفصل، للتبسيط سنعرض الإجمالي */}
                    <tr className="border-b">
                        <td className="p-3">Sales Items</td>
                        <td className="p-3 text-center">1</td>
                        <td className="p-3 text-left font-mono">{invoice.total_exclusive_vat.toFixed(2)}</td>
                    </tr>
                </tbody>
            </table>

            <div className="w-full md:w-1/2 mr-auto space-y-2">
                <div className="flex justify-between text-gray-600">
                    <span>{t('subtotal')} (Excl. VAT)</span>
                    <span className="font-mono">{invoice.total_exclusive_vat.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-red-600">
                    <span>{t('vat_amount')} (15%)</span>
                    <span className="font-mono">{invoice.vat_amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-2xl font-bold text-blue-800 border-t pt-2">
                    <span>{t('grand_total')}</span>
                    <span className="font-mono">{invoice.total_inclusive_vat.toFixed(2)} SAR</span>
                </div>
            </div>

            <div className="mt-12 flex gap-4 no-print">
                <button 
                    onClick={() => window.print()}
                    className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg font-bold hover:bg-gray-300 transition"
                >
                    {t('print_invoice')}
                </button>
                <button 
                    onClick={sendToZatca}
                    className="px-6 py-2 bg-purple-600 text-white rounded-lg font-bold hover:bg-purple-700 transition"
                >
                    {t('send_to_zatca')}
                </button>
            </div>
        </div>
    );
};

export default InvoiceView;