import React from 'react';
import './DestinationCard.css';

const DestinationCard = ({ wikipediaData }) => {
  if (!wikipediaData || !wikipediaData.found) {
    return null;
  }

  const { title, summary, extract, thumbnail, coordinates, url, related_articles } = wikipediaData;

  return (
    <div className="destination-card-wiki">
      <div className="destination-card-header">
        <h2 className="destination-card-title">
          📚 About {title}
        </h2>
        <a 
          href={url} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="wikipedia-link"
        >
          View on Wikipedia →
        </a>
      </div>

      <div className="destination-card-content">
        {thumbnail && (
          <div className="destination-image-container">
            <img 
              src={thumbnail} 
              alt={title} 
              className="destination-image"
            />
          </div>
        )}

        <div className="destination-info-container">
          <div className="destination-summary">
            <h3 className="info-label">Overview</h3>
            <p className="summary-text">{summary}</p>
          </div>

          <div className="destination-extract">
            <p className="extract-text">{extract}</p>
          </div>

          {coordinates && (
            <div className="destination-coordinates">
              <h3 className="info-label">Location</h3>
              <div className="coordinates-box">
                <span className="coordinate-item">
                  📍 {coordinates.lat.toFixed(4)}°N, {coordinates.lon.toFixed(4)}°E
                </span>
              </div>
            </div>
          )}

          {related_articles && related_articles.length > 0 && (
            <div className="related-topics">
              <h3 className="info-label">Related Topics</h3>
              <div className="topics-list">
                {related_articles.slice(0, 5).map((article, index) => (
                  <span key={index} className="topic-tag">
                    {article}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="destination-card-footer">
        <span className="source-badge">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6z"/>
            <path d="M7 4h2v5H7zm0 6h2v2H7z"/>
          </svg>
          Information from Wikipedia
        </span>
      </div>
    </div>
  );
};

export default DestinationCard;
