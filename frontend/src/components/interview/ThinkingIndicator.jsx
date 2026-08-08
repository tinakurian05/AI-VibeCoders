import { motion } from 'framer-motion'

export default function ThinkingIndicator() {
  const dotVariants = {
    initial: { opacity: 0.2, y: 0 },
    animate: { opacity: 1, y: -2 },
  }

  const containerVariants = {
    initial: {},
    animate: {
      transition: {
        staggerChildren: 0.18,
        repeat: Infinity,
        repeatType: 'reverse',
        duration: 0.6,
      },
    },
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="flex items-start gap-3 my-4"
    >
      {/* Lime AI Avatar Badge */}
      <div className="w-7 h-7 rounded-lg bg-[#151B17] border border-[#C8FF3D]/50 flex items-center justify-center shrink-0 shadow-sm mt-0.5">
        <span className="text-[10px] font-mono font-bold text-[#C8FF3D]">AI</span>
      </div>

      {/* Message Area */}
      <div className="space-y-1">
        {/* Header Tag */}
        <div className="flex items-center gap-2 text-[11px] font-mono">
          <span className="text-[#7DFFB2] font-medium">AI Interviewer</span>
          <span className="text-[10px] font-mono text-[#727D75]">&bull; Processing response</span>
        </div>

        {/* Dark Surface Bubble */}
        <div className="bg-[#151B17] border border-[#263029] px-4 py-3 rounded-2xl rounded-tl-sm text-xs font-mono text-[#B1BBB3] flex items-center gap-2 shadow-sm">
          <span>Thinking</span>
          <motion.div
            variants={containerVariants}
            initial="initial"
            animate="animate"
            className="inline-flex items-center gap-0.5 text-[#C8FF3D] font-bold text-sm tracking-widest"
          >
            <motion.span variants={dotVariants}>·</motion.span>
            <motion.span variants={dotVariants}>·</motion.span>
            <motion.span variants={dotVariants}>·</motion.span>
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}

