// src/pages/ClientDetailPage.js
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getClientById, getReferenceData } from '../services/api';

const ClientDetailPage = () => {
  const { id } = useParams();
  const [client, setClient] = useState(null);
  const [referenceData, setReferenceData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const clientData = await getClientById(id);
        const refData = await getReferenceData(); // Fetch all ref data
        
        setClient(clientData);
        setReferenceData(refData);

        if (!clientData) {
            setError('Client not found.');
        }
      } catch (err) {
        setError('Failed to fetch client details.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDetails();
  }, [id]);

  if (isLoading) return <p>Loading client details...</p>;
  if (error) return <p style={{ color: 'red' }}>{error} <Link to="/">Go back to list</Link></p>;
  if (!client) return <p>Client not found. <Link to="/">Go back to list</Link></p>;

  const getDisplayName = (type, code) => {
    if (!referenceData || !referenceData[type]) return code;
    const item = referenceData[type].find(i => i.code === code);
    return item ? (item.name || item.display_text) : code;
  };

  return (
    <div className="client-detail-card"> {/* Added className */}
      <h2>Client Details: {client.first_name} {client.last_name}</h2>
      <p><strong>ID:</strong> {client.id}</p>
      <p><strong>First Name:</strong> {client.first_name}</p>
      <p><strong>Last Name:</strong> {client.last_name}</p>
      <p><strong>Date of Birth:</strong> {client.date_of_birth}</p>
      <p><strong>Email:</strong> {client.email || 'N/A'}</p>
      <p><strong>Phone:</strong> {client.phone || 'N/A'}</p>
      <p><strong>Status:</strong> {getDisplayName('client_statuses', client.status_code)}</p>
      <p><strong>Primary Language:</strong> {getDisplayName('languages', client.primary_language_code)}</p>
      <p><strong>Pronoun:</strong> {getDisplayName('pronouns', client.pronoun_code)}</p>
      <p><strong>Sex:</strong> {getDisplayName('sex_values', client.sex)}</p>
      <p><strong>Interpreter Needed:</strong> {client.interpreter_needed ? 'Yes' : 'No'}</p>
      <p><strong>Created At:</strong> {new Date(client.created_at).toLocaleString()}</p>
      <p><strong>Updated At:</strong> {new Date(client.updated_at).toLocaleString()}</p>
      <br />
      <Link to={`/clients/edit/${client.id}`}><button>Edit Client</button></Link>
      <Link to="/"><button style={{ marginLeft: '10px' }}>Back to List</button></Link>
    </div>
  );
};
export default ClientDetailPage;
