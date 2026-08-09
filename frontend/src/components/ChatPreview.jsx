export default function ChatPreview() {
  return (
    <div className="w-full max-w-lg mx-auto lg:max-w-none bg-[#101513] border border-[#263029] rounded-2xl p-5 shadow-2xl space-y-4 relative overflow-hidden group">
      
      {/* Decorative top technical bar */}
      <div className="flex items-center justify-between pb-3 border-b border-[#263029]">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-[#C8FF3D]/80 animate-pulse" />
          <span className="text-xs font-mono text-[#F3F7F2] font-medium tracking-wide">
            LIVE INTERVIEW SESSION
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#727D75]">
          <span className="px-2 py-0.5 rounded bg-[#151B17] border border-[#263029] text-[#7DFFB2]">
            Q 01 / 08
          </span>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="space-y-4 pt-1">
        
        {/* Message 1: AI Interviewer */}
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-lg bg-[#151B17] border border-[#C8FF3D]/40 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
            <span className="text-[10px] font-mono font-bold text-[#C8FF3D]">AI</span>
          </div>
          <div className="space-y-1 max-w-[85%]">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-[#7DFFB2] font-medium">AI Interviewer</span>
              <span className="text-[10px] font-mono text-[#727D75]">Just now</span>
            </div>
            <div className="bg-[#151B17] border border-[#263029] text-[#F3F7F2] text-xs leading-relaxed p-3.5 rounded-2xl rounded-tl-sm shadow-sm">
              Let's start with your experience. Tell me about a system you built using retrieval.
            </div>
          </div>
        </div>

        {/* Message 2: Candidate */}
        <div className="flex items-start justify-end gap-3">
          <div className="space-y-1 max-w-[85%] text-right">
            <div className="flex items-center justify-end gap-2">
              <span className="text-[10px] font-mono text-[#727D75]">12s ago</span>
              <span className="text-[11px] font-mono text-[#B1BBB3] font-medium">Candidate</span>
            </div>
            <div className="bg-[#101513] border border-[#C8FF3D]/30 text-[#F3F7F2] text-xs leading-relaxed p-3.5 rounded-2xl rounded-tr-sm text-left shadow-sm">
              I built a RAG system using hybrid search to index technical documentation and handle complex domain queries...
            </div>
          </div>
          <div className="w-7 h-7 rounded-lg bg-[#151B17] border border-[#263029] flex items-center justify-center shrink-0 mt-0.5">
            <span className="text-[10px] font-mono text-[#B1BBB3]">YOU</span>
          </div>
        </div>

        {/* Message 3: AI Follow-up */}
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-lg bg-[#151B17] border border-[#C8FF3D]/40 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
            <span className="text-[10px] font-mono font-bold text-[#C8FF3D]">AI</span>
          </div>
          <div className="space-y-1 max-w-[85%]">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-[#7DFFB2] font-medium">AI Interviewer</span>
              <span className="text-[10px] font-mono text-[#C8FF3D]">Active follow-up</span>
            </div>
            <div className="bg-[#151B17] border border-[#263029] text-[#F3F7F2] text-xs leading-relaxed p-3.5 rounded-2xl rounded-tl-sm shadow-sm relative group-hover:border-[#C8FF3D]/30 transition-colors">
              Interesting. Why did you choose that retrieval approach?
            </div>
          </div>
        </div>

      </div>

      {/* Footer / Input Simulation */}
      <div className="pt-3 border-t border-[#263029] flex items-center justify-between text-xs text-[#727D75] font-mono">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#C8FF3D] animate-ping" />
          <span>Evaluation Engine: Adaptive Depth</span>
        </div>
        <span className="text-[11px] text-[#7DFFB2]">Interactive Demo</span>
      </div>

    </div>
  )
}
