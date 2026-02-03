import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Loader, CheckCircle, ArrowRight, Building } from 'lucide-react';
import { useResearchStore } from '../store/researchStore';
import ResearchProgressComponent from '../components/ResearchProgress';
import toast from 'react-hot-toast';

const NewResearch: React.FC = () => {
  const [companyName, setCompanyName] = useState('');
  const [projectName, setProjectName] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isStarted, setIsStarted] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const { startResearch, createProject, loading } = useResearchStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!companyName.trim()) {
      toast.error('Please enter a company name');
      return;
    }

    try {
      let projectId: number | undefined;

      if (projectName.trim()) {
        const project = await createProject({ name: projectName.trim() });
        projectId = project.id;
      }

      const result = await startResearch(companyName.trim(), projectId);
      setTaskId(result.task_id);
      setIsStarted(true);
      toast.success(`Research started for ${companyName}`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to start research');
    }
  };

  const handleComplete = () => {
    setIsComplete(true);
    toast.success('Research completed successfully!');
  };

  if (isComplete && taskId) {
    return (
      <div className="new-research-page">
        <div className="research-complete-card">
          <div className="research-complete-icon">
            <CheckCircle size={64} />
          </div>
          <h2>Research Complete!</h2>
          <p>
            The market research for <strong>{companyName}</strong> has been completed
            successfully.
          </p>
          <div className="research-complete-actions">
            <Link to={`/research/${taskId}`} className="btn btn-primary btn-lg">
              View Results <ArrowRight size={18} />
            </Link>
            <button
              className="btn btn-outline btn-lg"
              onClick={() => {
                setCompanyName('');
                setProjectName('');
                setTaskId(null);
                setIsStarted(false);
                setIsComplete(false);
              }}
            >
              Start Another Research
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isStarted && taskId) {
    return (
      <div className="new-research-page">
        <div className="page-header">
          <div>
            <h1>Researching: {companyName}</h1>
            <p className="page-subtitle">Our AI agents are working on your research</p>
          </div>
        </div>
        <ResearchProgressComponent taskId={taskId} onComplete={handleComplete} />
      </div>
    );
  }

  return (
    <div className="new-research-page">
      <div className="page-header">
        <div>
          <h1>New Research</h1>
          <p className="page-subtitle">
            Enter a company name to start comprehensive market research
          </p>
        </div>
      </div>

      <div className="research-form-card">
        <form onSubmit={handleSubmit} className="research-form">
          <div className="research-input-group">
            <div className="research-input-wrapper">
              <Building size={24} className="research-input-icon" />
              <input
                type="text"
                className="research-input"
                placeholder="Enter company name (e.g., Tesla, Apple, Microsoft)"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                autoFocus
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="project-name">Project Name (optional)</label>
            <input
              id="project-name"
              type="text"
              className="form-input"
              placeholder="Group this research into a project"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="research-info">
            <h4>What our AI agents will do:</h4>
            <ul>
              <li>Validate the company and identify its sector</li>
              <li>Discover and analyze key competitors</li>
              <li>Gather financial data and market metrics</li>
              <li>Perform sentiment analysis from news and social media</li>
              <li>Identify emerging trends and market opportunities</li>
              <li>Generate a comprehensive SWOT analysis</li>
              <li>Compile a detailed market research report</li>
            </ul>
          </div>

          <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={loading}>
            {loading ? (
              <>
                <Loader size={20} className="spinning" />
                Starting Research...
              </>
            ) : (
              <>
                <Search size={20} />
                Start Research
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default NewResearch;
