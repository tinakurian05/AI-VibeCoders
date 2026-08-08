export default function InterviewJourney({ currentQuestion = 3 }) {
  const journeyItems = [
    { title: 'Introduction', state: 'completed' },
    { title: 'Embeddings & Retrieval', state: 'completed' },
    { title: 'Prompt Engineering', state: 'active' },
    { title: 'Agents & MCP', state: 'upcoming' },
    { title: 'Deployment', state: 'upcoming' },
  ]

  return (
    <aside className="w-64 bg-[#101513] border-r border-[#263029] flex flex-col h-full select-none">
      
      {/* Panel Header */}
      <div className="p-5 border-b border-[#263029]">
        <h2 className="text-xs font-mono font-bold tracking-wider text-[#F3F7F2] uppercase flex items-center gap-2">
          <svg className="w-3.5 h-3.5 text-[#C8FF3D]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Interview Journey
        </h2>
      </div>

      {/* Topic List */}
      <div className="flex-1 p-4 space-y-2 overflow-y-auto">
        {journeyItems.map((item, index) => {
          const isCompleted = item.state === 'completed'
          const isActive = item.state === 'active'

          return (
            <div
              key={index}
              className={`flex items-center gap-3 p-3 rounded-xl border text-xs font-mono transition-all ${
                isActive
                  ? 'bg-[#151B17] border-[#C8FF3D]/50 text-[#F3F7F2] shadow-[0_0_15px_rgba(200,255,61,0.1)]'
                  : isCompleted
                  ? 'bg-[#101513] border-transparent text-[#7DFFB2]'
                  : 'bg-transparent border-transparent text-[#727D75]'
              }`}
            >
              {/* Icon Marker */}
              <div className="shrink-0 font-bold text-sm">
                {isCompleted && <span className="text-[#7DFFB2]">✓</span>}
                {isActive && <span className="text-[#C8FF3D] animate-pulse">●</span>}
                {!isCompleted && !isActive && <span className="text-[#727D75]">○</span>}
              </div>

              {/* Title */}
              <span className={`truncate ${isActive ? 'font-semibold text-[#F3F7F2]' : ''}`}>
                {item.title}
              </span>
            </div>
          )
        })}
      </div>

      {/* Panel Footer */}
      <div className="p-4 border-t border-[#263029] bg-[#080B0A]/50 text-center">
        <span className="text-xs font-mono text-[#727D75]">
          <strong className="text-[#C8FF3D] font-normal">{currentQuestion}</strong> of 8+ questions
        </span>
      </div>

    </aside>
  )
}
