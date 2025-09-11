'use client'

import React, { useState, useEffect } from 'react';
import { questionsAPI } from '@/services/api';
import { Send, MessageSquare, Clock, Bot, User } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function Logs() {
  const [questions, setQuestions] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [newQuestion, setNewQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadQuestions();
    loadFeedback();
  }, []);

  const loadQuestions = async () => {
    try {
      const response = await questionsAPI.getQuestions();
      setQuestions(response.data);
    } catch (err) {
      console.error('Error loading questions:', err);
    }
  };

  const loadFeedback = async () => {
    try {
      const response = await questionsAPI.getFeedback();
      setFeedback(response.data);
    } catch (err) {
      console.error('Error loading feedback:', err);
    }
  };

  const handleSubmitQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQuestion.trim()) return;

    setLoading(true);
    setError('');

    try {
      await questionsAPI.createQuestion(newQuestion);
      setNewQuestion('');
      // Reload both questions and feedback
      await Promise.all([loadQuestions(), loadFeedback()]);
    } catch (err) {
      setError('Failed to submit question. Please try again.');
      console.error('Error submitting question:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Combine questions and feedback for display
  const combinedLogs = [...questions, ...feedback]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-white/90 backdrop-blur-sm min-h-screen">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Golf Q&A Logs</h1>
          <p className="text-gray-600">
            Ask questions about your golf swing and get AI-powered coaching advice. 
            All your questions and responses are saved here for future reference.
          </p>
        </div>

        {/* Ask Question Form */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <MessageSquare className="w-5 h-5 mr-2 text-golf-600" />
            Ask a Question
          </h2>
          
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmitQuestion} className="space-y-4">
            <div>
              <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
                What would you like to know about your golf swing?
              </label>
              <textarea
                id="question"
                value={newQuestion}
                onChange={(e) => setNewQuestion(e.target.value)}
                placeholder="e.g., I keep slicing my driver. What am I doing wrong?"
                className="input-field min-h-[100px] resize-none"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !newQuestion.trim()}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Getting advice...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Ask Question</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Q&A Logs */}
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-golf-600" />
            Recent Q&A History
          </h2>

          {combinedLogs.length === 0 ? (
            <div className="card text-center py-12">
              <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No questions yet</h3>
              <p className="text-gray-600">
                Ask your first question above to get started with AI-powered golf coaching!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {combinedLogs.map((item, index) => (
                <div key={`${item.id}-${index}`} className="card">
                  <div className="flex items-start space-x-3">
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                      'question' in item 
                        ? 'bg-blue-100 text-blue-600' 
                        : 'bg-golf-100 text-golf-600'
                    }`}>
                      {'question' in item ? (
                        <User className="w-4 h-4" />
                      ) : (
                        <Bot className="w-4 h-4" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <p className={`text-sm font-medium ${
                          'question' in item ? 'text-blue-600' : 'text-golf-600'
                        }`}>
                          {'question' in item ? 'Your Question' : 'AI Coach Response'}
                        </p>
                        <p className="text-xs text-gray-500 flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {formatDate(item.created_at)}
                        </p>
                      </div>
                      <div className="prose prose-sm max-w-none">
                        <p className="text-gray-900 whitespace-pre-wrap">
                          {'question' in item ? item.question : item.feedback}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}

