'use client'

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Target, MessageSquare, BookOpen, TrendingUp, ArrowRight, Star } from 'lucide-react';

export default function Home() {
  const { user } = useAuth();

  const features = [
    {
      icon: MessageSquare,
      title: 'AI-Powered Q&A',
      description: 'Get instant, personalized swing advice from our AI golf coach. Ask questions and receive actionable feedback.',
    },
    {
      icon: Target,
      title: 'Personalized Plans',
      description: 'Create custom training plans based on your handicap, experience, and goals. Track your progress over time.',
    },
    {
      icon: BookOpen,
      title: 'Curated Resources',
      description: 'Access a library of golf resources tailored to your specific swing issues and improvement areas.',
    },
    {
      icon: TrendingUp,
      title: 'Progress Tracking',
      description: 'Monitor your improvement with detailed progress metrics and performance analytics.',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Welcome to{' '}
              <span className="text-golf-300">SwingSense</span>
            </h1>
            <p className="text-xl text-gray-200 mb-8 max-w-3xl mx-auto">
              Your AI-powered golf coaching companion. Get personalized swing advice, 
              training plans, and resources to improve your game.
            </p>
            {!user ? (
              <Link
                href="/login"
                className="inline-flex items-center space-x-2 bg-golf-600 hover:bg-golf-700 text-white font-semibold py-4 px-8 rounded-xl text-lg transition-colors duration-200 shadow-lg hover:shadow-xl"
              >
                <span>Get Started</span>
                <ArrowRight className="w-5 h-5" />
              </Link>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/logs"
                  className="inline-flex items-center space-x-2 bg-golf-600 hover:bg-golf-700 text-white font-semibold py-4 px-8 rounded-xl text-lg transition-colors duration-200 shadow-lg hover:shadow-xl"
                >
                  <MessageSquare className="w-5 h-5" />
                  <span>Ask a Question</span>
                </Link>
                <Link
                  href="/plans"
                  className="inline-flex items-center space-x-2 bg-white hover:bg-gray-50 text-golf-600 font-semibold py-4 px-8 rounded-xl text-lg transition-colors duration-200 shadow-lg hover:shadow-xl border-2 border-golf-600"
                >
                  <Target className="w-5 h-5" />
                  <span>Create Plan</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white/90 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Everything you need to improve your golf game
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our AI-powered platform provides personalized coaching, training plans, 
              and resources to help you reach your golfing goals.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="card hover:shadow-lg transition-shadow duration-200">
                <div className="flex items-center justify-center w-12 h-12 bg-golf-100 rounded-lg mb-4">
                  <feature.icon className="w-6 h-6 text-golf-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 bg-gray-50/90 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              What golfers are saying
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                name: 'Sarah Johnson',
                handicap: '12',
                quote: 'SwingSense helped me fix my slice in just 2 weeks. The AI advice was spot-on!',
                rating: 5,
              },
              {
                name: 'Mike Chen',
                handicap: '8',
                quote: 'The personalized training plans are incredible. I dropped 4 strokes this season.',
                rating: 5,
              },
              {
                name: 'Emily Davis',
                handicap: '18',
                quote: 'Finally, a golf coach that\'s available 24/7. The Q&A feature is a game-changer.',
                rating: 5,
              },
            ].map((testimonial, index) => (
              <div key={index} className="card">
                <div className="flex items-center mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-gray-600 mb-4 italic">
                  "{testimonial.quote}"
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-golf-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-golf-600 font-semibold text-sm">
                      {testimonial.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{testimonial.name}</p>
                    <p className="text-sm text-gray-500">Handicap: {testimonial.handicap}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-golf-600/90 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to improve your golf game?
          </h2>
          <p className="text-xl text-golf-100 mb-8">
            Join thousands of golfers who are already using SwingSense to reach their goals.
          </p>
          {!user && (
            <Link
              href="/login"
              className="inline-flex items-center space-x-2 bg-white hover:bg-gray-50 text-golf-600 font-semibold py-4 px-8 rounded-xl text-lg transition-colors duration-200 shadow-lg hover:shadow-xl"
            >
              <span>Start Your Journey</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
          )}
        </div>
      </section>
    </div>
  );
}

