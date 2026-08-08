import { useState } from 'react'
import InterviewHeader from '../components/interview/InterviewHeader'
import { Link } from 'react-router-dom'
import InterviewProgress from '../components/interview/InterviewProgress'
import InterviewJourney from '../components/interview/InterviewJourney'
import ChatWindow from '../components/interview/ChatWindow'

const INITIAL_MESSAGES = [
  {
    id: '1',
    sender: 'ai',
    text: "Let's talk about your experience with retrieval systems. Tell me about a RAG system you built.",
    timestamp: '11:40 AM',
  },
  {
    id: '2',
    sender: 'candidate',
    text: 'I built a RAG system that used hybrid search to retrieve technical documentation and answer complex domain questions.',
    timestamp: '11:41 AM',
  },
  {
    id: '3',
    sender: 'ai',
    text: 'Interesting. Why did you choose that retrieval approach?',
    timestamp: '11:41 AM',
  },
  {
    id: '4',
    sender: 'candidate',
    text: 'We needed keyword exact matching for specific API error codes alongside semantic search for conceptual user queries. BM25 sparse search combined with Dense Vector embeddings gave us optimal recall across both types of queries.',
    timestamp: '11:42 AM',
  },
  {
    id: '5',
    sender: 'ai',
    text: 'Makes sense. How did you handle chunking strategies and overlap for long technical documents to avoid losing context across boundaries?',
    timestamp: '11:43 AM',
  },
]

const MOCK_AI_RESPONSES = [
  "Good point on chunking boundaries. How did you evaluate the performance of your retrieval pipeline — did you use metrics like Reciprocal Rank Fusion or NDCG?",
  "That's a practical trade-off. How did you handle re-ranking, and did you encounter latency bottlenecks during peak traffic?",
  "Excellent explanation. Moving to prompt engineering — how did you prevent prompt injection or hallucination when serving generated technical answers to users?",
]

export default function InterviewPage() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES)
  const [isThinking, setIsThinking] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState(3)
  const [isComplete, setIsComplete] = useState(false)

  const handleSendMessage = (userText) => {
    const userMsg = {
      id: Date.now().toString(),
      sender: 'candidate',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    // Append candidate message
    setMessages((prev) => [...prev, userMsg])
    setIsThinking(true)

    // Simulate AI thinking and response
    setTimeout(() => {
      const responseIndex = (messages.length) % MOCK_AI_RESPONSES.length
      const aiResponseText = MOCK_AI_RESPONSES[responseIndex]

      const aiMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: aiResponseText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      setMessages((prev) => [...prev, aiMsg])
      setIsThinking(false)
      setCurrentQuestion((q) => {
        const nextQ = Math.min(8, q + 1)
        if (nextQ === 8) {
          // Final question reached, mark interview as complete
          setIsComplete(true)
        }
        return nextQ
      })
    }, 1500)
  }

  return (
    <div className="h-screen w-screen bg-[#080B0A] text-[#F3F7F2] font-sans flex flex-col overflow-hidden selection:bg-[#C8FF3D] selection:text-[#080B0A]">
      
      {/* 1. Header & 9. Progress Bar */}
      <InterviewHeader currentQuestion={currentQuestion} totalQuestions="8+" />
      <InterviewProgress currentQuestion={currentQuestion} totalNum={8} />

      {/* 2. Desktop Two-Column Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* 3. Left Panel: Interview Journey (Desktop view, hidden on mobile) */}
        <div className="hidden lg:block h-full">
          <InterviewJourney currentQuestion={currentQuestion} />
        </div>

        {/* 4., 5., 6., 7., 8. Right Panel: Main Chat Conversation & Input Area */}
        {isComplete ? (
          <div className="flex flex-col items-center justify-center flex-1 p-8 bg-primary-surface text-primary rounded-lg border border-subtle shadow-lg animate-fadeIn">
            <div className="text-4xl font-bold mb-4 text-primary">✓ INTERVIEW COMPLETE</div>
            <p className="mb-6 text-lg text-primary">Nice work. You've completed the technical interview.</p>
            <p className="mb-6 text-lg text-primary">Your personalized performance report is ready.</p>
            <Link to="/report" className="px-6 py-3 bg-primary-accent text-primary font-medium rounded-md hover:bg-primary-accent/90 transition-shadow shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary-accent">View Interview Report →</Link>
          </div>
        ) : (
          <div className="flex-1 flex flex-col h-full overflow-hidden">
            <ChatWindow
              messages={messages}
              isThinking={isThinking}
              onSendMessage={handleSendMessage}
            />
          </div>
        )}

      </div>

    </div>
  )
}
