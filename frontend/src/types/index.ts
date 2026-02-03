export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  company: string;
  role: 'admin' | 'analyst' | 'viewer';
  avatar?: string;
  preferences: Record<string, any>;
}

export interface ResearchProject {
  id: number;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'completed' | 'archived';
  tasks: ResearchTask[];
  created_at: string;
  updated_at: string;
}

export interface ResearchTask {
  id: number;
  project: number;
  company_name: string;
  task_id: string;
  status: 'pending' | 'validation' | 'sector_identification' | 'competitor_discovery' | 'financial_research' | 'deep_research' | 'sentiment_analysis' | 'trend_analysis' | 'report_generation' | 'completed' | 'failed';
  progress: number;
  result?: ResearchResult;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_at: string;
}

export interface ResearchResult {
  id: number;
  company_validated: boolean;
  company_sector: string;
  competitors: Competitor[];
  financial_data: Record<string, any>;
  market_research: Record<string, any>;
  sentiment_data: SentimentData;
  trend_data: TrendData;
  report_markdown: string;
  report_html: string;
  executive_summary: string;
  swot_analysis: SwotAnalysis;
  recommendations: string[];
  created_at: string;
}

export interface Competitor {
  name: string;
  description?: string;
  sector?: string;
}

export interface SentimentData {
  company_sentiment: { score: number; label: string; summary: string };
  competitor_sentiments: Record<string, { score: number; label: string }>;
  market_mood: string;
}

export interface TrendData {
  emerging_trends: string[];
  declining_trends: string[];
  opportunities: string[];
}

export interface SwotAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface Notification {
  id: number;
  type: 'research_complete' | 'watchlist_alert' | 'system';
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface SavedReport {
  id: number;
  title: string;
  description: string;
  report_data: Record<string, any>;
  format: 'markdown' | 'html' | 'pdf';
  is_public: boolean;
  share_token: string;
  download_count: number;
  created_at: string;
}

export interface AgentCard {
  name: string;
  description: string;
  capabilities: string[];
  status: 'active' | 'busy' | 'offline';
}

export interface WatchlistItem {
  id: number;
  company: { id: number; name: string; sector: string };
  alert_on_news: boolean;
  alert_on_competitor_change: boolean;
  notes: string;
  created_at: string;
}

export interface DashboardStats {
  total_researches: number;
  completed_researches: number;
  active_researches: number;
  watchlist_count: number;
  recent_researches: ResearchTask[];
  top_sectors: { sector: string; count: number }[];
  monthly_activity: { month: string; count: number }[];
}

export interface ResearchProgress {
  task_id: string;
  stage: string;
  progress: number;
  message: string;
  agent_name?: string;
}
