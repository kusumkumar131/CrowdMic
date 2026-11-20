import React, { useState, useEffect, useContext } from 'react';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';

const QuestionBoard = ({ sessionId, isModerator = false }) => {
  const { user } = useContext(AuthContext);
  const [questions, setQuestions] = useState([]);
  const [newQuestion, setNewQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchQuestions = async () => {
    try {
      const res = await api.get(`/sessions/${sessionId}/questions`);
      setQuestions(res.data || []);
    } catch (e) {
      console.error('Failed to fetch questions:', e);
    }
  };

  useEffect(() => {
    if (sessionId) {
      fetchQuestions();
      const interval = setInterval(fetchQuestions, 5000);
      return () => clearInterval(interval);
    }
  }, [sessionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newQuestion.trim()) return;
    setLoading(true);
    try {
      await api.post(`/sessions/${sessionId}/questions`, { text: newQuestion.trim() });
      setNewQuestion('');
      fetchQuestions();
    } catch (e) {
      console.error('Failed to post question:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleFlag = async (questionId) => {
    try {
      await api.post(`/sessions/${sessionId}/questions/${questionId}/flag`);
      fetchQuestions();
    } catch (e) {
      console.error('Failed to flag question:', e);
    }
  };

  return (
    <div className="glass-card" style={{ padding: '1.5rem' }}>
      <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '1rem' }}>
        💬 Session Questions & Q&A
      </h3>

      {/* Question Form */}
      {user && user.role !== 'receiver' && (
        <form onSubmit={handleSubmit} style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Ask a question or topic..."
              value={newQuestion}
              onChange={(e) => setNewQuestion(e.target.value)}
            />
            <button type="submit" className="btn btn-primary" disabled={loading}>
              Submit
            </button>
          </div>
        </form>
      )}

      {/* Question List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '400px', overflowY: 'auto' }}>
        {questions.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>
            No questions submitted yet.
          </p>
        ) : (
          questions.map((q) => (
            <div
              key={q.id}
              style={{
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: q.status === 'flagged' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                gap: '1rem'
              }}
            >
              <div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.3rem' }}>
                  <span className="role-badge student" style={{ fontSize: '0.7rem' }}>
                    {q.category || 'General'}
                  </span>
                  {q.isDuplicate && (
                    <span className="status-pill warning" style={{ fontSize: '0.65rem' }}>
                      ⚡ AI Duplicate Detected ({q.similarityScore}%)
                    </span>
                  )}
                  {q.priorityScore > 1.2 && (
                    <span style={{ fontSize: '0.75rem', color: '#f59e0b' }}>
                      ⭐ High Priority
                    </span>
                  )}
                </div>
                <p style={{ fontSize: '0.95rem', fontWeight: '500' }}>"{q.text}"</p>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  Asked by {q.userName}
                </span>
              </div>

              {isModerator && q.status !== 'flagged' && (
                <button
                  onClick={() => handleFlag(q.id)}
                  className="btn btn-secondary"
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', color: 'var(--accent-danger)' }}
                >
                  Flag
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default QuestionBoard;
