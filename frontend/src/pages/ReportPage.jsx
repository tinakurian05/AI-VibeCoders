import React, { useState } from 'react'

import { reportData } from '../data/reportData';



// -----------------------------------------------------------------------------
// Re‑usable UI components
// -----------------------------------------------------------------------------
function ProgressBar({ value, color = 'bg-accent-primary' }) {
  return (
    <div className="w-full bg-bg-app rounded h-4 overflow-hidden">
      <div
        className={`${color} h-4 rounded transition-all duration-700`}
        style={{ width: `${value}%` }}
      ></div>
    </div>
  )
}

function CircularScore({ score, max = 100, label }) {
  const percent = Math.round((score / max) * 100)
  const ringStyle = {
    background: `conic-gradient(#C8FF3D ${percent}deg, #263029 ${percent}deg)`,
  }
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32 mb-2">
        <div className="absolute inset-0 rounded-full" style={ringStyle}></div>
        <div className="absolute inset-2 bg-surface-primary rounded-full flex items-center justify-center">
          <span className="text-4xl font-bold text-accent-primary">{score}</span>
        </div>
        <div className="absolute inset-0 flex items-end justify-center pb-2 text-sm text-text-secondary">
          /{max}
        </div>
      </div>
      <div className="text-accent-primary font-semibold">{label}</div>
    </div>
  )
}

function TopicCard({ name, performance, label }) {
  return (
    <div className="bg-surface-secondary rounded p-4 hover:shadow-md transition-shadow">
      <h3 className="font-medium mb-1">{name}</h3>
      <ProgressBar value={performance} />
      <span className="mt-2 block text-accent-secondary font-medium text-right">
        {label}
      </span>
    </div>
  )
}

function Timeline({ steps }) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-4 md:gap-8 overflow-x-auto py-2">
      {steps.map((step, i) => (
        <div key={i} className="flex flex-col items-center">
          <div
            className={`w-12 h-12 rounded-full flex items-center justify-center text-sm font-medium
              ${step.label === 'Strong' && 'bg-accent-primary text-bg-app'}
              ${step.label === 'Good' && 'bg-accent-secondary text-bg-app'}
              ${step.label === 'Needs improvement' && 'bg-bg-app border border-accent-primary text-accent-primary'}`}
          >
            Q{step.q}
          </div>
          {i < steps.length - 1 && <div className="w-8 h-0 border-t border-text-muted mt-2"></div>}
        </div>
      ))}
    </div>
  )
}

function QuestionCard({ q, isOpen, onToggle }) {
  return (
    <div className="bg-surface-primary rounded-lg p-4 shadow transition-all duration-300">
      <button
        onClick={onToggle}
        className="w-full flex justify-between items-center text-left focus:outline-none"
      >
        <div>
          <span className="font-medium mr-2">Q{q.number} – {q.topic}</span>
          <span className="text-accent-primary">{q.label}</span>
        </div>
        <span className="text-text-muted">{isOpen ? '−' : '+'}</span>
      </button>
      {isOpen && (
        <div className="mt-4 text-sm space-y-3">
          <p><strong>AI QUESTION:</strong> {q.aiQuestion}</p>
          <p><strong>YOUR ANSWER:</strong> {q.candidateAnswer}</p>
          <p><strong>AI FEEDBACK:</strong> {q.aiFeedback}</p>
          <p><strong>WHAT YOU DID WELL:</strong> {q.whatYouDidWell}</p>
          <p><strong>WHAT TO IMPROVE:</strong> {q.whatToImprove}</p>
          <p><strong>SUGGESTED NEXT STEP:</strong> {q.nextStep}</p>
        </div>
      )}
    </div>
  )
}

function NextStepCard({ idx, title, description }) {
  return (
    <div className="bg-surface-secondary rounded p-4 hover:scale-105 transform transition-transform duration-200 text-center">
      <div className="text-2xl font-bold text-accent-primary mb-1">0{idx + 1}</div>
      <h3 className="font-medium mb-2">{title}</h3>
      <p className="text-sm text-text-secondary">{description}</p>
    </div>
  )
}

function ReportPage() {
  const [openQuestion, setOpenQuestion] = useState(null);
  const toggle = (idx) => setOpenQuestion(openQuestion === idx ? null : idx);
  const data = reportData;

  return (
    <div className="min-h-screen bg-bg-app text-text-primary py-8 px-4 md:px-8 lg:px-12">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-2 flex items-center justify-center gap-3">
            YOUR INTERVIEW REPORT
            <span className="bg-accent-primary text-bg-app text-xs font-mono px-2 py-1 rounded">✓ Completed</span>
          </h1>
          <p className="text-text-secondary mb-2">
            Technical Interview · 8 questions · Completed today
          </p>
          <p className="text-text-muted italic">Here's how you performed across the interview.</p>
        </header>

        {/* Performance Overview */}
        <section className="grid md:grid-cols-2 gap-8 mb-12">
          <div className="bg-surface-primary rounded-lg p-6 shadow-md flex flex-col items-center">
            <h2 className="text-xl font-semibold mb-4">Overall Performance</h2>
            <CircularScore score={data.overallScore} label={data.overallLabel} />
          </div>
          <div className="bg-surface-primary rounded-lg p-6 shadow-md">
            <h2 className="text-xl font-semibold mb-4">Performance Snapshot</h2>
            {data.dimensions.map((dim, i) => (
              <div key={i} className="mb-4">
                <div className="flex justify-between mb-1">
                  <span className="font-medium">{dim.name}</span>
                  <span>{dim.value}%</span>
                </div>
                <ProgressBar value={dim.value} />
              </div>
            ))}
          </div>
        </section>

        {/* Topic Performance */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold mb-6 text-center">Topic Performance</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.topics.map((t, i) => (
              <TopicCard key={i} name={t.name} performance={t.performance} label={t.label} />
            ))}
          </div>
        </section>

        {/* Key Takeaways */}
        <section className="mb-12 bg-surface-secondary rounded-lg p-6 shadow">
          <h2 className="text-xl font-semibold mb-4 text-center">Key Takeaways</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium mb-2 text-accent-primary">Strengths</h3>
              <ul className="list-disc list-inside space-y-1">
                {data.keyTakeaways.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-2 text-accent-primary">Focus Areas</h3>
              <ul className="list-disc list-inside space-y-1">
                {data.keyTakeaways.focusAreas.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Interview Timeline */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold mb-4 text-center">Interview Timeline</h2>
          <Timeline steps={data.timeline} />
        </section>

        {/* Question Review */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold mb-6">Question Review</h2>
          <div className="space-y-4">
            {data.questions.map((q, idx) => (
              <QuestionCard key={idx} q={q} isOpen={openQuestion === idx} onToggle={() => toggle(idx)} />
            ))}
          </div>
        </section>

        {/* Recommended Next Steps */}
        <section className="mb-12">
          <h2 className="text-xl font-semibold mb-6 text-center">Recommended Next Steps</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            {data.nextSteps.map((step, idx) => (
              <NextStepCard key={idx} idx={idx} title={step.title} description={step.description} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
export default ReportPage;
