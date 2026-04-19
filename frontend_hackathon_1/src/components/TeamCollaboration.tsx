const teamMembers = [
  {
    name: 'Alexandra Deff',
    task: 'Reviewing Senior Dev Candidates',
    status: 'Completed',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face',
  },
  {
    name: 'Edwin Adenike',
    task: 'Scheduling Final Round Interviews',
    status: 'In Progress',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face',
  },
  {
    name: 'Isaac Oluwatemilorun',
    task: 'Onboarding New Team Members',
    status: 'Pending',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&crop=face',
  },
  {
    name: 'David Oshodi',
    task: 'Updating Job Descriptions',
    status: 'In Progress',
    avatar: 'https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=100&h=100&fit=crop&crop=face',
  },
];

const statusStyles: Record<string, string> = {
  Completed: 'bg-green-100 text-green-700',
  'In Progress': 'bg-blue-100 text-blue-700',
  Pending: 'bg-orange-100 text-orange-700',
};

export function TeamCollaboration() {
  return (
    <div className="bg-card border border-border rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-foreground">Team Collaboration</h3>
        <button className="flex items-center gap-1 text-sm font-medium text-primary hover:text-primary-light transition-colors px-3 py-1.5 border border-border rounded-lg hover:border-primary">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Member
        </button>
      </div>
      <ul className="space-y-3">
        {teamMembers.map((member, index) => (
          <li key={index} className="flex items-center gap-3 p-2 rounded-xl hover:bg-secondary transition-colors">
            <img src={member.avatar} alt={member.name} className="w-10 h-10 rounded-full object-cover" />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-foreground text-sm">{member.name}</p>
              <p className="text-xs text-muted-foreground truncate">Working on: {member.task}</p>
            </div>
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${statusStyles[member.status]}`}>
              {member.status}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
