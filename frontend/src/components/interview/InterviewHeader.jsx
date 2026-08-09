import { Link } from 'react-router-dom'

export default function InterviewHeader({ currentQuestion = 3, totalQuestions = '8+', candidate }) {
  return (
    <header className="border-b border-[#263029] bg-[#101513] px-4 sm:px-8 py-3 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-40">
      
      {/* Left: Brand / Title */}
      <Link to="/" className="flex items-center gap-2 group">
        <div className="w-7 h-7 rounded-md bg-[#151B17] border border-[#263029] flex items-center justify-center transition-colors group-hover:border-[#C8FF3D]/40">
          <svg className="w-3.5 h-3.5 text-[#C8FF3D]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-mono">
          <span className="font-semibold text-[#F3F7F2]">AI-VibeCoders</span>
          <span className="text-[#263029]">/</span>
          <span className="text-[#B1BBB3] hidden sm:inline group-hover:text-[#F3F7F2] transition-colors">
            AI Technical Interview
          </span>
        </div>
      </Link>

      {/* Candidate Info */}
      {candidate && (
        <div className="flex items-center gap-2 text-xs font-mono bg-[#151B17] border border-[#263029] px-3 py-1 rounded-md">
          <span className="text-[#727D75]">Interviewing:</span>
          <span className="text-[#C8FF3D] font-bold">{candidate.name}</span>
          <span className="text-[#727D75] truncate max-w-[150px] sm:max-w-none">({candidate.role})</span>
        </div>
      )}

      {/* Center: Question Counter */}
      <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-[#151B17] border border-[#263029] text-xs font-mono">
        <span className="text-[#727D75]">Question</span>
        <span className="text-[#C8FF3D] font-semibold">{currentQuestion}</span>
        <span className="text-[#727D75]">of</span>
        <span className="text-[#F3F7F2]">{totalQuestions}</span>
      </div>

      {/* Right: Live Status Indicator */}
      <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#151B17] border border-[#263029]">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#C8FF3D] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#C8FF3D]"></span>
        </span>
        <span className="text-[11px] font-mono text-[#7DFFB2] hidden sm:inline">
          Interview in progress
        </span>
      </div>

    </header>
  )
}

