import React from 'react';
import { TrendingUp, TrendingDown, Star } from 'lucide-react';
import type { TrendData } from '../types';

interface TrendListProps {
  trendData: TrendData;
}

const TrendList: React.FC<TrendListProps> = ({ trendData }) => {
  if (!trendData) {
    return (
      <div className="empty-state">
        <p>No trend data available.</p>
      </div>
    );
  }

  return (
    <div className="trend-list-container">
      <h3>Market Trends</h3>

      {/* Emerging trends */}
      {trendData.emerging_trends && trendData.emerging_trends.length > 0 && (
        <div className="trend-section">
          <h4 className="trend-section-title trend-emerging">
            <TrendingUp size={18} />
            Emerging Trends
          </h4>
          <ul className="trend-items">
            {trendData.emerging_trends.map((trend, index) => (
              <li key={index} className="trend-item trend-item-emerging">
                <TrendingUp size={14} className="trend-item-icon" />
                <span>{trend}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Declining trends */}
      {trendData.declining_trends && trendData.declining_trends.length > 0 && (
        <div className="trend-section">
          <h4 className="trend-section-title trend-declining">
            <TrendingDown size={18} />
            Declining Trends
          </h4>
          <ul className="trend-items">
            {trendData.declining_trends.map((trend, index) => (
              <li key={index} className="trend-item trend-item-declining">
                <TrendingDown size={14} className="trend-item-icon" />
                <span>{trend}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Opportunities */}
      {trendData.opportunities && trendData.opportunities.length > 0 && (
        <div className="trend-section">
          <h4 className="trend-section-title trend-opportunities">
            <Star size={18} />
            Opportunities
          </h4>
          <ul className="trend-items">
            {trendData.opportunities.map((opportunity, index) => (
              <li key={index} className="trend-item trend-item-opportunity">
                <Star size={14} className="trend-item-icon" />
                <span>{opportunity}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default TrendList;
