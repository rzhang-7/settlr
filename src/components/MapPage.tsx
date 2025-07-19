import { useState } from 'react';
import Header from './Header';
import Footer from './Footer';
import SocioEconomicStatsMap from './SocioEconomicStatsMap';

// Gemini API integration setup (placeholder)
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent';
const GEMINI_API_KEY = import.meta.env.GEMINI_API_KEY;; // Replace with your actual API key

async function sendToGemini(message: string) {
  if (!GEMINI_API_KEY || GEMINI_API_KEY === 'YOUR_GEMINI_API_KEY') {
    // No API key set, fallback to mock
    return 'Settlr Agent: (Mock) I\'ve analyzed your request!';
  }
  try {
    const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: message }] }]
      })
    });
    const data = await response.json();
    return data?.candidates?.[0]?.content?.parts?.[0]?.text || 'Settlr Agent: Sorry, I could not get a response.';
  } catch (err) {
    return 'Settlr Agent: There was an error contacting Gemini.';
  }
}

const SettlrAgent = () => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hi! I\'m the Settlr Agent. Tell me what you\'re looking for in a neighbourhood, and I\'ll help you find the best matches!' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    setMessages([...messages, { sender: 'user', text: input }]);
    setLoading(true);
    const reply = await sendToGemini(input);
    setMessages(current => [
      ...current,
      { sender: 'bot', text: reply }
    ]);
    setLoading(false);
    setInput('');
  };

  return (
    <div className="bg-gray-50 rounded-lg shadow-lg p-6 flex flex-col h-[32rem] max-h-[80vh] border-l-4 border-green-600">
      <div className="flex items-center mb-2">
        <div className="w-3 h-3 bg-green-600 rounded-full mr-3"></div>
        <h3 className="text-lg font-semibold text-green-700 flex items-center">
          <svg className="w-6 h-6 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" strokeWidth="2" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 15s1.5 2 4 2 4-2 4-2" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 9h.01M15 9h.01" />
          </svg>
          Settlr Agent AI Chat
        </h3>
      </div>
      <div className="flex-1 overflow-y-auto bg-gray-50 rounded p-3 mb-3 border border-gray-100">
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-2 flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`px-4 py-2 rounded-lg max-w-xs text-sm ${msg.sender === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-800'}`}>
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="mb-2 flex justify-start">
            <div className="px-4 py-2 rounded-lg max-w-xs text-sm bg-gray-200 text-gray-800 animate-pulse">
              Settlr Agent is typing...
            </div>
          </div>
        )}
      </div>
      <div className="flex mt-2">
        <input
          className="flex-1 border border-gray-300 rounded-l-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          type="text"
          placeholder="Ask Settlr Agent about neighbourhoods..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') handleSend(); }}
          disabled={loading}
        />
        <button
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-r-lg font-medium disabled:opacity-50"
          onClick={handleSend}
          disabled={loading}
        >
          Send
        </button>
      </div>
    </div>
  );
};

const MapPage = () => {
  const [showMap, setShowMap] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Interactive Neighbourhood Map</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Choose your preferred way to find neighbourhoods: use detailed search preferences, chat with our Settlr Agent AI, or explore the interactive map.
            </p>
          </div>

          {/* Search Options Header */}
          <div className="text-center mb-8">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Choose Your Search Method</h3>
            <div className="flex justify-center space-x-8">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-indigo-600 rounded-full"></div>
                <span className="text-gray-700 font-medium">Manual Search Preferences</span>
              </div>
              <div className="text-gray-400">OR</div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-green-600 rounded-full"></div>
                <span className="text-gray-700 font-medium">Settlr Agent AI Chat</span>
              </div>
              <div className="text-gray-400">OR</div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-blue-600 rounded-full"></div>
                <span className="text-gray-700 font-medium">Interactive Map</span>
              </div>
            </div>
          </div>

          {/* Responsive grid: preferences + chatbot */}
          <div className="grid md:grid-cols-2 gap-8">
            {/* Left: Preferences and Results stacked */}
            <div className="flex flex-col space-y-8">
              <div className="bg-gray-50 rounded-lg p-6 border-l-4 border-indigo-600">
                <div className="flex items-center mb-4">
                  <div className="w-3 h-3 bg-indigo-600 rounded-full mr-3"></div>
                  <h3 className="text-lg font-semibold text-gray-900">Manual Search Preferences</h3>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Education Proximity</label>
                    <select className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                      <option>High Priority</option>
                      <option>Medium Priority</option>
                      <option>Low Priority</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Socioeconomic Growth Potential</label>
                    <select className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                      <option>High</option>
                      <option>Moderate</option>
                      <option>Low</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Crime Rates</label>
                    <select className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                      <option>Very Low</option>
                      <option>Low</option>
                      <option>Average</option>
                      <option>High</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Job Opportunities</label>
                    <select className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                      <option>Excellent</option>
                      <option>Good</option>
                      <option>Average</option>
                      <option>Poor</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-6 border-l-4 border-indigo-600">
                <div className="flex items-center mb-4">
                  <div className="w-3 h-3 bg-indigo-600 rounded-full mr-3"></div>
                  <h3 className="text-lg font-semibold text-gray-900">AI Analysis Results</h3>
                </div>
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border">
                    <h4 className="font-semibold text-gray-900 mb-2">Top Recommended Neighbourhoods</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Downtown Core</span>
                        <span className="text-sm font-semibold text-green-600">95% Match</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Midtown District</span>
                        <span className="text-sm font-semibold text-green-600">87% Match</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Riverside Community</span>
                        <span className="text-sm font-semibold text-green-600">82% Match</span>
                      </div>
                    </div>
                  </div>
                  <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-md transition-colors duration-200">
                    Run AI Analysis
                  </button>
                </div>
              </div>
            </div>
            {/* Right: Settlr Agent Chatbot */}
            <div className="h-full flex flex-col">
              <SettlrAgent />
            </div>
          </div>

          {/* Interactive Map Section */}
          <div className="mt-8">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Interactive Toronto Neighbourhood Map</h3>
              <p className="text-gray-600 mb-4">
                Explore Toronto neighbourhoods with detailed socioeconomic statistics and growth potential data.
              </p>
              <button
                onClick={() => setShowMap(!showMap)}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center mx-auto"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {showMap ? 'Hide Interactive Map' : 'Show Interactive Map'}
              </button>
            </div>
            
            {showMap && (
              <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="h-[600px] w-full">
                  <SocioEconomicStatsMap />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default MapPage; 