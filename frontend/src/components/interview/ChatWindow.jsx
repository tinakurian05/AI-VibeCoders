import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import ThinkingIndicator from './ThinkingIndicator'
import ChatInput from './ChatInput'

export default function ChatWindow({ messages, isThinking, onSendMessage }) {
  const scrollEndRef = useRef(null)

  const scrollToBottom = () => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isThinking])

  return (
    <div className="flex-1 flex flex-col h-full bg-[#080B0A] overflow-hidden">
      
      {/* Scrollable Message List */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 space-y-2">
        <div className="max-w-4xl mx-auto space-y-2">
          
          {/* Header Note */}
          <div className="text-center py-3 mb-6">
            <span className="inline-block px-3 py-1 rounded-full bg-[#151B17] border border-[#263029] text-[11px] font-mono text-[#7DFFB2]">
              Adaptive Technical Assessment Active &bull; Topic: Prompt Engineering & Retrieval
            </span>
          </div>

          {/* Messages */}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* AI Thinking Indicator */}
          {isThinking && <ThinkingIndicator />}

          <div ref={scrollEndRef} />
        </div>
      </div>

      {/* Prominent Chat Input Area */}
      <ChatInput onSendMessage={onSendMessage} disabled={isThinking} />

    </div>
  )
}
