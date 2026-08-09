import { Link } from 'react-router-dom'
import ChatPreview from './ChatPreview'

export default function HeroSection() {
  return (
    <section className="py-12 lg:py-20">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
        
        {/* Left Column: Headline, Copy & Action */}
        <div className="lg:col-span-7 space-y-8 text-left">
          
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#151B17] border border-[#263029]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#C8FF3D]" />
            <span className="text-xs font-mono text-[#7DFFB2] tracking-wider uppercase font-semibold">
              AI-POWERED TECHNICAL INTERVIEW
            </span>
          </div>

          {/* Main Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[#F3F7F2] leading-[1.1]">
            Show <span className="text-[#C8FF3D] relative inline-block">
              what you know.
              <span className="absolute bottom-1 left-0 right-0 h-[2px] bg-[#C8FF3D]/30 rounded-full" />
            </span>
          </h1>

          {/* Supporting Text & Short Description */}
          <div className="space-y-4 max-w-2xl">
            <p className="text-xl font-medium text-[#F3F7F2] leading-snug">
              An adaptive technical interview built around your learning journey.
            </p>
            <p className="text-[#B1BBB3] text-base leading-relaxed">
              Have a real conversation with an AI interviewer. Explain your decisions, handle follow-up questions, and receive personalized feedback when you're done.
            </p>
          </div>

          {/* Primary CTA & Secondary Context */}
          <div className="pt-2 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <Link 
                to="/candidates"
                className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-[#C8FF3D] text-[#080B0A] font-bold text-base transition-all duration-200 hover:bg-[#d5ff66] glow-accent-hover active:scale-[0.98] cursor-pointer shadow-lg"
              >
                <span>Start Interview</span>
                <span className="text-lg">→</span>
              </Link>
            </div>


            <p className="text-xs font-mono text-[#727D75] flex items-center gap-2">
              <span className="w-1 h-1 rounded-full bg-[#7DFFB2]" />
              8+ questions &middot; Multiple curriculum areas &middot; Personalized feedback
            </p>
          </div>

        </div>

        {/* Right Column: Visual Interview Chat Preview */}
        <div className="lg:col-span-5">
          <ChatPreview />
        </div>

      </div>
    </section>
  )
}
