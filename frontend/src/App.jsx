import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import WelcomePage from './pages/WelcomePage'
import CandidateSelection from './pages/CandidateSelection'
import InterviewPage from './pages/InterviewPage'
import ReportPage from './pages/ReportPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/candidates" element={<CandidateSelection />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/report" element={<ReportPage />} />
      </Routes>
    </Router>
  )
}

export default App

