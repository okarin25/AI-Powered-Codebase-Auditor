import React, { useEffect, useState } from 'react';
import { motion, animate } from 'framer-motion';

interface ScoreWidgetProps {
  score: number;
}

export const ScoreWidget: React.FC<ScoreWidgetProps> = ({ score }) => {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    const controls = animate(0, score, {
      duration: 1.8,
      ease: [0.19, 1, 0.22, 1],
      onUpdate: (latest) => setDisplayScore(Math.round(latest))
    });
    return () => controls.stop();
  }, [score]);

  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
      style={{ background: 'var(--color-pure-white)', borderRadius: '16px', padding: '60px 40px', boxShadow: 'var(--shadow-xl)', display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative', overflow: 'hidden' }}
    >
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px', background: 'var(--gradient-ember-orange)' }} />
      
      <div style={{ fontFamily: 'var(--font-louize)', fontSize: '130px', fontWeight: 400, lineHeight: '1', color: 'var(--color-midnight-ink)', letterSpacing: '-4px', marginBottom: '12px' }}>
        {displayScore}
        <span style={{ fontSize: '24px', letterSpacing: 'normal', color: 'var(--color-steel)' }}>/100</span>
      </div>

      <div className="micro-eyebrow" style={{ fontSize: '14px', letterSpacing: '2px', color: 'var(--color-deep-slate)' }}>
        System Stability Index Assessment
      </div>
    </motion.div>
  );
};