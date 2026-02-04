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
    validation: '#8B5CF6',
    sector_identification: '#8B5CF6',
    competitor_discovery: '#8B5CF6',
    financial_research: '#2563EB',
    deep_research: '#2563EB',
    sentiment_analysis: '#2563EB',
    trend_analysis: '#2563EB',
    report_generation: '#F59E0B',
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
    validation: 'Validating',
    sector_identification: 'Analyzing Sector',
    competitor_discovery: 'Finding Competitors',
    financial_research: 'Financial Research',
    deep_research: 'Deep Research',
    sentiment_analysis: 'Sentiment Analysis',
    trend_analysis: 'Trend Analysis',
    report_generation: 'Generating Report',
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
    validation: 10,
    sector_identification: 25,
    competitor_discovery: 40,
    financial_research: 50,
    deep_research: 60,
    sentiment_analysis: 70,
    trend_analysis: 85,
    report_generation: 95,
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
