// src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import ClientListPage from './pages/ClientListPage'; // Placeholder for now
import ClientFormPage from './pages/ClientFormPage'; // Placeholder for now
import ClientDetailPage from './pages/ClientDetailPage'; // Placeholder for now
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<ClientListPage />} />
          <Route path="/clients/new" element={<ClientFormPage mode="create" />} />
          <Route path="/clients/edit/:id" element={<ClientFormPage mode="edit" />} />
          <Route path="/clients/:id" element={<ClientDetailPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}
export default App;
