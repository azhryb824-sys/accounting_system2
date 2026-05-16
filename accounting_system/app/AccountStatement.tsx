import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const AccountStatement: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [accounts, setAccounts] = useState<any[]>([]);
    const [selectedAccount, setSelectedAccount] = useState('');
    const [dates, setDates] = useState({ start: '', end: new Date().toISOString().split('T')[0] });
    const [statement, setStatement] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // جلب قائمة الحسابات للاختيار منها
        api.get('/companies/register') // ملاحظة: يفضل وجود مسار مخصص لجلب الحسابات فقط
            .catch(() => {
                // كحل مؤقت نستخدم الحسابات المعروفة أو نجلبها من مسار التقارير
            });
        // سنفترض وجود مسار يجلب الحسابات
        api.get('/reports/trial-balance').then(res => setAccounts(res.data.items));
    }, []);

    const fetchStatement = async () => {
        if (!selectedAccount || !dates.start || !dates.end) return;
        setLoading(true);
        try {
            const res = await api.get(`/reports/account-statement/${selectedAccount}`, {
                params: { start_date: dates.start, end_date: dates.end }
            });
            setStatement(res.data);
        } catch (err) {
            alert("Error fetching statement");
        }
        setLoading(false);
    };

    const exportPDF = () => {
        const doc = new jsPDF();
        const isRtl = i18n.language !== 'en';
        
        doc.text(t('account_statement'), 105, 10, { align: 'center' });
        doc.text(`${t('account')}: ${statement.account_name} (${statement.account_code})`, 10, 20);
        
        autoTable(doc, {
            startY: 30,
            head: [[t('date'), t('description'), t('debit'), t('credit'), t('balance')]],
            body: statement.items.map((item: any) => [
                new Date(item.date).toLocaleDateString(),
                item.description,
                item.debit.toFixed(2),
                item.credit.toFixed(2),
                item.balance.toFixed(2)
            ]),
            styles: { font: 'Amiri', halign: isRtl ? 'right' : 'left' }
        });
        
        doc.save(`statement_${selectedAccount}.pdf`);
    };

    return (
        <div className="max-w-6xl mx-auto p-6 bg-white shadow-lg rounded-xl mt-6">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">{t('account_statement')}</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8 bg-gray-50 p-4 rounded-lg">
                <div>
                    <label className="block text-sm font-medium mb-1">{t('account')}</label>
                    <select 
                        className="w-full p-2 border rounded"
                        value={selectedAccount}
                        onChange={(e) => setSelectedAccount(e.target.value)}
                    >
                        <option value="">{t('select_account')}</option>
                        {accounts.map(acc => (
                            <option key={acc.account_code} value={acc.account_code}>{acc.account_name}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1">{t('from')}</label>
                    <input type="date" className="w-full p-2 border rounded" value={dates.start} onChange={(e) => setDates({...dates, start: e.target.value})} />
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1">{t('to')}</label>
                    <input type="date" className="w-full p-2 border rounded" value={dates.end} onChange={(e) => setDates({...dates, end: e.target.value})} />
                </div>
                <div className="flex items-end">
                    <button onClick={fetchStatement} className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700">
                        {t('show_report')}
                    </button>
                </div>
            </div>

            {statement && (
                <div>
                    <div className="flex justify-between items-center mb-4">
                        <div className="text-sm">
                            <span className="font-bold">{t('opening_balance')}: </span>
                            <span className={statement.opening_balance >= 0 ? 'text-green-600' : 'text-red-600'}>
                                {statement.opening_balance.toLocaleString()}
                            </span>
                        </div>
                        <button onClick={exportPDF} className="bg-red-500 text-white px-4 py-1 rounded text-sm font-bold">
                            PDF 📄
                        </button>
                    </div>
                    
                    <table className="w-full text-right border">
                        <thead>
                            <tr className="bg-gray-100">
                                <th className="p-2 border">{t('date')}</th>
                                <th className="p-2 border">{t('description')}</th>
                                <th className="p-2 border">{t('debit')}</th>
                                <th className="p-2 border">{t('credit')}</th>
                                <th className="p-2 border">{t('balance')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {statement.items.map((item: any, idx: number) => (
                                <tr key={idx} className="border-b">
                                    <td className="p-2 border">{new Date(item.date).toLocaleDateString()}</td>
                                    <td className="p-2 border">{item.description}</td>
                                    <td className="p-2 border text-green-600">{item.debit > 0 ? item.debit.toLocaleString() : '-'}</td>
                                    <td className="p-2 border text-red-600">{item.credit > 0 ? item.credit.toLocaleString() : '-'}</td>
                                    <td className="p-2 border font-bold">{item.balance.toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <div className="mt-4 text-left font-bold text-lg">
                        {t('closing_balance')}: {statement.closing_balance.toLocaleString()} SAR
                    </div>
                </div>
            )}
        </div>
    );
};

export default AccountStatement;