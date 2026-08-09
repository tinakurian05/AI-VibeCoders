import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { api } from '../services/api'

export default function CandidateSelection() {
  const [candidates, setCandidates] = useState([])
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    let active = true
    api.getCandidates()
      .then(data => {
        if (active) {
          setCandidates(data.candidates || [])
          setLoading(false)
        }
      })
      .catch(err => {
        if (active) {
          console.error(err)
          setError('Unable to load candidates. Please ensure the backend server is running.')
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [])

  const handleStartInterview = () => {
    if (selectedCandidate && selectedCandidate.eligible) {
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

          {/* Error Message */}
          {error && (
            <div className="max-w-md mx-auto p-4 bg-red-950/40 border border-red-900 rounded-lg text-red-200 text-sm text-center">
              {error}
            </div>
          )}

          {/* Loading State */}
          {loading ? (
            <div className="text-center py-20 font-mono text-sm text-[#727D75]">
              Loading candidate profiles...
            </div>
          ) : (
            /* Candidate Grid */
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {candidates.map((candidate) => {
                const isSelected = selectedCandidate?.candidateId === candidate.candidateId
                const isEligible = candidate.eligible
                return (
                  <div
                    key={candidate.candidateId}
                    onClick={() => isEligible && setSelectedCandidate(candidate)}
                    className={`flex flex-col justify-between p-6 rounded-xl border transition-all duration-300 bg-[#101513] select-none ${
                      !isEligible 
                        ? 'border-red-950/40 opacity-50 cursor-not-allowed' 
                        : isSelected
                        ? 'border-[#C8FF3D] shadow-[0_0_20px_rgba(200,255,61,0.18)] cursor-pointer'
                        : 'border-[#263029] hover:border-[#C8FF3D]/40 cursor-pointer'
                    }`}
                  >
                    <div className="space-y-4">
                      {/* Header: Name + Ready Status */}
                      <div className="flex items-center justify-between gap-2">
                        <h2 className="text-lg font-bold text-[#F3F7F2] truncate">
                          {candidate.name}
                        </h2>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className={`w-1.5 h-1.5 rounded-full ${isEligible ? 'bg-[#7DFFB2]' : 'bg-red-500'}`} />
                          <span className={`text-xs font-mono ${isEligible ? 'text-[#7DFFB2]' : 'text-red-400'}`}>
                            {isEligible ? 'Ready' : 'Ineligible'}
                          </span>
                        </div>
                      </div>

                      {/* Role & Experience */}
                      <div className="space-y-1">
                        <div className="text-sm font-semibold text-[#C8FF3D]">
                          {candidate.jobRole}
                        </div>
                        <div className="text-xs font-mono text-[#727D75]">
                          {candidate.yearsExperience} years experience
                        </div>
                      </div>

                      {/* Technical Profile Description */}
                      <p className="text-xs text-[#B1BBB3] leading-relaxed min-h-[48px]">
                        {isEligible 
                          ? `Eligible candidate profile prepared for technical interview evaluation.`
                          : `Candidate is currently not eligible. Reason: ${candidate.eligibilityReason || 'Does not meet minimum requirements.'}`
                        }
                      </p>
                    </div>

                    {/* Select button */}
                    <div className="pt-6">
                      <button
                        type="button"
                        disabled={!isEligible}
                        onClick={(e) => {
                          e.stopPropagation()
                          if (isEligible) setSelectedCandidate(candidate)
                        }}
                        className={`w-full py-2.5 px-4 rounded-lg font-bold text-xs transition-all duration-200 ${
                          !isEligible
                            ? 'bg-[#151B17] border border-red-950 text-red-400/40 cursor-not-allowed'
                            : isSelected
                            ? 'bg-[#C8FF3D] text-[#080B0A] shadow-[0_0_15px_rgba(200,255,61,0.25)] cursor-pointer'
                            : 'bg-[#151B17] border border-[#263029] text-[#F3F7F2] hover:bg-[#263029] cursor-pointer'
                        }`}
                      >
                        {!isEligible ? 'Ineligible' : isSelected ? '✓ Selected' : 'Select Candidate'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
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
            disabled={!selectedCandidate || !selectedCandidate.eligible}
            className={`inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg font-bold text-sm transition-all duration-200 shadow-md ${
              selectedCandidate && selectedCandidate.eligible
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

