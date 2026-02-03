import React from 'react';
import type { SentimentData } from '../types';
import { getSentimentColor, getSentimentLabel } from '../utils/helpers';

interface SentimentGaugeProps {
  sentimentData: SentimentData;
}

const SentimentGauge: React.FC<SentimentGaugeProps> = ({ sentimentData }) => {
  if (!sentimentData) {
    return (
      <div className="empty-state">
        <p>No sentiment data available.</p>
      </div>
    );
  }

  const { company_sentiment, competitor_sentiments, market_mood } = sentimentData;
  const score = company_sentiment?.score ?? 0.5;
  const color = getSentimentColor(score);
  const label = company_sentiment?.label || getSentimentLabel(score);

  return (
    <div className="sentiment-gauge-container">
      <h3>Market Sentiment</h3>

      {/* Main company sentiment */}
      <div className="sentiment-main">
        <div className="sentiment-score-display">
          <div
            className="sentiment-circle"
            style={{
              borderColor: color,
              background: `conic-gradient(${color} ${score * 360}deg, #E5E7EB ${score * 360}deg)`,
            }}
          >
            <div className="sentiment-circle-inner">
              <span className="sentiment-score-value">{(score * 100).toFixed(0)}</span>
              <span className="sentiment-score-unit">/100</span>
            </div>
          </div>
          <span className="sentiment-label" style={{ color }}>
            {label}
          </span>
        </div>
        {company_sentiment?.summary && (
          <p className="sentiment-summary">{company_sentiment.summary}</p>
        )}
      </div>

      {/* Market mood */}
      {market_mood && (
        <div className="sentiment-market-mood">
          <span className="mood-label">Market Mood:</span>
          <span className="mood-value">{market_mood}</span>
        </div>
      )}

      {/* Competitor sentiments */}
      {competitor_sentiments && Object.keys(competitor_sentiments).length > 0 && (
        <div className="sentiment-competitors">
          <h4>Competitor Sentiments</h4>
          <div className="sentiment-bars">
            {Object.entries(competitor_sentiments).map(([name, data]) => (
              <div key={name} className="sentiment-bar-item">
                <div className="sentiment-bar-label">
                  <span className="sentiment-bar-name">{name}</span>
                  <span className="sentiment-bar-score" style={{ color: getSentimentColor(data.score) }}>
                    {data.label} ({(data.score * 100).toFixed(0)})
                  </span>
                </div>
                <div className="sentiment-bar-track">
                  <div
                    className="sentiment-bar-fill"
                    style={{
                      width: `${data.score * 100}%`,
                      backgroundColor: getSentimentColor(data.score),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SentimentGauge;
