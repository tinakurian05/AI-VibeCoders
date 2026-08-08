import { useState, useRef } from 'react'

export default function ChatInput({ onSendMessage, disabled = false }) {
  const [text, setText] = useState('')
  const textareaRef = useRef(null)

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (!text.trim() || disabled) return
    onSendMessage(text.trim())
    setText('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleChange = (e) => {
    setText(e.target.value)
    // Auto adjust height up to 140px
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(140, textareaRef.current.scrollHeight)}px`
    }
  }

  return (
    <div className="p-4 border-t border-[#263029] bg-[#101513] sticky bottom-0 z-30">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-end gap-3">
        
        {/* Text Area Input */}
        <div className="flex-1 bg-[#151B17] border border-[#263029] focus-within:border-[#C8FF3D]/60 rounded-xl p-3 shadow-inner transition-colors">
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Type your answer..."
            className="w-full bg-transparent text-[#F3F7F2] placeholder-[#727D75] text-sm focus:outline-none resize-none overflow-y-auto max-h-36 font-sans leading-relaxed"
          />
          <div className="flex items-center justify-between pt-2 border-t border-[#263029]/50 text-[11px] font-mono text-[#727D75]">
            <span>Press <kbd className="px-1 py-0.5 rounded bg-[#080B0A] border border-[#263029] text-[#B1BBB3]">Enter ↵</kbd> to send</span>
            <span><kbd className="px-1 py-0.5 rounded bg-[#080B0A] border border-[#263029] text-[#B1BBB3]">Shift + Enter</kbd> for line break</span>
          </div>
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!text.trim() || disabled}
          className={`h-11 px-5 rounded-xl font-bold text-sm flex items-center gap-2 shrink-0 transition-all ${
            text.trim() && !disabled
              ? 'bg-[#C8FF3D] text-[#080B0A] hover:bg-[#d5ff66] glow-accent-hover cursor-pointer active:scale-95'
              : 'bg-[#151B17] border border-[#263029] text-[#727D75] cursor-not-allowed'
          }`}
        >
          <span>Send</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>

      </form>
    </div>
  )
}
