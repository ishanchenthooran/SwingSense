'use client'

import React, { useState } from 'react';
import { resourcesAPI } from '@/services/api';
import { Search, ExternalLink, BookOpen, Video, FileText, Loader } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';

interface Resource {
  id: number;
  title: string;
  description: string;
  url: string;
}

export default function Resources() {
  const [searchTerm, setSearchTerm] = useState('');
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError('');
    setHasSearched(true);

    try {
      const response = await resourcesAPI.getResources(searchTerm);
      setResources(response.data.resources);
    } catch (err) {
      setError('Failed to fetch resources. Please try again.');
      console.error('Error fetching resources:', err);
    } finally {
      setLoading(false);
    }
  };

  const getResourceIcon = (title: string) => {
    const titleLower = title.toLowerCase();
    if (titleLower.includes('video') || titleLower.includes('drill')) {
      return <Video className="w-5 h-5 text-blue-600" />;
    } else if (titleLower.includes('article') || titleLower.includes('guide')) {
      return <FileText className="w-5 h-5 text-green-600" />;
    } else {
      return <BookOpen className="w-5 h-5 text-golf-600" />;
    }
  };

  const popularSearches = [
    'fix slice',
    'improve putting',
    'bunker shots',
    'driver accuracy',
    'short game',
    'course management',
    'mental game',
    'swing tempo'
  ];

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-white/90 backdrop-blur-sm min-h-screen">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Golf Resources</h1>
          <p className="text-gray-600">
            Get personalized resources and recommendations for specific golf issues. 
            Our AI will find the best articles, videos, and drills for your needs.
          </p>
        </div>

        {/* Search Form */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Search className="w-5 h-5 mr-2 text-golf-600" />
            Find Resources
          </h2>
          
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
                What golf issue would you like help with?
              </label>
              <input
                type="text"
                id="search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="e.g., fix slice, improve putting, bunker shots"
                className="input-field"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !searchTerm.trim()}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  <span>Finding resources...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Search Resources</span>
                </>
              )}
            </button>
          </form>

          {/* Popular Searches */}
          <div className="mt-6">
            <p className="text-sm font-medium text-gray-700 mb-3">Popular searches:</p>
            <div className="flex flex-wrap gap-2">
              {popularSearches.map((search, index) => (
                <button
                  key={index}
                  onClick={() => setSearchTerm(search)}
                  className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-full transition-colors duration-200"
                >
                  {search}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Search Results */}
        {hasSearched && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <BookOpen className="w-5 h-5 mr-2 text-golf-600" />
              Resources for "{searchTerm}"
            </h2>

            {resources.length === 0 && !loading ? (
              <div className="card text-center py-12">
                <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No resources found</h3>
                <p className="text-gray-600">
                  Try a different search term or check back later for more resources.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {resources.map((resource, index) => (
                  <div key={index} className="card hover:shadow-lg transition-shadow duration-200">
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 mt-1">
                        {getResourceIcon(resource.title)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {resource.title}
                        </h3>
                        <p className="text-gray-600 mb-3">
                          {resource.description}
                        </p>
                        <a
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-2 text-golf-600 hover:text-golf-700 font-medium transition-colors duration-200"
                        >
                          <span>View Resource</span>
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* How it Works */}
        {!hasSearched && (
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">How it Works</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-golf-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Search className="w-6 h-6 text-golf-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">1. Search</h3>
                <p className="text-gray-600 text-sm">
                  Describe the golf issue you're facing or the skill you want to improve.
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-golf-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <BookOpen className="w-6 h-6 text-golf-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">2. Discover</h3>
                <p className="text-gray-600 text-sm">
                  Our AI finds the best articles, videos, and drills tailored to your needs.
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-golf-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <ExternalLink className="w-6 h-6 text-golf-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">3. Learn</h3>
                <p className="text-gray-600 text-sm">
                  Access curated resources from trusted golf instructors and experts.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}

