'use client'

import React, { useState, useEffect } from 'react';
import { questionsAPI } from '@/services/api';
import { Send, MessageSquare, Clock, Bot, User, Loader, BookOpen } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';

interface Question {
  id: string;
  question: string;
  created_at: string;
}

interface Feedback {
  id: string;
  question_id: string;
  feedback: string;
  sources: string[];
  created_at: string;
}

interface QAPair {
  question: Question;
  feedback: Feedback | null;
}

export default function Logs() {
  const [qaPairs, setQaPairs] = useState<QAPair[]>([]);
  const [newQuestion, setNewQuestion] = useState('');
  const [initialLoading, setInitialLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    try {
      const [questionsRes, feedbackRes] = await Promise.all([
        questionsAPI.getQuestions(),
        questionsAPI.getFeedback(),
      ]);
      const questions: Question[] = questionsRes.data;
      const feedbackList: Feedback[] = feedbackRes.data;

      const feedbackByQuestionId = new Map(feedbackList.map((f) => [f.question_id, f]));
      const pairs: QAPair[] = questions.map((q) => ({
        question: q,
        feedback: feedbackByQuestionId.get(q.id) ?? null,
      }));

      setQaPairs(pairs);
    } catch (err) {
      console.error('Error loading Q&A logs:', err);
    } finally {
      setInitialLoading(false);
    }
  };

  const handleSubmitQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQuestion.trim()) return;

    setSubmitting(true);
    setError('');

    try {
      await questionsAPI.createQuestion(newQuestion);
      setNewQuestion('');
      await loadLogs();
    } catch (err) {
      setError('Failed to submit question. Please try again.');
      console.error('Error submitting question:', err);
    } finally {
      setSubmitting(false);
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

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-white/90 backdrop-blur-sm min-h-screen">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Golf Q&A Logs</h1>
          <p className="text-gray-600">
            Ask questions about your golf swing and get AI-powered coaching advice.
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
                disabled={submitting}
              />
            </div>
            <button
              type="submit"
              disabled={submitting || !newQuestion.trim()}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
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

        {/* Q&A History */}
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-golf-600" />
            Recent Q&A History
          </h2>

          {initialLoading ? (
            <div className="card flex items-center justify-center py-12">
              <Loader className="w-6 h-6 animate-spin text-golf-600 mr-3" />
              <span className="text-gray-600">Loading your Q&A history...</span>
            </div>
          ) : qaPairs.length === 0 ? (
            <div className="card text-center py-12">
              <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No questions yet</h3>
              <p className="text-gray-600">
                Ask your first question above to get started with AI-powered golf coaching!
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {qaPairs.map(({ question, feedback }) => (
                <div key={question.id} className="card space-y-4">
                  {/* Question */}
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                      <User className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-sm font-medium text-blue-600">Your Question</p>
                        <p className="text-xs text-gray-500 flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {formatDate(question.created_at)}
                        </p>
                      </div>
                      <p className="text-gray-900">{question.question}</p>
                    </div>
                  </div>

                  {/* Feedback */}
                  {feedback ? (
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-golf-100 text-golf-600 flex items-center justify-center">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-golf-600 mb-1">AI Coach Response</p>
                        <p className="text-gray-900 whitespace-pre-wrap">{feedback.feedback}</p>
                        {feedback.sources.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {feedback.sources.map((src, i) => (
                              <span
                                key={i}
                                className="inline-flex items-center space-x-1 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full"
                              >
                                <BookOpen className="w-3 h-3" />
                                <span>{src}</span>
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-3 text-sm text-gray-500 pl-11">
                      <Loader className="w-4 h-4 animate-spin" />
                      <span>Generating response...</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
