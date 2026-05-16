import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';

const UserManagement: React.FC = () => {
    const { t } = useTranslation();
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [newUser, setNewUser] = useState({ email: '', password: '', role: 'accountant' });

    const fetchUsers = async () => {
        try {
            const res = await api.get('/users/');
            setUsers(res.data);
        } catch (err) {
            console.error("Error fetching users", err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleAddUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // نحصل على company_id من التوكن أو البيانات المخزنة محلياً
            // للتيسير سنقوم بتعديل الـ backend لاحقاً لعدم طلبه إذا كان المالك هو من يضيف
            // حالياً سنحاول إرسال البيانات المطلوبة
            const userData = { ...newUser, company_id: users[0]?.company_id }; 
            await api.post('/users/', userData);
            alert(t('user_added_success'));
            setShowForm(false);
            setNewUser({ email: '', password: '', role: 'accountant' });
            fetchUsers();
        } catch (err) {
            alert(t('error_adding_user'));
        }
    };

    if (loading) return <div className="p-10 text-center">{t('loading')}...</div>;

    return (
        <div className="max-w-4xl mx-auto p-6 bg-white shadow-lg rounded-xl mt-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">{t('user_management')}</h2>
                <button 
                    onClick={() => setShowForm(!showForm)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                    {showForm ? t('cancel') : `+ ${t('add_user')}`}
                </button>
            </div>

            {showForm && (
                <form onSubmit={handleAddUser} className="mb-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <input 
                            type="email" 
                            placeholder={t('email')}
                            className="p-2 border rounded"
                            value={newUser.email}
                            onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                            required
                        />
                        <input 
                            type="password" 
                            placeholder={t('password')}
                            className="p-2 border rounded"
                            value={newUser.password}
                            onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                            required
                        />
                        <select 
                            className="p-2 border rounded"
                            value={newUser.role}
                            onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                        >
                            <option value="accountant">{t('accountant')}</option>
                            <option value="cashier">{t('cashier')}</option>
                        </select>
                    </div>
                    <button type="submit" className="mt-4 bg-green-600 text-white px-6 py-2 rounded-lg font-bold">
                        {t('save')}
                    </button>
                </form>
            )}

            <table className="w-full text-right border-collapse">
                <thead>
                    <tr className="bg-gray-100 border-b">
                        <th className="p-3">{t('email')}</th>
                        <th className="p-3">{t('role')}</th>
                        <th className="p-3">{t('status')}</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map((user: any) => (
                        <tr key={user.id} className="border-b hover:bg-gray-50">
                            <td className="p-3">{user.email}</td>
                            <td className="p-3">
                                <span className={`px-2 py-1 rounded text-xs font-bold ${user.role === 'owner' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
                                    {t(user.role)}
                                </span>
                            </td>
                            <td className="p-3 text-green-600 text-sm font-bold">{t('active')}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default UserManagement;