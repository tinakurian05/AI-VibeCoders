const topics = [
  'Embeddings',
  'RAG',
  'Prompting',
  'Agents',
  'MCP',
  'Deployment',
]

export default function TopicSection() {
  return (
    <section className="py-10 border-t border-[#263029]/60">
      <div className="bg-[#101513]/60 border border-[#263029] p-8 rounded-2xl text-center space-y-6">
        
        <p className="text-xs font-mono text-[#727D75] uppercase tracking-widest">
          Built around your learning journey.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3">
          {topics.map((topic, idx) => (
            <span
              key={idx}
              className="px-4 py-2 rounded-xl bg-[#151B17] border border-[#263029] text-xs font-mono text-[#B1BBB3] tracking-wide select-none transition-colors duration-200 hover:text-[#F3F7F2] hover:border-[#727D75]"
            >
              {topic}
            </span>
          ))}
        </div>

      </div>
    </section>
  )
}
