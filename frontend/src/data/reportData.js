// Centralized mock data for ReportPage – easy to replace with real API data later
export const reportData = {
  // 1. Overall performance
  overallScore: 78,
  overallLabel: 'Strong', // performanceLevel

  // 2. Performance snapshot (dimensions)
  dimensions: [
    { name: 'Technical Knowledge', value: 80 },
    { name: 'Reasoning', value: 75 },
    { name: 'Answer Quality', value: 78 },
    { name: 'Problem Solving', value: 77 },
  ],

  // 3. Topic performance
  topics: [
    { name: 'RAG', performance: 85, label: 'Strong' },
    { name: 'Embeddings', performance: 70, label: 'Good' },
    { name: 'Prompting', performance: 65, label: 'Needs improvement' },
    { name: 'Agents', performance: 78, label: 'Good' },
    { name: 'MCP', performance: 72, label: 'Good' },
  ],

  // 4. Key takeaways
  keyTakeaways: {
    strengths: ['Strong understanding of RAG', 'Good technical reasoning'],
    focusAreas: ['Explain trade‑offs more clearly', 'Strengthen agent orchestration concepts'],
  },

  // 5. Interview timeline
  timeline: [
    { q: 1, label: 'Strong' },
    { q: 2, label: 'Good' },
    { q: 3, label: 'Needs improvement' },
    { q: 4, label: 'Good' },
    { q: 5, label: 'Strong' },
    { q: 6, label: 'Good' },
    { q: 7, label: 'Needs improvement' },
    { q: 8, label: 'Good' },
  ],

  // 6. Question review (expanded fields for potential future use)
  questions: [
    {
      number: 1,
      topic: 'RAG',
      label: 'Strong',
      summary: 'Great understanding of retrieval‑augmented generation.',
      aiQuestion: 'Explain how you would design a RAG system for a knowledge base.',
      candidateAnswer: 'I would start by ... (mock answer)',
      aiFeedback: 'Your answer covered the key components and trade‑offs.',
      whatYouDidWell: 'Clear architecture, mentioned chunking and indexing.',
      whatToImprove: 'Could elaborate on latency handling.',
      nextStep: 'Read about hybrid retrieval strategies.',
    },
    // Additional questions can be added here following the same structure
  ],

  // 7. Recommended next steps
  nextSteps: [
    { title: 'Strengthen hybrid retrieval', description: 'Read about hybrid retrieval strategies and practice implementation.' },
    { title: 'Practice trade‑off explanations', description: 'Take a few mock scenarios and articulate pros/cons.' },
    { title: 'Review agent orchestration', description: 'Study patterns for coordinating multiple AI agents.' },
  ],
};
