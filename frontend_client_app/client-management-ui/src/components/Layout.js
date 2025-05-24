// src/components/Layout.js
import React from 'react';
import { NavLink } from 'react-router-dom'; // Use NavLink for active class

const Layout = ({ children }) => {
  return (
    <> {/* Use Fragment or div if #root styling is not flex */}
      <header className="app-header">
        <h1>Client Management</h1>
        <nav className="app-nav">
          <NavLink to="/" end className={({isActive}) => isActive ? "active" : ""}>Client List</NavLink>
          <NavLink to="/clients/new" className={({isActive}) => isActive ? "active" : ""}>Add New Client</NavLink>
        </nav>
      </header>
      <main className="app-main">
        {children}
      </main>
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} SWiS Client Management</p>
      </footer>
    </>
  );
};
export default Layout;
