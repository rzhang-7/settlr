import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import Header from './Header';
import Footer from './Footer';

const HomePage = () => {
  const navigate = useNavigate();
  const [expandedStep, setExpandedStep] = useState<number | null>(1); // Set first step as default

  const handleExploreMap = () => {
    navigate('/map');
  };

  const toggleStep = (stepId: number) => {
    setExpandedStep(stepId);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            {/* Main Heading */}
            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6">
              Find Your Perfect
                              <span className="text-indigo-600 block">Neighbourhood</span>
            </h1>
            
            {/* Subtitle */}
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Discover ideal neighbourhoods in Toronto
              based on your unique preferences through the power of AI.
            </p>

            

            {/* CTA Button */}
            <button
              onClick={handleExploreMap}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-8 rounded-lg text-lg transition-colors duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
            >
                              Explore Neighbourhoods
            </button>

            {/* Additional Info */}
            <p className="text-gray-500 mt-6 text-sm">
              Start your journey to finding the perfect place to call home
            </p>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-white py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-6">How it works</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Our intelligent platform combines data analysis with AI to help you make informed decisions about where to live.
            </p>
          </div>

          {/* Timeline */}
          <div className="relative">
            {/* Timeline Line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200"></div>
            
            {/* Step 1 */}
            <div className="relative mb-16 last:mb-0">
              <div 
                className={`absolute left-0 top-8 w-16 h-16 rounded-full flex items-center justify-center shadow-lg z-10 cursor-pointer transition-all duration-300 ${
                  expandedStep === 1 ? 'bg-indigo-600' : 'bg-gray-300 hover:bg-gray-400 hover:scale-105'
                }`}
                onClick={() => toggleStep(1)}
                style={{ transform: 'translateY(-50%)' }}
              >
                <span className={`font-bold text-2xl transition-colors duration-300 ${
                  expandedStep === 1 ? 'text-white' : 'text-gray-600'
                }`}>1</span>
              </div>
              <div className="ml-24">
                {expandedStep === 1 ? (
                  <div className="bg-white rounded-lg border-2 border-indigo-200 shadow-lg p-8 transition-all duration-300">
                    <h3 className="text-3xl font-bold text-gray-900 mb-4">Set Preferences</h3>
                    <p className="text-xl text-gray-600 leading-relaxed">
                      Tell us what matters most to you - schools, safety, job opportunities, etc.
                    </p>
                  </div>
                ) : (
                  <div 
                    className="cursor-pointer transition-all duration-300 flex items-center h-16 hover:translate-x-1"
                    onClick={() => toggleStep(1)}
                  >
                    <h3 className="text-3xl font-bold text-gray-500 hover:text-gray-700 transition-colors duration-300">Set Preferences</h3>
                  </div>
                )}
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative mb-16 last:mb-0">
              <div 
                className={`absolute left-0 top-8 w-16 h-16 rounded-full flex items-center justify-center shadow-lg z-10 cursor-pointer transition-all duration-300 ${
                  expandedStep === 2 ? 'bg-indigo-600' : 'bg-gray-300 hover:bg-gray-400 hover:scale-105'
                }`}
                onClick={() => toggleStep(2)}
                style={{ transform: 'translateY(-50%)' }}
              >
                <span className={`font-bold text-2xl transition-colors duration-300 ${
                  expandedStep === 2 ? 'text-white' : 'text-gray-600'
                }`}>2</span>
              </div>
              <div className="ml-24">
                {expandedStep === 2 ? (
                  <div className="bg-white rounded-lg border-2 border-indigo-200 shadow-lg p-8 transition-all duration-300">
                    <h3 className="text-3xl font-bold text-gray-900 mb-4">AI Analysis</h3>
                    <p className="text-xl text-gray-600 leading-relaxed">
                      Our AI analyzes thousands of data points to find neighbourhoods that match your criteria.
                    </p>
                  </div>
                ) : (
                  <div 
                    className="cursor-pointer transition-all duration-300 flex items-center h-16 hover:translate-x-1"
                    onClick={() => toggleStep(2)}
                  >
                    <h3 className="text-3xl font-bold text-gray-500 hover:text-gray-700 transition-colors duration-300">AI Analysis</h3>
                  </div>
                )}
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative mb-16 last:mb-0">
              <div 
                className={`absolute left-0 top-8 w-16 h-16 rounded-full flex items-center justify-center shadow-lg z-10 cursor-pointer transition-all duration-300 ${
                  expandedStep === 3 ? 'bg-indigo-600' : 'bg-gray-300 hover:bg-gray-400 hover:scale-105'
                }`}
                onClick={() => toggleStep(3)}
                style={{ transform: 'translateY(-50%)' }}
              >
                <span className={`font-bold text-2xl transition-colors duration-300 ${
                  expandedStep === 3 ? 'text-white' : 'text-gray-600'
                }`}>3</span>
              </div>
              <div className="ml-24">
                {expandedStep === 3 ? (
                  <div className="bg-white rounded-lg border-2 border-indigo-200 shadow-lg p-8 transition-all duration-300">
                    <h3 className="text-3xl font-bold text-gray-900 mb-4">Get Rankings</h3>
                    <p className="text-xl text-gray-600 leading-relaxed">
                      Receive personalized neighbourhood rankings with detailed explanations and insights.
                    </p>
                  </div>
                ) : (
                  <div 
                    className="cursor-pointer transition-all duration-300 flex items-center h-16 hover:translate-x-1"
                    onClick={() => toggleStep(3)}
                  >
                    <h3 className="text-3xl font-bold text-gray-500 hover:text-gray-700 transition-colors duration-300">Get Rankings</h3>
                  </div>
                )}
              </div>
            </div>

            {/* Step 4 */}
            <div className="relative mb-16 last:mb-0">
              <div 
                className={`absolute left-0 top-8 w-16 h-16 rounded-full flex items-center justify-center shadow-lg z-10 cursor-pointer transition-all duration-300 ${
                  expandedStep === 4 ? 'bg-indigo-600' : 'bg-gray-300 hover:bg-gray-400 hover:scale-105'
                }`}
                onClick={() => toggleStep(4)}
                style={{ transform: 'translateY(-50%)' }}
              >
                <span className={`font-bold text-2xl transition-colors duration-300 ${
                  expandedStep === 4 ? 'text-white' : 'text-gray-600'
                }`}>4</span>
              </div>
              <div className="ml-24">
                {expandedStep === 4 ? (
                  <div className="bg-white rounded-lg border-2 border-indigo-200 shadow-lg p-8 transition-all duration-300">
                    <h3 className="text-3xl font-bold text-gray-900 mb-4">Explore & Decide</h3>
                    <p className="text-xl text-gray-600 leading-relaxed">
                      Use interactive maps and detailed data to explore your top matches and make your decision.
                    </p>
                  </div>
                ) : (
                  <div 
                    className="cursor-pointer transition-all duration-300 flex items-center h-16 hover:translate-x-1"
                    onClick={() => toggleStep(4)}
                  >
                    <h3 className="text-3xl font-bold text-gray-500 hover:text-gray-700 transition-colors duration-300">Explore & Decide</h3>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

      {/* Technology Section */}
        <div className="mt-12 mb-12 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Our Technology</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">AI-Powered Analysis</h3>
                <p className="text-gray-600">
                  Advanced machine learning algorithms analyze comprehensive neighbourhood data to provide accurate recommendations.
                </p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Comprehensive Data</h3>
                <p className="text-gray-600">
                  Access to thousands of data points including socioeconomic statistics, crime rates, school proximity, and more.
                </p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Interactive Maps</h3>
                <p className="text-gray-600">
                  Visualize neighbourhood data with interactive maps and detailed profiles to make informed decisions.
                </p>
              </div>
            </div>
          </div>

        {/* Call to Action */}
        <div className="text-center mt-16">
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-12 max-w-4xl mx-auto">
              <h3 className="text-3xl font-bold text-gray-900 mb-4">Ready to start your neighbourhood search?</h3>
              <p className="text-xl text-gray-600 mb-8">Join thousands of users who have found their perfect neighbourhood with Settlr.</p>
              <button
                onClick={handleExploreMap}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold py-4 px-8 rounded-lg text-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                Get Started Now
              </button>
            </div>
          </div>
      </div>


      <Footer />
    </div>
  );
};

export default HomePage; 