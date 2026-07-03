import { useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { startAudit, getAuditStatus, getAuditReport, type AuditReport } from './api/client';
import { AuditInput } from './components/AuditInput';
import { LoadingState } from './components/LoadingState';
import { ScoreWidget } from './components/ScoreWidget';
import { IssuesTable } from './components/IssuesTable';
import { ReadmePreview } from './components/ReadmePreview';
import { ArrowLeft, GitBranch } from 'lucide-react';
import './App.css';

function App() {
  const [view, setView] = useState<'input' | 'loading' | 'report'>('input');
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AuditReport | null>(null);
  const [activeUrl, setActiveUrl] = useState<string>('');
  const loopRef = useRef<number | null>(null);

  useEffect(() => {
    return () => { if (loopRef.current) clearInterval(loopRef.current); };
  }, []);

  const handleStartScan = async (url: string) => {
    try {
      setError(null);
      setActiveUrl(url);
      setView('loading');
      setProgress('Connecting to core analysis pipeline channels...');

      const startData = await startAudit(url);
      setJobId(startData.job_id);
      startTrackingLoop(startData.job_id);
    } catch (err: any) {
      setError(err.message || 'System fault encountered during pipeline execution.');
      setView('input');
    }
  };

  const startTrackingLoop = (id: string) => {
    if (loopRef.current) clearInterval(loopRef.current);

    loopRef.current = window.setInterval(async () => {
      try {
        const status = await getAuditStatus(id);
        if (status.progress) setProgress(status.progress);

        if (status.status === 'done') {
          if (loopRef.current) clearInterval(loopRef.current);
          setProgress('Unpacking processed workspace objects...');
          const reportPayload = await getAuditReport(id);
          setReport(reportPayload);
          setView('report');
        } else if (status.status === 'error') {
          if (loopRef.current) clearInterval(loopRef.current);
          setError(status.error || 'The analysis runtime pipeline failed.');
          setView('input');
        }
      } catch {
        if (loopRef.current) clearInterval(loopRef.current);
        setError('Tracking synchronization link severed.');
        setView('input');
      }
    }, 1500);
  };

  const resetEnvironment = () => {
    setView('input');
    setReport(null);
    setJobId(null);
    setProgress(null);
    setError(null);
  };

  return (
    <div className="app-viewport">
      <div className="hero-bloom" />

      <header style={{ height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 50px', zIndex: 10, background: 'transparent' }}>
        <div className="micro-eyebrow" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }} onClick={resetEnvironment}>
          <span style={{ width: '6px', height: '6px', background: 'var(--color-ember-orange)', borderRadius: '50%' }} />
          <span style={{ color: 'var(--color-midnight-ink)' }}>mymind.auditor</span>
        </div>
        {view === 'report' && (
          <button className="btn-ember-outline" style={{ padding: '8px 20px', fontSize: '12px' }} onClick={resetEnvironment}>
            <ArrowLeft size={12} /> New Registry
          </button>
        )}
      </header>

      <main style={{ flexGrow: 1, zIndex: 1, padding: '0 50px 100px' }}>
        <AnimatePresence mode="wait">
          {view === 'input' && (
            <motion.div key="input" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.7, ease: [0.19, 1, 0.22, 1] }}>
              <AuditInput onSubmit={handleStartScan} isLoading={false} />
              {error && (
                <div style={{ maxWidth: '680px', margin: '40px auto 0', background: 'var(--color-blush-tint)', border: '1px solid var(--color-ember-orange)', borderRadius: '12px', padding: '20px', color: '#b71c1c', fontSize: '15px', fontFamily: 'var(--font-inter)', textAlign: 'left' }}>
                  {error}
                </div>
              )}
            </motion.div>
          )}

          {view === 'loading' && (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <LoadingState progress={progress} />
            </motion.div>
          )}

          {view === 'report' && report && jobId && (
            <motion.div key="report" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: [0.19, 1, 0.22, 1] }} style={{ maxWidth: '1000px', margin: '40px auto 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-steel)', fontFamily: 'var(--font-mono)', fontSize: '15px', marginBottom: '40px', justifyContent: 'flex-start' }}>
                <GitBranch size={16} style={{ color: 'var(--color-ember-orange)' }} />
                <span>{activeUrl.replace('https://github.com/', '')}</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}>
                <ScoreWidget score={report.overall_score} />

                <div style={{ background: 'var(--color-parchment-card)', borderRadius: '16px', padding: '50px', textAlign: 'left' }}>
                  <h3 className="display-headline" style={{ fontSize: '42px', marginBottom: '24px' }}>Executive Abstract Overview</h3>
                  <p style={{ fontSize: '17px', lineHeight: '1.75', color: 'var(--color-storm)', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-inter)' }}>{report.summary}</p>
                </div>

                <IssuesTable complexityIssues={report.complexity_hotspots} securityIssues={report.security_issues} lintIssues={report.lint_issues} />
                <ReadmePreview readme={report.generated_readme} jobId={jobId} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;