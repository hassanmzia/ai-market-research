import { format, formatDistanceToNow, parseISO } from 'date-fns';

export function formatDate(dateString: string): string {
  try {
    const date = parseISO(dateString);
    return format(date, 'MMM d, yyyy');
  } catch {
    return dateString;
  }
}

export function formatDateTime(dateString: string): string {
  try {
    const date = parseISO(dateString);
    return format(date, 'MMM d, yyyy h:mm a');
  } catch {
    return dateString;
  }
}

export function formatRelativeTime(dateString: string): string {
  try {
    const date = parseISO(dateString);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return dateString;
  }
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: '#6B7280',
    pending: '#6B7280',
    active: '#2563EB',
    validating: '#8B5CF6',
    analyzing_sector: '#8B5CF6',
    finding_competitors: '#8B5CF6',
    researching: '#2563EB',
    analyzing_sentiment: '#2563EB',
    analyzing_trends: '#2563EB',
    generating_report: '#F59E0B',
    completed: '#10B981',
    failed: '#EF4444',
    archived: '#9CA3AF',
  };
  return colors[status] || '#6B7280';
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: 'Draft',
    pending: 'Pending',
    active: 'Active',
    validating: 'Validating',
    analyzing_sector: 'Analyzing Sector',
    finding_competitors: 'Finding Competitors',
    researching: 'Researching',
    analyzing_sentiment: 'Sentiment Analysis',
    analyzing_trends: 'Trend Analysis',
    generating_report: 'Generating Report',
    completed: 'Completed',
    failed: 'Failed',
    archived: 'Archived',
  };
  return labels[status] || status;
}

export function calculateProgress(status: string, progress?: number): number {
  if (progress !== undefined && progress > 0) return progress;

  const progressMap: Record<string, number> = {
    pending: 0,
    validating: 10,
    analyzing_sector: 20,
    finding_competitors: 35,
    researching: 50,
    analyzing_sentiment: 65,
    analyzing_trends: 78,
    generating_report: 90,
    completed: 100,
    failed: 0,
  };
  return progressMap[status] || 0;
}

export function getSentimentColor(score: number): string {
  if (score >= 0.6) return '#10B981';
  if (score >= 0.3) return '#F59E0B';
  return '#EF4444';
}

export function getSentimentLabel(score: number): string {
  if (score >= 0.6) return 'Positive';
  if (score >= 0.3) return 'Neutral';
  return 'Negative';
}

export function generateShareUrl(token: string): string {
  return `${window.location.origin}/shared/report/${token}`;
}

export function downloadBlob(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
