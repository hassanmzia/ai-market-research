import React from 'react';
import { TrendingUp, TrendingDown, Minus, LucideIcon } from 'lucide-react';

interface StatsCardProps {
  icon: LucideIcon;
  label: string;
  value: number | string;
  trend?: {
    value: number;
    label: string;
  };
  color?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ icon: Icon, label, value, trend, color = '#2563EB' }) => {
  const getTrendIcon = () => {
    if (!trend) return null;
    if (trend.value > 0) return <TrendingUp size={14} />;
    if (trend.value < 0) return <TrendingDown size={14} />;
    return <Minus size={14} />;
  };

  const getTrendClass = () => {
    if (!trend) return '';
    if (trend.value > 0) return 'trend-up';
    if (trend.value < 0) return 'trend-down';
    return 'trend-neutral';
  };

  return (
    <div className="stats-card">
      <div className="stats-card-icon" style={{ backgroundColor: `${color}15`, color }}>
        <Icon size={24} />
      </div>
      <div className="stats-card-content">
        <span className="stats-card-label">{label}</span>
        <span className="stats-card-value">{value}</span>
        {trend && (
          <div className={`stats-card-trend ${getTrendClass()}`}>
            {getTrendIcon()}
            <span>{Math.abs(trend.value)}% {trend.label}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatsCard;
