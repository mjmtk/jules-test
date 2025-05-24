// src/pages/ClientListPage.js
import React, { useState, useEffect, useCallback } from 'react';
import { getClients, getReferenceData, deleteClient } from '../services/api';
import { Link } from 'react-router-dom';

const ITEMS_PER_PAGE = 2; // Small number for easy pagination testing

const ClientListPage = () => {
  const [clients, setClients] = useState([]);
  const [totalClients, setTotalClients] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [clientStatuses, setClientStatuses] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchClientData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const params = {
      _page: currentPage,
      _limit: ITEMS_PER_PAGE,
    };
    if (statusFilter) {
      params.status_code = statusFilter;
    }
    try {
      const { data, totalCount } = await getClients(params);
      setClients(data);
      setTotalClients(totalCount);
    } catch (err) {
      setError('Failed to fetch clients. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, statusFilter]);

  useEffect(() => {
    const fetchInitialData = async () => {
      const refData = await getReferenceData();
      if (refData && refData.client_statuses) {
        setClientStatuses(refData.client_statuses);
      }
    };
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchClientData();
  }, [fetchClientData]);

  const handleStatusFilterChange = (e) => {
    setStatusFilter(e.target.value);
    setCurrentPage(1); // Reset to first page when filter changes
  };

  const handleDelete = async (clientId) => {
    if (window.confirm('Are you sure you want to delete this client? This action will mark them as "deleted".')) {
      try {
        setIsLoading(true); // Optional: set loading state for delete action
        await deleteClient(clientId);
        alert('Client marked as deleted successfully.');
        fetchClientData(); // Refresh the client list
      } catch (err) {
        setError(err.message || 'Failed to delete client.');
        console.error(err);
      } finally {
        setIsLoading(false); // Optional: clear loading state
      }
    }
  };

  const totalPages = Math.ceil(totalClients / ITEMS_PER_PAGE);

  return (
    <div>
      <h2>Client List</h2>
      <div className="filter-bar"> {/* Added className */}
        <label htmlFor="statusFilter">Filter by Status: </label>
        <select id="statusFilter" value={statusFilter} onChange={handleStatusFilterChange}>
          <option value="">All Statuses</option>
          {clientStatuses.map(status => (
            <option key={status.code} value={status.code}>{status.name}</option>
          ))}
        </select>
      </div>

      {isLoading && <p>Loading clients...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      {/* Removed inline styles from table, relying on App.css now */}
      <table> 
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {clients.length > 0 ? clients.map(client => (
            <tr key={client.id}>
              <td>{client.first_name} {client.last_name}</td>
              <td>{client.email || 'N/A'}</td>
              <td>{client.phone || 'N/A'}</td>
              <td>
                {clientStatuses.find(s => s.code === client.status_code)?.name || client.status_code}
              </td>
              <td>
                <Link to={`/clients/${client.id}`}><button>View</button></Link>
                <Link to={`/clients/edit/${client.id}`}><button>Edit</button></Link>
                <button onClick={() => handleDelete(client.id)} className="danger">Delete</button> {/* Added className */}
              </td>
            </tr>
          )) : (
            <tr>
              <td colSpan="5" style={{ textAlign: 'center' }}>No clients found.</td>
            </tr>
          )}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="pagination-controls"> {/* Added className */}
          <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>
            Previous
          </button>
          <span>Page {currentPage} of {totalPages}</span>
          <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>
            Next
          </button>
        </div>
      )}
    </div>
  );
};
export default ClientListPage;
