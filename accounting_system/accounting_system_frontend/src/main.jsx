import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './i18n' // تأكد من وجود ملف i18n.ts أو i18n.js في نفس المجلد
import { BrowserRouter } from 'react-router-dom'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)