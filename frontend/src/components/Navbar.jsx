import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <header className="border-b border-[#263029] bg-[#080B0A]/90 backdrop-blur-md sticky top-0 z-50 px-6 lg:px-12 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Left: Brand Logo & Title */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-[#151B17] border border-[#263029] flex items-center justify-center shadow-inner transition-all duration-200 group-hover:border-[#C8FF3D]/50">
            <svg 
              className="w-4 h-4 text-[#C8FF3D] transition-transform duration-200 group-hover:scale-110" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold tracking-wider text-[#F3F7F2] uppercase">
              AI-VibeCoders
            </span>
            <span className="text-[#263029] font-mono">/</span>
            <span className="text-xs font-mono text-[#B1BBB3] tracking-wide group-hover:text-[#F3F7F2] transition-colors">
              AI Technical Interview Agent
            </span>
          </div>
        </Link>


        {/* Right: Mode & Status Indicator */}
        <div className="flex items-center gap-4">
          <span className="text-xs font-mono text-[#B1BBB3] hidden sm:inline-block">
            Text Interview
          </span>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#151B17] border border-[#263029]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#C8FF3D] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#C8FF3D]"></span>
            </span>
            <span className="text-xs font-mono text-[#7DFFB2]">Ready</span>
          </div>
        </div>

      </div>
    </header>
  )
}
