'use client'

import React, { useState, useEffect } from 'react';
import { plansAPI } from '@/services/api';
import { Target, Calendar, Trophy, TrendingUp, Star, Clock, CheckCircle } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';

interface PlanData {
  years_played: number;
  handicap: number;
  strengths: string;
  weaknesses: string;
  goals: string;
}

interface CurrentPlan {
  plan: string;
  years_played: number;
  handicap: number;
  strengths: string;
  weaknesses: string;
  goals: string;
  created_at: string;
}

export default function Plans() {
  const [currentPlan, setCurrentPlan] = useState<CurrentPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<PlanData>({
    years_played: 0,
    handicap: 0,
    strengths: '',
    weaknesses: '',
    goals: '',
  });

  useEffect(() => {
    loadCurrentPlan();
  }, []);

  const loadCurrentPlan = async () => {
    try {
      const response = await plansAPI.getCurrentPlan();
      if (response.data.plan) {
        setCurrentPlan(response.data);
      }
    } catch (err) {
      console.error('Error loading current plan:', err);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'years_played' || name === 'handicap' ? Number(value) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const planData: PlanData = {
        years_played: formData.years_played,
        handicap: formData.handicap,
        strengths: formData.strengths,
        weaknesses: formData.weaknesses,
        goals: formData.goals,
      };

      await plansAPI.generatePlan(planData);
      await loadCurrentPlan();
      setShowForm(false);
      setFormData({
        years_played: 0,
        handicap: 0,
        strengths: '',
        weaknesses: '',
        goals: '',
      });
    } catch (err) {
      setError('Failed to generate plan. Please try again.');
      console.error('Error generating plan:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-white/90 backdrop-blur-sm min-h-screen">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Training Plans</h1>
          <p className="text-gray-600">
            Get personalized 4-week training plans based on your experience, handicap, and goals.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        )}

        {!currentPlan ? (
          <div className="card text-center py-12">
            <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">No Training Plan Yet</h2>
            <p className="text-gray-600 mb-6">
              Create your first personalized training plan to start improving your golf game.
            </p>
            <button
              onClick={() => setShowForm(true)}
              className="btn-primary"
            >
              Create Training Plan
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Current Plan Header */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-gray-900 flex items-center">
                  <Target className="w-6 h-6 mr-2 text-golf-600" />
                  Your Current Training Plan
                </h2>
                <button
                  onClick={() => setShowForm(true)}
                  className="btn-secondary text-sm"
                >
                  Create New Plan
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-golf-50 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <Calendar className="w-4 h-4 text-golf-600 mr-2" />
                    <span className="text-sm font-medium text-golf-600">Experience</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">{currentPlan.years_played} years</p>
                </div>
                <div className="bg-golf-50 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <Trophy className="w-4 h-4 text-golf-600 mr-2" />
                    <span className="text-sm font-medium text-golf-600">Handicap</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">{currentPlan.handicap}</p>
                </div>
                <div className="bg-golf-50 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <Clock className="w-4 h-4 text-golf-600 mr-2" />
                    <span className="text-sm font-medium text-golf-600">Created</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">{formatDate(currentPlan.created_at)}</p>
                </div>
              </div>

              {/* Plan Details */}
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
                    <Star className="w-5 h-5 mr-2 text-golf-600" />
                    Strengths
                  </h3>
                  <p className="text-gray-700 bg-green-50 p-3 rounded-lg">{currentPlan.strengths}</p>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-golf-600" />
                    Areas for Improvement
                  </h3>
                  <p className="text-gray-700 bg-yellow-50 p-3 rounded-lg">{currentPlan.weaknesses}</p>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
                    <Target className="w-5 h-5 mr-2 text-golf-600" />
                    Goals
                  </h3>
                  <p className="text-gray-700 bg-blue-50 p-3 rounded-lg">{currentPlan.goals}</p>
                </div>
              </div>
            </div>

            {/* Training Plan Content */}
            <div className="card">
              <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-golf-600" />
                4-Week Training Plan
              </h3>
              <div className="prose prose-lg max-w-none">
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                  {currentPlan.plan}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Create Plan Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-semibold text-gray-900">Create Training Plan</h2>
                  <button
                    onClick={() => setShowForm(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <span className="sr-only">Close</span>
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="years_played" className="block text-sm font-medium text-gray-700 mb-2">
                        Years Playing Golf
                      </label>
                      <input
                        type="number"
                        id="years_played"
                        name="years_played"
                        min="0"
                        max="80"
                        value={formData.years_played}
                        onChange={handleInputChange}
                        className="input-field"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="handicap" className="block text-sm font-medium text-gray-700 mb-2">
                        Current Handicap
                      </label>
                      <input
                        type="number"
                        id="handicap"
                        name="handicap"
                        min="0"
                        max="54"
                        step="0.1"
                        value={formData.handicap}
                        onChange={handleInputChange}
                        className="input-field"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="strengths" className="block text-sm font-medium text-gray-700 mb-2">
                      Your Strengths
                    </label>
                    <textarea
                      id="strengths"
                      name="strengths"
                      rows={3}
                      value={formData.strengths}
                      onChange={handleInputChange}
                      className="input-field"
                      placeholder="e.g., Good short game, consistent putting, strong mental game"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="weaknesses" className="block text-sm font-medium text-gray-700 mb-2">
                      Areas for Improvement
                    </label>
                    <textarea
                      id="weaknesses"
                      name="weaknesses"
                      rows={3}
                      value={formData.weaknesses}
                      onChange={handleInputChange}
                      className="input-field"
                      placeholder="e.g., Driver accuracy, bunker shots, course management"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="goals" className="block text-sm font-medium text-gray-700 mb-2">
                      Your Goals
                    </label>
                    <textarea
                      id="goals"
                      name="goals"
                      rows={3}
                      value={formData.goals}
                      onChange={handleInputChange}
                      className="input-field"
                      placeholder="e.g., Lower handicap by 5 strokes, improve driving distance, break 80 consistently"
                      required
                    />
                  </div>

                  <div className="flex justify-end space-x-4">
                    <button
                      type="button"
                      onClick={() => setShowForm(false)}
                      className="btn-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <div className="flex items-center space-x-2">
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          <span>Generating Plan...</span>
                        </div>
                      ) : (
                        'Generate Plan'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}

