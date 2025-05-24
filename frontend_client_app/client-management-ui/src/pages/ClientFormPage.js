// src/pages/ClientFormPage.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { createClient, getClientById, updateClient, getReferenceData } from '../services/api'; // Add getClientById & updateClient

const ClientFormPage = ({ mode }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [isEditMode, setIsEditMode] = useState(mode === 'edit');
  
  const initialFormState = {
    first_name: '',
    last_name: '',
    date_of_birth: '',
    email: '',
    phone: '',
    status_code: '',
    primary_language_code: '',
    pronoun_code: '',
    sex: '',
    interpreter_needed: false,
  };
  const [formData, setFormData] = useState(initialFormState);
  const [referenceData, setReferenceData] = useState({
    client_statuses: [], languages: [], pronouns: [], sex_values: []
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formError, setFormError] = useState(null);


  useEffect(() => {
    const fetchRefData = async () => {
      setIsLoading(true);
      try {
        const refData = await getReferenceData();
        if (refData) {
          setReferenceData({
            client_statuses: refData.client_statuses || [],
            languages: refData.languages || [],
            pronouns: refData.pronouns || [],
            sex_values: refData.sex_values || []
          });
        }
      } catch (err) {
        setError('Failed to load reference data.');
        console.error(err);
      } finally {
        setIsLoading(false); // Should be part of the combined loading state
      }
    };
    fetchRefData();
  }, []);
  
  useEffect(() => {
    setIsEditMode(mode === 'edit'); // Update based on mode prop
    if (mode === 'edit' && id) {
      setIsLoading(true);
      getClientById(id)
        .then(client => {
          if (client) {
            // Ensure all fields in initialFormState are covered
            // And also handle fields that might come from client but are not in initialFormState (like id, created_at etc.)
            const clientDataForForm = { ...initialFormState }; 
            for (const key in client) {
                if (key in initialFormState) { // Only populate fields defined in initialFormState
                    clientDataForForm[key] = client[key] !== undefined ? client[key] : initialFormState[key];
                }
            }
            // Ensure boolean for checkbox
            clientDataForForm.interpreter_needed = !!client.interpreter_needed; 
            setFormData(clientDataForForm);
          } else {
            setError('Client not found for editing.');
          }
        })
        .catch(err => {
          setError('Failed to fetch client for editing.');
          console.error(err);
        })
        .finally(() => setIsLoading(false));
    } else {
        setFormData(initialFormState); // Reset for create mode or if no id
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, id]);


  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    setIsLoading(true);
    
    if (!formData.first_name || !formData.last_name || !formData.date_of_birth || !formData.status_code) {
        setFormError('Required fields are missing (First Name, Last Name, DOB, Status).');
        setIsLoading(false);
        return;
    }

    // Add created_at and updated_at for new clients
    const submissionData = {
        ...formData,
        ...(isEditMode ? { updated_at: new Date().toISOString() } : { created_at: new Date().toISOString(), updated_at: new Date().toISOString() })
    };


    try {
      let response;
      if (isEditMode) {
        response = await updateClient(id, submissionData);
        alert('Client updated successfully!');
        navigate(`/clients/${id}`); 
      } else {
        response = await createClient(submissionData);
        alert('Client created successfully! ID: ' + response.id);
        navigate('/'); 
      }
    } catch (err) {
      setFormError(err.message || 'An error occurred while saving the client.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const title = isEditMode ? `Edit Client: ${formData.first_name || ''} ${formData.last_name || ''}` : 'Create New Client';

  // Combined loading state for initial data fetch (ref data or client data)
  if (isLoading && (!referenceData.client_statuses.length || (isEditMode && !formData.first_name))) {
      return <p>Loading form data...</p>;
  }
  if (error) return <p style={{ color: 'red' }}>{error} <Link to="/">Go back to list</Link></p>;


  return (
    <div>
      <h2>{title}</h2>
      {formError && <p style={{color: 'red'}}>{formError}</p>}
      <form onSubmit={handleSubmit}>
        <div><label>First Name: <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} required /></label></div>
        <div><label>Last Name: <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} required /></label></div>
        <div><label>Date of Birth: <input type="date" name="date_of_birth" value={formData.date_of_birth} onChange={handleChange} required /></label></div>
        <div><label>Email: <input type="email" name="email" value={formData.email} onChange={handleChange} /></label></div>
        <div><label>Phone: <input type="tel" name="phone" value={formData.phone} onChange={handleChange} /></label></div>
        
        <div>
          <label>Status: <select name="status_code" value={formData.status_code} onChange={handleChange} required>
            <option value="">Select Status</option>
            {referenceData.client_statuses.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
          </select></label>
        </div>
        <div>
          <label>Primary Language: <select name="primary_language_code" value={formData.primary_language_code} onChange={handleChange}>
            <option value="">Select Language</option>
            {referenceData.languages.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
          </select></label>
        </div>
        <div>
          <label>Pronoun: <select name="pronoun_code" value={formData.pronoun_code} onChange={handleChange}>
            <option value="">Select Pronoun</option>
            {referenceData.pronouns.map(p => <option key={p.code} value={p.code}>{p.display_text}</option>)}
          </select></label>
        </div>
        <div>
          <label>Sex: <select name="sex" value={formData.sex} onChange={handleChange}>
            <option value="">Select Sex</option>
            {referenceData.sex_values.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
          </select></label>
        </div>
        <div>
          <label>Interpreter Needed: <input type="checkbox" name="interpreter_needed" checked={formData.interpreter_needed} onChange={handleChange} /></label>
        </div>
        <br/>
        <button type="submit" disabled={isLoading}>{isLoading ? (isEditMode ? 'Saving...' : 'Creating...') : (isEditMode ? 'Save Changes' : 'Create Client')}</button>
        <button type="button" onClick={() => navigate(isEditMode ? `/clients/${id}` : '/')} style={{marginLeft: '10px'}} disabled={isLoading}>Cancel</button>
      </form>
    </div>
  );
};
export default ClientFormPage;
