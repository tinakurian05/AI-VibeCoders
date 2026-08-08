import { Sliders, Layers, Award } from 'lucide-react'

const features = [
  {
    title: 'ADAPTIVE',
    description: 'Questions evolve based on your responses.',
    icon: Sliders,
    badge: 'Dynamic Depth',
  },
  {
    title: 'CURRICULUM-AWARE',
    description: "Your interview reflects what you've learned.",
    icon: Layers,
    badge: 'Context Synced',
  },
  {
    title: 'PERSONALIZED FEEDBACK',
    description: 'Get strengths, gaps, and next steps.',
    icon: Award,
    badge: 'Actionable Report',
  },
]

export default function FeatureCards() {
  return (
    <section className="py-12 border-t border-[#263029]/60">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((feature, idx) => {
          const Icon = feature.icon
          return (
            <div 
              key={idx}
              className="bg-[#101513] border border-[#263029] p-6 rounded-2xl space-y-4 text-left transition-all duration-300 hover:border-[#263029]/80 hover:bg-[#151B17]/70 hover:shadow-xl group"
            >
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-[#151B17] border border-[#263029] flex items-center justify-center text-[#C8FF3D] group-hover:border-[#C8FF3D]/40 transition-colors">
                  <Icon className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-mono text-[#727D75] uppercase tracking-wider px-2 py-0.5 rounded bg-[#080B0A] border border-[#263029]">
                  {feature.badge}
                </span>
              </div>

              <div className="space-y-2">
                <h3 className="text-xs font-mono font-bold tracking-wider text-[#F3F7F2] uppercase">
                  {feature.title}
                </h3>
                <p className="text-sm text-[#B1BBB3] leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
