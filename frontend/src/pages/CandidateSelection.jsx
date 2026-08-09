import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { candidateData } from '../data/candidateData'

export default function CandidateSelection() {
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const navigate = useNavigate()

  const handleStartInterview = () => {
    if (selectedCandidate) {
      // Store selected candidate in localStorage or state if needed later, then navigate
      localStorage.setItem('selectedCandidate', JSON.stringify(selectedCandidate))
      navigate('/interview')
    }
  }

  return (
    <div className="min-h-screen bg-[#080B0A] text-[#F3F7F2] font-sans flex flex-col selection:bg-[#C8FF3D] selection:text-[#080B0A]">
      {/* Top Minimal Navigation */}
      <Navbar />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 lg:px-12 py-10 flex flex-col justify-between">
        <div className="space-y-8">
          {/* Header */}
          <div className="text-center space-y-3">
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F3F7F2]">
              Choose Your Candidate
            </h1>
            <p className="text-[#B1BBB3] text-sm sm:text-base max-w-xl mx-auto">
              Select a candidate profile to begin the technical interview.
            </p>
          </div>

          {/* Candidate Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {candidateData.map((candidate) => {
              const isSelected = selectedCandidate?.id === candidate.id
              return (
                <div
                  key={candidate.id}
                  onClick={() => setSelectedCandidate(candidate)}
                  className={`flex flex-col justify-between p-6 rounded-xl border transition-all duration-300 cursor-pointer bg-[#101513] select-none ${
                    isSelected
                      ? 'border-[#C8FF3D] shadow-[0_0_20px_rgba(200,255,61,0.18)]'
                      : 'border-[#263029] hover:border-[#C8FF3D]/40'
                  }`}
                >
                  <div className="space-y-4">
                    {/* Header: Name + Ready Status */}
                    <div className="flex items-center justify-between gap-2">
                      <h2 className="text-lg font-bold text-[#F3F7F2] truncate">
                        {candidate.name}
                      </h2>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#7DFFB2]" />
                        <span className="text-xs font-mono text-[#7DFFB2]">
                          {candidate.status}
                        </span>
                      </div>
                    </div>

                    {/* Role & Experience */}
                    <div className="space-y-1">
                      <div className="text-sm font-semibold text-[#C8FF3D]">
                        {candidate.role}
                      </div>
                      <div className="text-xs font-mono text-[#727D75]">
                        {candidate.experience}
                      </div>
                    </div>

                    {/* Technical Profile Description */}
                    <p className="text-xs text-[#B1BBB3] leading-relaxed min-h-[48px]">
                      {candidate.description}
                    </p>

                    {/* Relevant Skills */}
                    <div className="space-y-2">
                      <div className="text-[10px] font-mono uppercase tracking-wider text-[#727D75]">
                        AI / Data Engineering
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {candidate.skills.map((skill, index) => (
                          <span
                            key={index}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#151B17] border border-[#263029] text-[#B1BBB3]"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Select button */}
                  <div className="pt-6">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedCandidate(candidate)
                      }}
                      className={`w-full py-2.5 px-4 rounded-lg font-bold text-xs transition-all duration-200 cursor-pointer ${
                        isSelected
                          ? 'bg-[#C8FF3D] text-[#080B0A] shadow-[0_0_15px_rgba(200,255,61,0.25)]'
                          : 'bg-[#151B17] border border-[#263029] text-[#F3F7F2] hover:bg-[#263029]'
                      }`}
                    >
                      {isSelected ? '✓ Selected' : 'Select Candidate'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between pt-12 max-w-6xl w-full mx-auto">
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg border border-[#263029] text-[#B1BBB3] hover:text-[#F3F7F2] hover:bg-[#151B17] transition-all text-sm font-semibold"
          >
            ← Back
          </Link>
          <button
            onClick={handleStartInterview}
            disabled={!selectedCandidate}
            className={`inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg font-bold text-sm transition-all duration-200 shadow-md ${
              selectedCandidate
                ? 'bg-[#C8FF3D] text-[#080B0A] hover:bg-[#d5ff66] glow-accent-hover cursor-pointer'
                : 'bg-[#151B17] border border-[#263029] text-[#727D75] cursor-not-allowed opacity-50'
            }`}
          >
            Start Interview →
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#263029] bg-[#080B0A] py-8 px-6 text-center mt-auto">
        <p className="text-xs font-mono text-[#727D75]">
          AI-VibeCoders &bull; AI Technical Interview Agent &bull; Midnight Electric Theme
        </p>
      </footer>
    </div>
  )
}
