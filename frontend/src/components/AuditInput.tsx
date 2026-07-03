import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Globe } from 'lucide-react';

interface AuditInputProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

// Fixed: Explicitly typed as a transition easing array for Framer Motion
const momentumEase = [0.19, 1, 0.22, 1] as const;

export const AuditInput: React.FC<AuditInputProps> = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [focused, setFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const checkedUrl = url.trim();

    if (!checkedUrl) {
      setError('An active, open repository address pointer is required.');
      return;
    }
    if (!/^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+\/?$/.test(checkedUrl)) {
      setError('Verify that the resource link follows standard GitHub formatting.');
      return;
    }
    onSubmit(checkedUrl);
  };

  return (
    <motion.div 
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.12, delayChildren: 0.1 } }
      }}
      style={{ maxWidth: '880px', width: '100%', margin: '120px auto 0', textAlign: 'center' }}
    >
      <motion.div variants={{ hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } }} transition={{ duration: 0.8, ease: momentumEase }} className="micro-eyebrow" style={{ marginBottom: '24px' }}>
        Codebase Architecture Preservation Engine
      </motion.div>
      
      <motion.h1 variants={{ hidden: { y: 30, opacity: 0 }, visible: { y: 0, opacity: 1 } }} transition={{ duration: 0.8, ease: momentumEase }} className="display-headline" style={{ fontSize: '112px', marginBottom: '40px' }}>
        Audit your <br />
        <span style={{ fontStyle: 'italic' }}>digital mind.</span>
      </motion.h1>

      <motion.p variants={{ hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } }} transition={{ duration: 0.8, ease: momentumEase }} style={{ color: 'var(--color-storm)', fontFamily: 'var(--font-inter)', fontSize: '20px', lineHeight: '1.75', maxWidth: '640px', margin: '0 auto 54px' }}>
        Incorporate remote development manifests directly into a clean typographic record layout, tracking 
        <span style={{ color: 'var(--color-cobalt-link)', textDecoration: 'underline', margin: '0 6px', cursor: 'pointer' }}>stability patterns</span> 
        and structural asset codebases instantly.
      </motion.p>

      <motion.form 
        variants={{ hidden: { y: 30, opacity: 0 }, visible: { y: 0, opacity: 1 } }}
        transition={{ duration: 0.9, ease: momentumEase }}
        onSubmit={handleSubmit}
        style={{ 
          display: 'flex', 
          gap: '16px', 
          background: 'var(--color-pure-white)', 
          padding: '12px 16px', 
          borderRadius: '120px', 
          border: focused ? '1px solid var(--color-ember-orange)' : '1px solid var(--color-mist)', 
          maxWidth: '700px', 
          margin: '0 auto',
          boxShadow: focused ? '0 12px 30px rgba(255,89,36,0.08)' : 'var(--shadow-sm)',
          transition: 'all 0.5s cubic-bezier(0.19,1,0.22,1)' 
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', flexGrow: 1, paddingLeft: '16px' }}>
          <Globe size={18} style={{ color: focused ? 'var(--color-ember-orange)' : 'var(--color-slate)', marginRight: '16px', transition: 'color 0.2s' }} />
          <input
            type="text"
            placeholder="github.com/owner/repository..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            disabled={isLoading}
            style={{ width: '100%', border: 'none', outline: 'none', fontSize: '18px', background: 'transparent', fontFamily: 'var(--font-inter)', color: 'var(--color-midnight-ink)' }}
          />
        </div>
        <motion.button 
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
          transition={{ duration: 0.4, ease: momentumEase }}
          type="submit" 
          disabled={isLoading} 
          className="btn-ember-outline"
        >
          <span>Analyze Module</span>
          <ArrowRight size={14} />
        </motion.button>
      </motion.form>

      {error && (
        <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} style={{ color: 'var(--color-ember-orange)', fontSize: '15px', marginTop: '24px', fontFamily: 'var(--font-nunito)', fontWeight: 500 }}>
          {error}
        </motion.p>
      )}
    </motion.div>
  );
};