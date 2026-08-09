import { useState, useEffect } from 'react'
import InterviewHeader from '../components/interview/InterviewHeader'
import { Link } from 'react-router-dom'
import InterviewProgress from '../components/interview/InterviewProgress'
import InterviewJourney from '../components/interview/InterviewJourney'
import ChatWindow from '../components/interview/ChatWindow'
import { api } from '../services/api'


export default function InterviewPage() {
  const [candidate] = useState(() => {
    try {
      const saved = localStorage.getItem('selectedCandidate')
      return saved ? JSON.parse(saved) : { name: 'Sarah Johnson', jobRole: 'Senior Data Engineer', candidateId: 'CAND-001' }
    } catch (e) {
      return { name: 'Sarah Johnson', jobRole: 'Senior Data Engineer', candidateId: 'CAND-001' }
    }
  })

  const [sessionId] = useState(() => {
    // Generate one persistent session ID for the entire interview
    return crypto.randomUUID()
  })

  const [messages, setMessages] = useState([])
  const [isThinking, setIsThinking] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState(1)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState(null)

  // Start interview on mount
  useEffect(() => {
    let active = true
    setIsThinking(true)
    api.startInterview(sessionId, candidate.candidateId)
      .then(res => {
        if (active) {
          const firstMsg = {
            id: 'first-q',
            sender: 'ai',
            text: res.reply,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          }
          setMessages([firstMsg])
          setIsThinking(false)
          if (res.done) {
            setIsComplete(true)
          }
        }
      })
      .catch(err => {
        if (active) {
          console.error(err)
          setError('Unable to start interview. Please ensure backend is running.')
          setIsThinking(false)
        }
      })

    return () => {
      active = false
    }
  }, [sessionId, candidate.candidateId])

  const handleSendMessage = (userText) => {
    if (!userText.trim()) return

    const userMsg = {
      id: Date.now().toString(),
      sender: 'candidate',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    setIsThinking(true)
    setError(null)

    api.submitAnswer(sessionId, userText)
      .then(res => {
        const aiMsg = {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: res.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
        setMessages((prev) => [...prev, aiMsg])
        setIsThinking(false)
        setCurrentQuestion((q) => q + 1)
        if (res.done) {
          setIsComplete(true)
        }
      })
      .catch(err => {
        console.error(err)
        setError('Failed to receive response from backend server.')
        setIsThinking(false)
      })
  }

  const displayCandidate = {
    name: candidate.name,
    role: candidate.jobRole || candidate.role || 'Data Engineer'
  }

  return (
    <div className="h-screen w-screen bg-[#080B0A] text-[#F3F7F2] font-sans flex flex-col overflow-hidden selection:bg-[#C8FF3D] selection:text-[#080B0A]">
      
      {/* 1. Header & 9. Progress Bar */}
      <InterviewHeader currentQuestion={currentQuestion} totalQuestions="8+" candidate={displayCandidate} />
      <InterviewProgress currentQuestion={currentQuestion} totalNum={8} />

      {/* 2. Desktop Two-Column Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* 3. Left Panel: Interview Journey (Desktop view, hidden on mobile) */}
        <div className="hidden lg:block h-full">
          <InterviewJourney currentQuestion={currentQuestion} />
        </div>

        {/* 4., 5., 6., 7., 8. Right Panel: Main Chat Conversation & Input Area */}
        <div className="flex-1 flex flex-col h-full overflow-hidden relative">
          
          {error && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 px-4 py-2 bg-red-950 border border-red-800 text-red-200 text-xs rounded-lg shadow-lg font-mono">
              {error}
            </div>
          )}

          {isComplete ? (
            <div className="flex flex-col items-center justify-center flex-1 p-8 bg-[#101513] text-[#F3F7F2] rounded-lg border border-[#263029] shadow-lg animate-fadeIn">
              <div className="text-4xl font-bold mb-4 text-[#C8FF3D]">✓ INTERVIEW COMPLETE</div>
              <p className="mb-6 text-lg text-[#B1BBB3]">Nice work. You've completed the technical interview.</p>
              <p className="mb-6 text-lg text-[#B1BBB3]">Your personalized performance report is ready.</p>
              <Link to="/report" className="px-6 py-3 bg-[#C8FF3D] text-[#080B0A] font-bold rounded-lg hover:bg-[#d5ff66] transition-all shadow-md">View Interview Report →</Link>
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

    </div>
  )
}

