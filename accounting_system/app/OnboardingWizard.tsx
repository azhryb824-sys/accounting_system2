import React, { useState } from 'react';
import api from '../api/axios';
import { useTranslation } from 'react-i18next';

const OnboardingWizard: React.FC = () => {
    const { t } = useTranslation();
    const [step, setStep] = useState(1);
    const [csrData, setCsrData] = useState({ csr: '', private_key: '' });
    const [otp, setOtp] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    // المرحلة الأولى: توليد طلب توقيع الشهادة
    const handleGenerateCSR = async () => {
        setLoading(true);
        try {
            const res = await api.post('/onboarding/generate-csr');
            setCsrData(res.data);
            setStep(2);
        } catch (err) {
            alert("Failed to generate CSR");
        }
        setLoading(false);
    };

    // المرحلة الثانية: الحصول على CSID باستخدام OTP
    const handleSubmitOTP = async () => {
        setLoading(true);
        try {
            const res = await api.post('/onboarding/issue-compliance-csid', { otp });
            setMessage(res.data.message);
            setStep(3);
        } catch (err) {
            alert("Invalid OTP or ZATCA Error");
        }
        setLoading(false);
    };

    return (
        <div className="max-w-2xl mx-auto p-8 bg-white shadow-xl rounded-2xl mt-10">
            <h2 className="text-2xl font-bold mb-6 text-blue-700 border-b pb-4">
                ZATCA Onboarding (Phase 2)
            </h2>

            {step === 1 && (
                <div className="space-y-4">
                    <p className="text-gray-600">هذه الخطوة ستقوم بتوليد المفاتيح الرقمية الخاصة بمنشأتك لربطها بهيئة الزكاة.</p>
                    <button 
                        onClick={handleGenerateCSR}
                        disabled={loading}
                        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-bold"
                    >
                        {loading ? t('loading') : "Generate Digital Keys (CSR)"}
                    </button>
                </div>
            )}

            {step === 2 && (
                <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700">أدخل رمز OTP المستخرج من بوابة "فاتورة":</label>
                    <input 
                        type="text" 
                        maxLength={6}
                        className="w-full p-3 border-2 border-blue-100 rounded-lg text-center text-2xl tracking-widest outline-blue-500"
                        placeholder="000000"
                        value={otp}
                        onChange={(e) => setOtp(e.target.value)}
                    />
                    <button 
                        onClick={handleSubmitOTP}
                        disabled={loading || otp.length < 6}
                        className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition font-bold"
                    >
                        {loading ? t('loading') : "Complete Compliance Registration"}
                    </button>
                </div>
            )}

            {step === 3 && (
                <div className="text-center space-y-4">
                    <div className="text-green-500 text-5xl font-bold">✓</div>
                    <p className="text-xl font-semibold text-gray-800">{message}</p>
                    <p className="text-gray-500 text-sm">أصبح نظامك الآن جاهزاً لتوقيع وإرسال الفواتير رقمياً.</p>
                </div>
            )}
        </div>
    );
};

export default OnboardingWizard;