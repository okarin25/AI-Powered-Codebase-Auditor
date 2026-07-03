const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Explicitly defined and exported FileIssue matching backend schema parameters
export interface FileIssue {
  file: string;
  line: number | null;
  tool: string;     // "radon" | "bandit" | "pylint"
  severity: string; // "low" | "medium" | "high"
  message: string;
}

export interface AuditReport {
  repo_url: string;
  overall_score: number;
  summary: string;
  complexity_hotspots: FileIssue[];
  security_issues: FileIssue[];
  lint_issues: FileIssue[];
  generated_readme: string;
}

export interface AuditResponse {
  job_id: string;
  status: string;
}

export interface StatusResponse {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
  progress: string | null;
  error: string | null;
}

export const startAudit = async (repoUrl: string): Promise<AuditResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/audit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl }),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to initialize system audit pipeline.');
  }
  return response.json();
};

export const getAuditStatus = async (jobId: string): Promise<StatusResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/audit/${jobId}/status`);
  if (!response.ok) throw new Error('Failed to synchronize current background engine state.');
  return response.json();
};

export const getAuditReport = async (jobId: string): Promise<AuditReport> => {
  const response = await fetch(`${API_BASE_URL}/api/audit/${jobId}/report`);
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to extract report schema payload.');
  }
  return response.json();
};

export const getReadmeDownloadUrl = (jobId: string): string => {
  return `${API_BASE_URL}/api/audit/${jobId}/readme`;
};