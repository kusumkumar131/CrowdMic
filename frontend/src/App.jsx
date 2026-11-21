import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import { SessionProvider, SessionContext } from './context/SessionContext';

import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import StudentDashboard from './pages/StudentDashboard';
import StudentSession from './pages/StudentSession';
import ProfessionalDashboard from './pages/ProfessionalDashboard';
import ProfessionalSession from './pages/ProfessionalSession';
import ModeratorDashboard from './pages/ModeratorDashboard';
import ModeratorSession from './pages/ModeratorSession';
import Receiver from './pages/Receiver';
import ReceiverSession from './pages/ReceiverSession';
import AdminDashboard from './pages/AdminDashboard';

const NotificationToast = () => {
  const { notification } = useContext(SessionContext);
  if (!notification) return null;
  return (
    <div className="toast-banner">
      {notification.type === 'success' && '✅ '}
      {notification.type === 'warning' && '⚡ '}
      {notification.type === 'info' && 'ℹ️ '}
      {notification.message}
    </div>
  );
};

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div style={{ color: '#fff', padding: '2rem', textAlign: 'center' }}>Loading CrowdMic...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <AuthProvider>
      <SessionProvider>
        <Router>
          <div className="app-container">
            <Navbar />
            <NotificationToast />

            <main className="main-content">
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Student Routes */}
                <Route path="/student/dashboard" element={<ProtectedRoute allowedRoles={['student']}><StudentDashboard /></ProtectedRoute>} />
                <Route path="/student/session/:sessionId" element={<ProtectedRoute allowedRoles={['student']}><StudentSession /></ProtectedRoute>} />

                {/* Professional Routes */}
                <Route path="/professional/dashboard" element={<ProtectedRoute allowedRoles={['professional']}><ProfessionalDashboard /></ProtectedRoute>} />
                <Route path="/professional/session/:sessionId" element={<ProtectedRoute allowedRoles={['professional']}><ProfessionalSession /></ProtectedRoute>} />

                {/* Moderator Routes */}
                <Route path="/moderator/dashboard" element={<ProtectedRoute allowedRoles={['moderator', 'admin']}><ModeratorDashboard /></ProtectedRoute>} />
                <Route path="/moderator/session/:sessionId" element={<ProtectedRoute allowedRoles={['moderator', 'admin']}><ModeratorSession /></ProtectedRoute>} />

                {/* Receiver Routes (Accessible by any attendee/moderator device acting as auditorium speaker) */}
                <Route path="/receiver" element={<ProtectedRoute allowedRoles={['receiver', 'admin', 'moderator', 'student', 'professional']}><Receiver /></ProtectedRoute>} />
                <Route path="/receiver/session/:sessionId" element={<ProtectedRoute allowedRoles={['receiver', 'admin', 'moderator', 'student', 'professional']}><ReceiverSession /></ProtectedRoute>} />

                {/* Admin Routes */}
                <Route path="/admin/dashboard" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />

                {/* Fallback Redirect */}
                <Route path="*" element={<Navigate to="/login" replace />} />
              </Routes>
            </main>
          </div>
        </Router>
      </SessionProvider>
    </AuthProvider>
  );
}

export default App;
