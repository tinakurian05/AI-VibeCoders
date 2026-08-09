import { motion } from 'framer-motion'

export default function MessageBubble({ message }) {
  const isAi = message.sender === 'ai'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className={`flex items-start gap-3 my-4 ${isAi ? '' : 'flex-row-reverse'}`}
    >
      {/* Avatar */}
      <div
        className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-mono font-bold shadow-sm ${
          isAi
            ? 'bg-[#151B17] border border-[#C8FF3D]/40 text-[#C8FF3D]'
            : 'bg-[#151B17] border border-[#263029] text-[#F3F7F2]'
        }`}
      >
        {isAi ? 'AI' : 'YOU'}
      </div>

      {/* Message Content & Metadata */}
      <div className={`space-y-1 max-w-[85%] sm:max-w-[75%] ${isAi ? '' : 'text-right'}`}>
        
        {/* Sender Meta */}
        <div className={`flex items-center gap-2 text-[11px] font-mono ${isAi ? '' : 'justify-end'}`}>
          <span className={isAi ? 'text-[#7DFFB2] font-medium' : 'text-[#B1BBB3] font-medium'}>
            {isAi ? 'AI Technical Interviewer' : 'Candidate'}
          </span>
          <span className="text-[#727D75] text-[10px]">{message.timestamp || 'Just now'}</span>
        </div>

        {/* Message Box */}
        <div
          className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap shadow-sm border ${
            isAi
              ? 'bg-[#151B17] border-[#263029] text-[#F3F7F2] rounded-tl-sm'
              : 'bg-[#101513] border-[#C8FF3D]/30 text-[#F3F7F2] rounded-tr-sm text-left'
          }`}
        >
          {message.text}
        </div>

      </div>
    </motion.div>
  )
}
