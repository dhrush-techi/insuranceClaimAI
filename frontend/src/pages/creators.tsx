import React from 'react';

const Creators: React.FC = () => {
  const teamMembers = [
    {
      name: 'Anil. A',
      role: 'Lead Developer, AI Specialist, Backend Developer & Database Specialist',
      department: 'Artificial Intelligence & Machine Learning',
      year: '3rd Year',
      description: 'Full-stack development, AI/ML integration, system architecture, Server-side logic, database management, and API development.',
      skills: ['React', 'TypeScript', 'Python', 'TensorFlow', 'Node.js', 'PostgreSQL', 'MongoDB', 'REST APIs', 'Authentication'],
      imageColor: 'from-blue-500 to-purple-600'
    },
    {
      name: 'A B Rohith Manikanta',
      role: 'UI/UX Designer & Frontend Developer',
      department: 'Artificial Intelligence & Machine Learning',
      year: '3rd Year',
      description: 'User interface design, user experience optimization, and frontend development.',
      skills: ['Figma', 'CSS/SCSS', 'React', 'UI/UX Design', 'Prototyping'],
      imageColor: 'from-pink-500 to-red-600'
    }
  ];

  return (
    <div className="creators-page">
      <div className="app-shell">
        {/* Hero Section */}
        <div className="card mb-8">
          <div className="text-center">
            <h1 className="nav-title-main mb-4">
              Meet the Creators
            </h1>
            <p className="text-text-muted text-lg mb-6 max-w-2xl mx-auto">
              A team of passionate AI/ML engineering students from New Horizon College of Engineering, 
              Bengaluru, dedicated to building intelligent solutions for the future.
            </p>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-google-blue-light border border-google-blue/30">
              <span className="text-google-blue text-sm font-medium">Department of Artificial Intelligence & Machine Learning</span>
            </div>
          </div>
        </div>

        {/* College Info */}
        <div className="card-muted mb-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex-1">
              <h2 className="text-xl font-semibold mb-2 mono-gradient">
                New Horizon College of Engineering
              </h2>
              <p className="text-text-muted mb-2">📍 Bengaluru, Karnataka</p>
              <p className="text-text-faint text-sm">
                A premier institution nurturing innovation and excellence in engineering education, 
                with state-of-the-art facilities for AI/ML research and development.
              </p>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-500 to-green-500 flex items-center justify-center mb-2">
                <span className="text-white font-bold text-xl">NH</span>
              </div>
              <span className="text-text-muted text-sm">Established 2001</span>
            </div>
          </div>
        </div>

        {/* Team Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6 mono-gradient-subtle">Our Team</h2>
          <div className="dashboard-grid">
            {teamMembers.map((member, index) => (
              <div key={index} className="card group">
                <div className="flex items-start gap-4 mb-4">
                  <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${member.imageColor} flex items-center justify-center flex-shrink-0`}>
                    <span className="text-white font-bold text-lg">
                      {member.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold mb-1">{member.name}</h3>
                    <p className="text-google-blue text-sm font-medium mb-1">{member.role}</p>
                    <p className="text-text-faint text-xs">{member.department} • {member.year}</p>
                  </div>
                </div>
                <p className="text-text-muted text-sm mb-4">{member.description}</p>
                
                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-text-muted mb-2">Skills & Expertise</h4>
                    <div className="flex flex-wrap gap-2">
                      {member.skills.map((skill, skillIndex) => (
                        <span 
                          key={skillIndex}
                          className="pill-label text-xs"
                          style={{
                            background: 'rgba(66, 133, 244, 0.1)',
                            borderColor: 'rgba(66, 133, 244, 0.3)',
                            color: 'var(--google-blue)'
                          }}
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Project Info */}
        <div className="card-muted">
          <h2 className="text-lg font-semibold mb-4 mono-gradient-subtle">About Lighthouse AI</h2>
          <div className="space-y-4">
            <p className="text-text-muted">
              Lighthouse AI is an advanced evaluation platform developed as part of our academic project, 
              combining cutting-edge AI technologies with intuitive user interfaces to revolutionize 
              the way evaluations and assessments are conducted.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-google-blue-light flex items-center justify-center">
                  <svg className="w-5 h-5 text-google-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-medium text-sm">AI-Powered</h4>
                  <p className="text-text-faint text-xs">Advanced ML algorithms</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-google-green-light flex items-center justify-center">
                  <svg className="w-5 h-5 text-google-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-medium text-sm">Secure</h4>
                  <p className="text-text-faint text-xs">Protected assessments</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-google-yellow-light flex items-center justify-center">
                  <svg className="w-5 h-5 text-google-yellow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-medium text-sm">Fast</h4>
                  <p className="text-text-faint text-xs">Real-time processing</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-text-faint text-sm">
            © {new Date().getFullYear()} Lighthouse AI • Developed at New Horizon College of Engineering, Bengaluru
          </p>
          <p className="text-text-faint text-xs mt-2">
            Department of Artificial Intelligence & Machine Learning • 3rd Year Engineering Project
          </p>
        </div>
      </div>
      
      {/* Inline Styles */}
      <style>{`
        .creators-page {
          min-height: 100vh;
          background: var(--bg-main);
        }
        
        .text-google-blue {
          color: var(--google-blue);
        }
        
        .bg-google-blue-light {
          background-color: var(--google-blue-light);
        }
        
        .border-google-blue\/30 {
          border-color: rgba(66, 133, 244, 0.3);
        }
        
        .from-blue-500 {
          --tw-gradient-from: #3b82f6;
          --tw-gradient-to: rgba(59, 130, 246, 0);
          --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to);
        }
        
        .to-purple-600 {
          --tw-gradient-to: #7c3aed;
        }
        
        .from-pink-500 {
          --tw-gradient-from: #ec4899;
          --tw-gradient-to: rgba(236, 72, 153, 0);
          --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to);
        }
        
        .to-red-600 {
          --tw-gradient-to: #dc2626;
        }
        
        .from-green-500 {
          --tw-gradient-from: #10b981;
          --tw-gradient-to: rgba(16, 185, 129, 0);
          --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to);
        }
        
        .to-teal-600 {
          --tw-gradient-to: #0d9488;
        }
        
        .from-yellow-500 {
          --tw-gradient-from: #f59e0b;
          --tw-gradient-to: rgba(245, 158, 11, 0);
          --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to);
        }
        
        .to-orange-600 {
          --tw-gradient-to: #ea580c;
        }
        
        .bg-google-green-light {
          background-color: var(--google-green-light);
        }
        
        .text-google-green {
          color: var(--google-green);
        }
        
        .bg-google-yellow-light {
          background-color: var(--google-yellow-light);
        }
        
        .text-google-yellow {
          color: var(--google-yellow);
        }
        
        .mb-8 {
          margin-bottom: 2rem;
        }
        
        .mb-6 {
          margin-bottom: 1.5rem;
        }
        
        .mb-4 {
          margin-bottom: 1rem;
        }
        
        .mb-2 {
          margin-bottom: 0.5rem;
        }
        
        .mb-1 {
          margin-bottom: 0.25rem;
        }
        
        .mt-8 {
          margin-top: 2rem;
        }
        
        .mt-2 {
          margin-top: 0.5rem;
        }
        
        .mx-auto {
          margin-left: auto;
          margin-right: auto;
        }
        
        .text-center {
          text-align: center;
        }
        
        .text-lg {
          font-size: 1.125rem;
          line-height: 1.75rem;
        }
        
        .text-xl {
          font-size: 1.25rem;
          line-height: 1.75rem;
        }
        
        .text-xs {
          font-size: 0.75rem;
          line-height: 1rem;
        }
        
        .text-sm {
          font-size: 0.875rem;
          line-height: 1.25rem;
        }
        
        .font-semibold {
          font-weight: 600;
        }
        
        .font-medium {
          font-weight: 500;
        }
        
        .font-bold {
          font-weight: 700;
        }
        
        .max-w-2xl {
          max-width: 42rem;
        }
        
        .inline-flex {
          display: inline-flex;
        }
        
        .flex {
          display: flex;
        }
        
        .flex-col {
          flex-direction: column;
        }
        
        .flex-row {
          flex-direction: row;
        }
        
        .items-center {
          align-items: center;
        }
        
        .items-start {
          align-items: flex-start;
        }
        
        .justify-center {
          justify-content: center;
        }
        
        .justify-between {
          justify-content: space-between;
        }
        
        .gap-2 {
          gap: 0.5rem;
        }
        
        .gap-3 {
          gap: 0.75rem;
        }
        
        .gap-4 {
          gap: 1rem;
        }
        
        .gap-6 {
          gap: 1.5rem;
        }
        
        .flex-wrap {
          flex-wrap: wrap;
        }
        
        .flex-shrink-0 {
          flex-shrink: 0;
        }
        
        .flex-1 {
          flex: 1 1 0%;
        }
        
        .space-y-3 > * + * {
          margin-top: 0.75rem;
        }
        
        .space-y-4 > * + * {
          margin-top: 1rem;
        }
        
        .group:hover .card {
          transform: translateY(-4px);
        }
        
        .rounded-full {
          border-radius: 9999px;
        }
        
        .rounded-xl {
          border-radius: 0.75rem;
        }
        
        .rounded-lg {
          border-radius: 0.5rem;
        }
        
        .px-4 {
          padding-left: 1rem;
          padding-right: 1rem;
        }
        
        .py-2 {
          padding-top: 0.5rem;
          padding-bottom: 0.5rem;
        }
        
        .bg-gradient-to-br {
          background-image: linear-gradient(to bottom right, var(--tw-gradient-stops));
        }
        
        .w-16 {
          width: 4rem;
        }
        
        .h-16 {
          height: 4rem;
        }
        
        .w-10 {
          width: 2.5rem;
        }
        
        .h-10 {
          height: 2.5rem;
        }
        
        .w-5 {
          width: 1.25rem;
        }
        
        .h-5 {
          height: 1.25rem;
        }
        
        @media (min-width: 768px) {
          .md\\:flex-row {
            flex-direction: row;
          }
          
          .md\\:grid-cols-3 {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
        }
      `}</style>
    </div>
  );
};

export default Creators;