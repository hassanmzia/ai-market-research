import React from 'react';
import type { SwotAnalysis } from '../types';

interface SwotChartProps {
  swot: SwotAnalysis;
}

const SwotChart: React.FC<SwotChartProps> = ({ swot }) => {
  if (!swot) {
    return (
      <div className="empty-state">
        <p>No SWOT analysis data available.</p>
      </div>
    );
  }

  return (
    <div className="swot-chart">
      <h3 className="swot-title">SWOT Analysis</h3>
      <div className="swot-grid">
        <div className="swot-quadrant swot-strengths">
          <div className="swot-quadrant-header">
            <span className="swot-icon">S</span>
            <h4>Strengths</h4>
          </div>
          <ul>
            {swot.strengths?.map((item, i) => (
              <li key={i}>{item}</li>
            )) || <li>No data</li>}
          </ul>
        </div>

        <div className="swot-quadrant swot-weaknesses">
          <div className="swot-quadrant-header">
            <span className="swot-icon">W</span>
            <h4>Weaknesses</h4>
          </div>
          <ul>
            {swot.weaknesses?.map((item, i) => (
              <li key={i}>{item}</li>
            )) || <li>No data</li>}
          </ul>
        </div>

        <div className="swot-quadrant swot-opportunities">
          <div className="swot-quadrant-header">
            <span className="swot-icon">O</span>
            <h4>Opportunities</h4>
          </div>
          <ul>
            {swot.opportunities?.map((item, i) => (
              <li key={i}>{item}</li>
            )) || <li>No data</li>}
          </ul>
        </div>

        <div className="swot-quadrant swot-threats">
          <div className="swot-quadrant-header">
            <span className="swot-icon">T</span>
            <h4>Threats</h4>
          </div>
          <ul>
            {swot.threats?.map((item, i) => (
              <li key={i}>{item}</li>
            )) || <li>No data</li>}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default SwotChart;
