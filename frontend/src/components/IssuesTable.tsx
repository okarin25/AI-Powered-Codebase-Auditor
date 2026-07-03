import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { type FileIssue } from '../api/client';

interface IssuesTableProps {
  complexityIssues: FileIssue[];
  securityIssues: FileIssue[];
  lintIssues: FileIssue[];
}

const visualCurve = [0.19, 1, 0.22, 1] as const;

export const IssuesTable: React.FC<IssuesTableProps> = ({ complexityIssues, securityIssues, lintIssues }) => {
  const [activeTab, setActiveTab] = useState<'complexity' | 'security' | 'lint'>('complexity');

  const getTargetViewContext = () => {
    switch (activeTab) {
      case 'complexity': return { data: complexityIssues, color: 'var(--color-parchment-card)', accent: 'var(--color-deep-slate)' };
      case 'security': return { data: securityIssues, color: 'var(--color-blush-tint)', accent: 'var(--color-ember-orange)' };
      case 'lint': return { data: lintIssues, color: 'var(--color-slate-blue-card)', accent: 'var(--color-cobalt-link)' };
    }
  };

  const active = getTargetViewContext();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Tab Selectors with Shared Layout Underline Animation */}
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-start', position: 'relative' }}>
        {(['complexity', 'security', 'lint'] as const).map((tab) => {
          const isActive = activeTab === tab;
          const count = tab === 'complexity' ? complexityIssues.length : tab === 'security' ? securityIssues.length : lintIssues.length;
          
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                position: 'relative', background: 'transparent', border: 'none', padding: '12px 24px',
                fontFamily: 'var(--font-ui)', textTransform: 'uppercase', fontSize: '13px', fontWeight: 600,
                letterSpacing: '0.05em', color: isActive ? 'var(--color-midnight-ink)' : 'var(--color-slate)',
                cursor: 'pointer', transition: 'color 0.3s ease'
              }}
            >
              <span style={{ position: 'relative', zIndex: 2 }}>
                {tab} ({count})
              </span>
              {isActive && (
                <motion.div
                  layoutId="activeTabIndicator"
                  className="tab-highlight-pill"
                  style={{
                    position: 'absolute', inset: 0, borderRadius: '100px',
                    border: '1px solid var(--color-mist)', background: 'var(--color-pure-white)', zIndex: 1
                  }}
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Dynamic Smooth Height Morphing Card Viewport */}
      <div style={{ position: 'relative', overflow: 'hidden', width: '100%' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.5, ease: visualCurve }}
            style={{ background: active.color, borderRadius: '16px', padding: '40px', textAlign: 'left' }}
          >
            <h3 className="display-headline" style={{ fontSize: '40px', marginBottom: '32px' }}>
              Detected <span style={{ fontStyle: 'italic' }}>{activeTab}</span> properties.
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {active.data.length > 0 ? (
                active.data.map((issue, idx) => (
                  <motion.div 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: idx * 0.04, ease: visualCurve }}
                    whileHover={{ scale: 1.005, y: -2 }}
                    key={idx} 
                    style={{ background: 'var(--color-pure-white)', padding: '24px 32px', borderRadius: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid rgba(0,0,0,0.02)', boxShadow: 'var(--shadow-sm)', transition: 'transform 0.2s cubic-bezier(0.19,1,0.22,1)' }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', paddingRight: '20px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 500, color: 'var(--color-midnight-ink)' }}>
                        {issue.file} <span style={{ color: 'var(--color-steel)' }}>: line {issue.line ?? 'root'}</span>
                      </span>
                      <span style={{ fontSize: '15.5px', color: 'var(--color-storm)' }}>{issue.message}</span>
                    </div>
                    <span className="nunito-label" style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '1px', color: active.accent, padding: '4px 10px', background: 'var(--color-canvas-white)', borderRadius: '6px' }}>
                      {issue.severity}
                    </span>
                  </motion.div>
                ))
              ) : (
                <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--color-steel)', fontStyle: 'italic', fontFamily: 'var(--font-louize)', fontSize: '20px' }}>
                  No structural exceptions mapped in this partition category.
                </div>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};