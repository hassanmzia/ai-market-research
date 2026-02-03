import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ReportRendererProps {
  markdown: string;
  className?: string;
}

const ReportRenderer: React.FC<ReportRendererProps> = ({ markdown, className = '' }) => {
  if (!markdown) {
    return (
      <div className="empty-state">
        <p>No report content available.</p>
      </div>
    );
  }

  return (
    <div className={`report-renderer ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="report-h1">{children}</h1>,
          h2: ({ children }) => <h2 className="report-h2">{children}</h2>,
          h3: ({ children }) => <h3 className="report-h3">{children}</h3>,
          h4: ({ children }) => <h4 className="report-h4">{children}</h4>,
          p: ({ children }) => <p className="report-p">{children}</p>,
          ul: ({ children }) => <ul className="report-ul">{children}</ul>,
          ol: ({ children }) => <ol className="report-ol">{children}</ol>,
          li: ({ children }) => <li className="report-li">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="report-blockquote">{children}</blockquote>
          ),
          code: ({ className: codeClassName, children, ...props }) => {
            const isInline = !codeClassName;
            if (isInline) {
              return <code className="report-inline-code" {...props}>{children}</code>;
            }
            return (
              <pre className="report-code-block">
                <code className={codeClassName} {...props}>
                  {children}
                </code>
              </pre>
            );
          },
          table: ({ children }) => (
            <div className="report-table-wrapper">
              <table className="report-table">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="report-thead">{children}</thead>,
          tbody: ({ children }) => <tbody className="report-tbody">{children}</tbody>,
          tr: ({ children }) => <tr className="report-tr">{children}</tr>,
          th: ({ children }) => <th className="report-th">{children}</th>,
          td: ({ children }) => <td className="report-td">{children}</td>,
          a: ({ href, children }) => (
            <a href={href} className="report-link" target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
          hr: () => <hr className="report-hr" />,
          strong: ({ children }) => <strong className="report-strong">{children}</strong>,
          em: ({ children }) => <em className="report-em">{children}</em>,
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
};

export default ReportRenderer;
