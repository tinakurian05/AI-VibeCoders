import Navbar from '../components/Navbar'
import HeroSection from '../components/HeroSection'
import FeatureCards from '../components/FeatureCards'
import TopicSection from '../components/TopicSection'

export default function WelcomePage() {
  return (
    <div className="min-h-screen bg-[#080B0A] text-[#F3F7F2] font-sans flex flex-col selection:bg-[#C8FF3D] selection:text-[#080B0A]">
      {/* Top Minimal Navigation */}
      <Navbar />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 lg:px-12 py-6 space-y-12">
        {/* Hero Section + Chat Preview */}
        <HeroSection />

        {/* Three Feature Cards */}
        <FeatureCards />

        {/* Bottom Topic Labels Section */}
        <TopicSection />
      </main>

      {/* Footer */}
      <footer className="border-t border-[#263029] bg-[#080B0A] py-8 px-6 text-center">
        <p className="text-xs font-mono text-[#727D75]">
          AI-VibeCoders &bull; AI Technical Interview Agent &bull; Midnight Electric Theme
        </p>
      </footer>
    </div>
  )
}
