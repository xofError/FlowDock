// src/main.jsx (or src/main.js)
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css'; // Your global styles/Tailwind styles
import { HashRouter } from 'react-router-dom'; 

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* WRAP APP WITH THE BROWSER ROUTER** */}
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>,
);