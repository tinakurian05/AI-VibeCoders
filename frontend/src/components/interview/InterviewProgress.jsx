export default function InterviewProgress({ currentQuestion = 3, totalNum = 8 }) {
  const percentage = Math.min(100, Math.round((currentQuestion / totalNum) * 100))

  return (
    <div className="w-full bg-[#101513] border-b border-[#263029]">
      <div className="w-full h-1 bg-[#151B17] relative overflow-hidden">
        <div 
          className="h-full bg-[#C8FF3D] transition-all duration-500 ease-out shadow-[0_0_10px_rgba(200,255,61,0.5)]"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
