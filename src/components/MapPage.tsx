import React, { useState } from 'react'; // Import React for type definitions
import Header from './Header'; // Assuming you have these components
import Footer from './Footer'; // Assuming you have these components
import SocioEconomicStatsMap from './SocioEconomicStatsMap'; // Assuming you have this component

// Define a type for our chat messages for strong type safety
interface Message {
  sender: 'bot' | 'user';
  text: string;
}

// This function now calls YOUR backend. No API key is needed here!
async function sendToSettlrAgent(message: string): Promise<string> {
  // The URL for your FastAPI backend. Default port for uvicorn is 8000.
  const BACKEND_URL = 'http://localhost:8000/api/chat'; 

  try {
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message })
    });

    if (!response.ok) {
      const errorData = await response.json();
      // FastAPI uses 'detail' for HTTPException errors
      return `Settlr Agent: Error - ${errorData.detail || 'Something went wrong on the server.'}`;
    }

    const data = await response.json();
    return data.reply || 'Settlr Agent: Sorry, I could not get a response.';
  } catch (err) {
    console.error('Error contacting backend:', err);
    return 'Settlr Agent: There was an error connecting to the agent. Is the backend server running?';
  }
}

interface SettlrAgentProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  loading: boolean;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

const SettlrAgent: React.FC<SettlrAgentProps> = ({ 
  messages, 
  setMessages, 
  input, 
  setInput, 
  loading, 
  setLoading 
}) => {
  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage: Message = { sender: 'user', text: input };
    // Use functional update to ensure state is always fresh
    setMessages(currentMessages => [...currentMessages, userMessage]);
    setLoading(true);
    setInput(''); // Clear input immediately for better UX

    const replyText = await sendToSettlrAgent(input);

    const botMessage: Message = { sender: 'bot', text: replyText };
    setMessages(currentMessages => [...currentMessages, botMessage]);
    setLoading(false);
  };

  return (
    <div className="p-6 flex flex-col h-[24rem] max-h-[80vh]">
      <div className="flex-1 overflow-y-auto rounded p-3 mb-3 ">
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-4 flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
              msg.sender === 'user' 
                ? 'bg-indigo-600 text-white rounded-br-md' 
                : 'bg-gray-100 text-gray-800 rounded-bl-md border border-gray-200'
            }`}>
              <div className="text-sm leading-relaxed">
                {msg.text}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="mb-4 flex justify-start">
            <div className="bg-gray-100 text-gray-800 rounded-2xl rounded-bl-md border border-gray-200 px-4 py-3">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm text-gray-600">Settlr Agent is typing...</span>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="flex mt-2">
        <input
          className="flex-1 border border-gray-300 rounded-l-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          type="text"
          placeholder="Ask about safe areas, schools, growth..."
          value={input}
          // Add explicit types for event handlers
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
          onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => { if (e.key === 'Enter') handleSend(); }}
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

const MapPage: React.FC = () => {
  const [showMap, setShowMap] = useState(true);
  const [showChat, setShowChat] = useState(true);
  
  // Move chat state to MapPage to persist across collapse/expand
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'bot', text: 'Hi! I\'m the Settlr Agent. Tell me what you\'re looking for in a neighbourhood, and I\'ll help you find the best matches!' }
  ]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Interactive Neighbourhood Map</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Chat with our Settlr Agent AI to find your perfect neighbourhood, or explore the interactive map with detailed socioeconomic data.
            </p>
          </div>
      {/* Interactive Map Section */}
        <div className="mt-8">
          <div className="text-center mb-6">
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

        {/* AI Chat Section */}
        <div className="max-w-2xl mx-auto mb-8 mt-12">
          <div className="bg-white rounded-lg shadow-lg border border-gray-200">
            {/* Chat Header with Toggle */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-600 rounded-full mr-3"></div>
                <h3 className="text-lg font-semibold text-gray-900">Settlr Agent AI Chat</h3>
              </div>
              <button
                onClick={() => setShowChat(!showChat)}
                className="flex items-center space-x-2 text-gray-500 hover:text-gray-700 transition-colors"
              >
                <span className="text-sm font-medium">
                  {showChat ? 'Hide Chat' : 'Show Chat'}
                </span>
                <svg 
                  className={`w-5 h-5 transition-transform duration-200 ${showChat ? 'rotate-180' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
            
            {/* Collapsible Chat Content */}
            {showChat && (
              <div className="p-4">
                <SettlrAgent 
                  messages={messages}
                  setMessages={setMessages}
                  input={input}
                  setInput={setInput}
                  loading={loading}
                  setLoading={setLoading}
                />
              </div>
            )}
          </div>
        </div>

          
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default MapPage;