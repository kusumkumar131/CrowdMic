import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { SessionContext } from '../context/SessionContext';

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const { session, socketConnected } = useContext(SessionContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        <span className="brand-icon">🎤</span>
        <span>Crowd<span className="brand-tag">Mic</span></span>
      </Link>

      <div className="nav-links">
        {session && (
          <div className="status-pill active" title="Session Code">
            <span>● Code: <strong>{session.sessionCode}</strong></span>
          </div>
        )}

        {user ? (
          <>
            <span className={`role-badge ${user.role}`}>
              {user.role}
            </span>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              {user.name}
            </span>
            <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.85rem' }}>
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>Login</Link>
            <Link to="/register" className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>Register</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
