import React from 'react';
import { motion } from 'framer-motion';

interface LoadingStateProps {
  progress: string | null;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ progress }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', textAlign: 'center' }}>
      <div style={{ position: 'relative', width: '120px', height: '120px', marginBottom: '40px' }}>
        {/* Soft, deep ambient light glow */}
        <motion.div
          style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: 'rgba(255,89,36,0.18)', filter: 'blur(16px)' }}
          animate={{ scale: [1, 1.25, 1], opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
        />
        <div style={{ position: 'absolute', inset: '24px', borderRadius: '50%', background: 'var(--color-pure-white)', border: '1px solid var(--color-mist)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-ember-orange)" strokeWidth="1.5">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>

      <div className="micro-eyebrow" style={{ letterSpacing: '3px', fontSize: '12px', marginBottom: '16px' }}>
        Magic is happening...
      </div>
      <h2 className="display-headline" style={{ fontSize: '36px', maxWidth: '440px', color: 'var(--color-deep-slate)' }}>
        {progress || 'Aggregating system configuration patterns.'}
      </h2>
    </div>
  );
};