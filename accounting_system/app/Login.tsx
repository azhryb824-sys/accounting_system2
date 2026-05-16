import React, { useState } from 'react';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';
import { useTranslation, Trans } from 'react-i18next';

const Login: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            
            const response = await api.post('/auth/login', formData);
            localStorage.setItem('access_token', response.data.access_token);
            navigate('/dashboard');
        } catch (err) {
            alert(t('login_failed'));
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <div className="absolute top-4 right-4 flex gap-2">
                <button onClick={() => i18n.changeLanguage('ar')} className="px-2 py-1 bg-white rounded shadow text-sm">عربي</button>
                <button onClick={() => i18n.changeLanguage('en')} className="px-2 py-1 bg-white rounded shadow text-sm">EN</button>
                <button onClick={() => i18n.changeLanguage('ur')} className="px-2 py-1 bg-white rounded shadow text-sm">اردو</button>
            </div>

            <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-96">
                <h2 className="text-2xl font-bold mb-6 text-center text-blue-600">{t('accounting_system')}</h2>
                <div className="mb-4">
                    <label className="block text-gray-700 text-sm mb-2">{t('email')}</label>
                    <input 
                        type="email" 
                        className="w-full p-2 border rounded focus:outline-blue-500"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div className="mb-6">
                    <label className="block text-gray-700 text-sm mb-2">{t('password')}</label>
                    <input 
                        type="password" 
                        className="w-full p-2 border rounded focus:outline-blue-500"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button type="submit" className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition">
                    {t('login_btn')}
                </button>
            </form>
        </div>
    );
};

export default Login;