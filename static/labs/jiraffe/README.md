# 🦒 Jiraffe - Project Management Made Simple

Jiraffe is a lightweight, browser-based project management tool designed for engineering teams who want to track projects, tasks, interactions, and architectural decisions without the complexity of enterprise tools.

## Features

- **📊 Project Management**: Organize work by teams and projects with priority levels
- **✅ Task Tracking**: Create and track tasks with due dates and status updates
- **💬 Interaction Logging**: Record meetings, chats, and emails with team members
- **📋 ADR Management**: Track Architecture Decision Records through their lifecycle
- **👥 People Management**: Maintain contact information and interaction history
- **🔍 Search**: Full-text search across all projects, tasks, and interactions
- **📤 Export/Import**: Export data as Markdown or HTML reports
- **🌙 Dark Mode**: Toggle between light and dark themes
- **💾 Local Storage**: All data is stored locally in your browser

## Getting Started

1. **Open Jiraffe**: Navigate to `jiraffe.html` in your web browser
2. **Create a Team**: Click "New Team" and add team members
3. **Add a Project**: Create projects within teams with priorities and status
4. **Track Tasks**: Add tasks to projects with due dates
5. **Log Interactions**: Record meetings and communications
6. **Monitor Progress**: Use the dashboard to see what needs attention

## Navigation

### 📈 Dashboard
Your central hub showing:
- Current tasks sorted by urgency
- ADRs waiting for your action
- Upcoming meetings
- High-priority projects
- Weekly activity chart
- Teams needing attention

### 📊 Projects
Organized by teams, showing:
- Project details and progress notes
- Associated tasks, interactions, and ADRs
- Priority and status indicators
- Action buttons for editing and management

### ✅ Tasks
All tasks across projects with:
- Deadline highlighting (overdue, due today, etc.)
- Project and team context
- Work session tracking
- Filtering and sorting options

### 👥 People
Contact management featuring:
- VIP marking for important contacts
- Interaction history
- Team membership tracking
- Last contact warnings

### 💬 1-1s
Dedicated space for one-on-one meetings:
- Separate from project work
- Meeting notes and follow-ups
- Export capabilities

### 📋 ADRs
Architecture Decision Record tracking:
- Status workflow (not started → waiting → approved/rejected)
- Due date tracking
- Author assignment

### 🔍 Search
Full-text search across:
- Project names and descriptions
- Task titles and descriptions
- Interaction notes
- People names and notes
- Tags

## Data Management

### Priorities
Projects use four priority levels:
- **Critical**: Urgent, blocking work
- **Urgent**: Important, time-sensitive
- **Important**: Significant but not blocking
- **Enhancement**: Nice-to-have improvements

### Status Values
- **Projects**: not-started, ongoing, complete, on-hold
- **Tasks**: not-started, ongoing, complete
- **ADRs**: not-started, waiting-for-me, waiting-for-others, approved, rejected, on-hold

### Interaction Types
- **Meeting**: Face-to-face or video calls
- **Chat**: Slack, Teams, or informal conversations
- **Email**: Written communications

## Export and Import

### Export Options
- **Markdown Export**: Human-readable format for documentation
- **HTML Export**: Formatted reports for sharing
- **Meeting Notes**: Individual interaction exports

### Import (Planned)
Future versions will support importing Markdown files. See `file-format.md` for the expected format specification.

## Tips and Best Practices

### Team Organization
- Create teams that match your organizational structure
- Add all team members to track interaction history
- Use team tags to categorize by technology or domain

### Project Management
- Set realistic priorities - not everything can be critical
- Use progress notes to provide context for stakeholders
- Tag projects with relevant technologies or themes

### Task Tracking
- Break large work into smaller, manageable tasks
- Set realistic due dates and update them when needed
- Use work sessions to track time spent

### Interaction Logging
- Log important decisions and outcomes
- Include artifact URLs for meeting notes or documents
- Use tags to categorize by topic or urgency

### ADR Workflow
1. Create ADR in "not-started" status
2. Move to "waiting-for-me" when you need to work on it
3. Move to "waiting-for-others" when blocked on external input
4. Complete with "approved" or "rejected" status

### Dashboard Usage
- Check daily for overdue tasks and urgent items
- Monitor teams needing attention (>30 days since last interaction)
- Use the activity chart to track your work patterns

## Data Storage

Jiraffe stores all data locally in your browser using localStorage. This means:

- **Privacy**: Your data never leaves your computer
- **Performance**: Fast loading and searching
- **Offline**: Works without internet connection
- **Backup**: Export regularly to avoid data loss

### Data Safety
- Export your data regularly as backup
- Browser data can be cleared by accident or browser updates
- Consider syncing exports to cloud storage

## Browser Compatibility

Jiraffe works in all modern browsers:
- Chrome/Chromium
- Firefox
- Safari
- Edge

## Keyboard Shortcuts

- **Escape**: Close any open modal
- **Tab**: Navigate through form fields
- **Enter**: Submit forms (when focused on submit button)

## Troubleshooting

### Data Not Loading
- Check browser console for errors
- Try refreshing the page
- Clear browser cache if needed

### Export Not Working
- Ensure pop-ups are allowed for the site
- Check download folder for exported files
- Try a different browser if issues persist

### Performance Issues
- Large datasets may slow down the interface
- Consider archiving old projects
- Export and clear old data periodically

## File Structure

```
jiraffe/
├── jiraffe.html          # Main application file
├── README.md             # This file
└── file-format.md        # Markdown import/export format specification
```

## Development

Jiraffe is built with:
- **Vue.js 3**: Reactive frontend framework
- **Vanilla CSS**: Custom styling with CSS variables
- **LocalStorage API**: Browser-native data persistence

The application is entirely client-side with no server dependencies.

## Version History

- **v1.0**: Initial release with core project management features
- Current development focuses on import functionality and mobile responsiveness

## Support

For issues or feature requests:
1. Check existing functionality in the documentation
2. Export your data before trying fixes
3. Try clearing browser cache for persistent issues

## License

Jiraffe is open source software. See the source code for implementation details and feel free to modify for your needs.
