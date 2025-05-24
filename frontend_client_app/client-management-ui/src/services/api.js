// src/services/api.js
const API_BASE_URL = 'http://localhost:3001/api/v1';

export const getClients = async (params = {}) => {
  // JSON server uses _page and _limit for pagination
  // And direct property names for filtering, e.g. status_code=active
  const query = new URLSearchParams(params);
  try {
    const response = await fetch(`${API_BASE_URL}/clients?${query.toString()}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    // JSON Server includes total count in X-Total-Count header
    const totalCount = response.headers.get('X-Total-Count');
    const data = await response.json();
    return { data, totalCount: parseInt(totalCount, 10) || data.length };
  } catch (error) {
    console.error("Failed to fetch clients:", error);
    // In a real app, handle this more gracefully
    return { data: [], totalCount: 0 };
  }
};

export const getReferenceData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/reference-data/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch reference data:", error);
    return null; // Or some default structure
  }
};

export const getClientById = async (id) => {
  try {
    const response = await fetch(`${API_BASE_URL}/clients/${id}`);
    if (!response.ok) {
      if (response.status === 404) return null; // Handle not found gracefully
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch client ${id}:`, error);
    throw error; // Re-throw to be caught by component
  }
};

export const createClient = async (clientData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/clients`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(clientData),
    });
    if (!response.ok) {
      // TODO: Handle specific errors like 400 (validation) based on response body
      const errorBody = await response.json();
      console.error('Create client failed:', errorBody);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorBody.error?.message || 'Unknown error'}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to create client:", error);
    throw error; // Re-throw
  }
};

export const updateClient = async (id, clientData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/clients/${id}`, {
      method: 'PATCH', // Or PUT, depending on your API for partial/full update
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(clientData),
    });
    if (!response.ok) {
      const errorBody = await response.json();
      console.error('Update client failed:', errorBody);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorBody.error?.message || 'Unknown error'}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Failed to update client ${id}:`, error);
    throw error;
  }
};

export const deleteClient = async (id) => {
  try {
    const response = await fetch(`${API_BASE_URL}/clients/${id}`, {
      method: 'DELETE',
    });
    // DELETE requests on json-server with custom route might not return content.
    // The custom server.js sends 204.
    if (response.status === 204) {
      return { success: true }; // Or simply return nothing for 204
    }
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({})); // Catch if no body
      console.error('Delete client failed:', errorBody);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorBody.error?.message || 'Failed to delete client'}`);
    }
    // If server sent back data (though typically 204 for DELETE)
    return { success: true, data: await response.json().catch(() => null) }; 
  } catch (error) {
    console.error(`Failed to delete client ${id}:`, error);
    throw error; // Re-throw
  }
};
