import React from 'react';
import { motion } from 'framer-motion';
import { Download } from 'lucide-react';
import { getReadmeDownloadUrl } from '../api/client';

interface ReadmePreviewProps {
  readme: string;
  jobId: string;
}

const transitionEase = [0.19, 1, 0.22, 1] as const;

export const ReadmePreview: React.FC<ReadmePreviewProps> = ({ readme, jobId }) => {
  
  const processInlineStrings = (text: string): React.ReactNode[] => {
    let components: React.ReactNode[] = [];
    let boundaryIndex = 0;
    const expressions = /(\*\*.*?\*\*|`.*?`)/g;
    let capture;
    
    while ((capture = expressions.exec(text)) !== null) {
      const matchText = capture[0];
      const foundIndex = capture.index;
      
      if (foundIndex > boundaryIndex) {
        components.push(text.substring(boundaryIndex, foundIndex));
      }
      
      if (matchText.startsWith('**') && matchText.endsWith('**')) {
        components.push(
          <strong key={foundIndex} style={{ fontWeight: 600, color: 'var(--color-midnight-ink)' }}>
            {matchText.substring(2, matchText.length - 2)}
          </strong>
        );
      } else if (matchText.startsWith('`') && matchText.endsWith('`')) {
        components.push(
          <code key={foundIndex} style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', background: 'rgba(0,0,0,0.04)', padding: '2px 6px', borderRadius: '4px', color: 'var(--color-midnight-ink)' }}>
            {matchText.substring(1, matchText.length - 1)}
          </code>
        );
      }
      boundaryIndex = expressions.lastIndex;
    }
    
    if (boundaryIndex < text.length) {
      components.push(text.substring(boundaryIndex));
    }
    return components.length > 0 ? components : [text];
  };

  const compileSyntaxTree = (mdText: string) => {
    const lines = mdText.split('\n');
    const nodes: React.ReactNode[] = [];
    let insideCodeFence = false;
    let codeBlockBuffer: string[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();
      
      if (trimmed.startsWith('```')) {
        if (insideCodeFence) {
          nodes.push(
            <div key={`code-block-${i}`} style={{ position: 'relative', margin: '24px 0' }}>
              <pre style={{ background: 'var(--color-pure-white)', padding: '24px', borderRadius: '12px', border: '1px solid var(--color-mist)', overflowX: 'auto', fontFamily: 'var(--font-mono)', fontSize: '14px', lineHeight: '1.6', color: 'var(--color-deep-slate)' }}>
                <code>{codeBlockBuffer.join('\n')}</code>
              </pre>
            </div>
          );
          codeBlockBuffer = [];
          insideCodeFence = false;
        } else {
          insideCodeFence = true;
        }
        continue;
      }
      
      if (insideCodeFence) {
        codeBlockBuffer.push(line);
        continue;
      }
      
      if (trimmed.startsWith('# ')) {
        nodes.push(<h1 key={i}>{processInlineStrings(trimmed.substring(2))}</h1>);
      } else if (trimmed.startsWith('## ')) {
        nodes.push(<h2 key={i}>{processInlineStrings(trimmed.substring(3))}</h2>);
      } else if (trimmed.startsWith('### ')) {
        nodes.push(<h3 key={i}>{processInlineStrings(trimmed.substring(4))}</h3>);
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        nodes.push(
          <ul key={i} style={{ margin: '0 0 10px 0', paddingLeft: '24px' }}>
            <li style={{ fontSize: '16.5px', color: 'var(--color-storm)' }}>{processInlineStrings(trimmed.substring(2))}</li>
          </ul>
        );
      } else if (/^\d+\.\s/.test(trimmed)) {
        nodes.push(
          <ol key={i} style={{ margin: '0 0 10px 0', paddingLeft: '24px' }}>
            <li style={{ fontSize: '16.5px', color: 'var(--color-storm)' }}>{processInlineStrings(trimmed.replace(/^\d+\.\s/, ''))}</li>
          </ol>
        );
      } else if (trimmed.startsWith('> ')) {
        nodes.push(
          <blockquote key={i} style={{ margin: '24px 0', padding: '16px 24px', borderLeft: '3px solid var(--color-ember-orange)', background: 'rgba(255,89,36,0.02)', fontStyle: 'italic', color: 'var(--color-storm)', borderRadius: '0 8px 8px 0' }}>
            {processInlineStrings(trimmed.substring(2))}
          </blockquote>
        );
      } else if (trimmed === '---') {
        nodes.push(<hr key={i} style={{ border: 'none', height: '1px', background: 'var(--color-mist)', margin: '40px 0' }} />);
      } else if (!trimmed) {
        nodes.push(<div key={i} style={{ height: '14px' }} />);
      } else {
        nodes.push(<p key={i}>{processInlineStrings(line)}</p>);
      }
    }
    return nodes;
  };

  return (
    <motion.div
      initial={{ y: 40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.9, ease: transitionEase }}
      style={{ marginTop: '72px' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '36px' }}>
        <div>
          <div className="micro-eyebrow" style={{ marginBottom: '8px' }}>Project Specification Asset</div>
          <h2 className="display-headline" style={{ fontSize: '54px' }}>Comprehensive Manifest</h2>
        </div>
        <motion.a 
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          href={getReadmeDownloadUrl(jobId)} 
          className="btn-ember-outline" 
          style={{ textDecoration: 'none' }} 
          target="_blank" 
          rel="noreferrer"
        >
          <Download size="{14}"/>
          <span>Save Blueprint</span>
        </motion.a>
      </div>

      <div className="markdown-editorial" style={{ background: 'var(--color-sage-card)', padding: '60px', borderRadius: '16px' }}>
        <div style={{ background: 'var(--color-pure-white)', padding: '60px', borderRadius: '12px', border: '1px solid rgba(0,0,0,0.02)', boxShadow: 'var(--shadow-sm)' }}>
          {compileSyntaxTree(readme)}
        </div>
      </div>
    </motion.div>
  );
};