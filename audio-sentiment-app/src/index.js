import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';  // We'll define App in App.js
import './index.css';     // optional, can remove if not used

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
