import React from 'react';
import type { Competitor } from '../types';

interface CompetitorTableProps {
  competitors: Competitor[];
  companyName?: string;
}

const CompetitorTable: React.FC<CompetitorTableProps> = ({ competitors, companyName }) => {
  if (!competitors || competitors.length === 0) {
    return (
      <div className="empty-state">
        <p>No competitor data available.</p>
      </div>
    );
  }

  return (
    <div className="competitor-table-wrapper">
      {companyName && <h3 className="competitor-table-title">Competitors of {companyName}</h3>}
      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Sector</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {competitors.map((competitor, index) => (
              <tr key={index}>
                <td>
                  <span className="competitor-name">{competitor.name}</span>
                </td>
                <td>
                  {competitor.sector ? (
                    <span className="sector-badge">{competitor.sector}</span>
                  ) : (
                    <span className="text-muted">N/A</span>
                  )}
                </td>
                <td>
                  <span className="competitor-description">
                    {competitor.description || 'No description available'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CompetitorTable;
