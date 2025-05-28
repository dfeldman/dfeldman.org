# Jiraffe Architecture Documentation

## Overview

Jiraffe is a single-page application (SPA) built as a client-side-only project management tool. It uses modern web technologies to provide a responsive, fast, and privacy-focused experience without requiring any server infrastructure.

## Design Principles

### 1. Privacy First
- All data remains on the user's device
- No external API calls or data transmission
- No tracking or analytics

### 2. Zero Server Dependencies
- Pure client-side implementation
- No backend services required
- Can be hosted as static files

### 3. Progressive Enhancement
- Works without JavaScript (basic HTML structure)
- Enhanced experience with JavaScript enabled
- Graceful degradation for older browsers

### 4. Data Portability
- Standard Markdown export format
- Human-readable data structures
- Easy migration between instances

## Technology Stack

### Frontend Framework
- **Vue.js 3 (Options API)**: Reactive UI framework
  - CDN-based inclusion for simplicity
  - No build process required
  - Options API for easier maintenance

### Styling
- **Custom CSS with CSS Variables**: Theme-aware styling
  - Dark/light mode support
  - Responsive design
  - No CSS framework dependencies

### Data Persistence
- **localStorage API**: Browser-native storage
  - JSON serialization
  - Automatic persistence
  - No external database

### Build Process
- **None**: Direct browser execution
  - No compilation step
  - No bundling required
  - Immediate development feedback

## Application Architecture

### Component Structure

```
App (Root Vue Instance)
├── Navigation Sidebar
├── Main Content Area
│   ├── Dashboard View
│   ├── Projects View
│   ├── Tasks View
│   ├── People View
│   ├── 1-1s View
│   ├── ADRs View
│   └── Search View
├── Modal System
│   ├── Team Form
│   ├── Project Form
│   ├── Task Form
│   ├── Interaction Form
│   ├── ADR Form
│   ├── Person Form
│   └── Work Session Form
└── Import/Export Modals
```

### Data Model

#### Core Entities

```javascript
// Base Item Structure
{
    id: String,           // Unique identifier
    type: String,         // Entity type
    createdDate: String,  // ISO timestamp
    // ... type-specific fields
}

// Team
{
    id: String,
    type: 'team',
    name: String,
    people: String[],     // Array of person names
    tags: String[]        // Array of tag strings
}

// Project
{
    id: String,
    type: 'project',
    name: String,
    teamId: String,       // Reference to team
    priority: String,     // critical|urgent|important|enhancement
    status: String,       // not-started|ongoing|complete|on-hold
    startDate: String,    // ISO date
    endDate?: String,     // ISO date (optional)
    progress?: String,    // Free-form text
    tags: String[]
}

// Task
{
    id: String,
    type: 'task',
    title: String,
    description?: String,
    projectId: String,    // Reference to project
    dueDate: String,      // ISO date
    status: String,       // not-started|ongoing|complete
    artifactUrl?: String,
    tags: String[]
}

// Interaction
{
    id: String,
    type: 'interaction',
    title: String,
    interactionType: String, // meeting|chat|email
    projectId: String,       // Reference to project
    date: String,           // ISO date
    duration: Number,       // Minutes
    people: String[],       // Array of person names
    notes?: String,
    artifactUrl?: String,
    tags: String[]
}

// ADR (Architecture Decision Record)
{
    id: String,
    type: 'adr',
    title: String,
    description?: String,
    projectId: String,     // Reference to project
    adrStatus: String,     // not-started|waiting-for-me|waiting-for-others|approved|rejected|on-hold
    dueDate: String,       // ISO date
    authors: String[],     // Array of author names
    artifactUrl?: String,
    tags: String[]
}

// Person
{
    id: String,
    type: 'person',
    name: String,
    isVIP: Boolean,
    notes?: String,
    tags: String[]
}

// Work Session
{
    id: String,
    type: 'workSession',
    taskId: String,        // Reference to task
    date: String,          // ISO date
    duration: Number       // Minutes
}
```

### State Management

#### Reactive Data Store
```javascript
data() {
    return {
        // Core data - array of all entities
        items: [],
        
        // UI state
        currentView: 'dashboard',
        showModal: false,
        modalTitle: '',
        currentForm: {},
        
        // Filters and preferences
        showCompletedProjects: false,
        showOnHoldProjects: false,
        showCompletedTasks: false,
        showCompletedADRs: false,
        showVIPOnly: false,
        
        // Sorting preferences
        taskSortBy: 'dueDate',
        adrSortBy: 'createdDate',
        personSortBy: 'name',
        
        // Search
        searchQuery: '',
        
        // Special entities
        oneOnOneTeamId: null,
        oneOnOneProjectId: null,
        
        // UI preferences
        darkMode: false,
        
        // Navigation state
        highlightedProjectId: null
    }
}
```

#### Computed Properties
- **Filtered Collections**: teams, projects, tasks, adrs, people
- **Sorted Collections**: sortedTasks, sortedADRs, filteredPeople
- **Dashboard Data**: myCurrentTasks, myWaitingADRs, upcomingMeetings
- **Analytics**: weeklyActivityData, teamsNeedingAttention

### Event Flow

#### Data Modification Flow
1. User interacts with UI (button click, form submission)
2. Event handler called
3. Form data validated
4. Items array updated
5. Vue reactivity triggers UI updates
6. Data persisted to localStorage

#### Navigation Flow
1. User clicks dashboard item
2. navigateToProject() method called
3. currentView changed to 'projects'
4. highlightedProjectId set for visual feedback
5. Smooth scroll to target project
6. Highlight removed after 3 seconds

#### Search Flow
1. User types in search box
2. searchQuery updated reactively
3. searchResults computed property recalculates
4. Filtered results displayed instantly

### File Structure

```
jiraffe/
├── jiraffe.html              # Main application file (single file architecture)
│   ├── <head>
│   │   ├── Vue.js CDN
│   │   └── Embedded CSS (~1000 lines)
│   ├── <body>
│   │   ├── Vue App Template (~800 lines)
│   │   └── Embedded JavaScript (~1500 lines)
├── README.md                 # Usage documentation
├── file-format.md           # Import/export format specification
└── architecture.md          # This file
```

## Data Flow Patterns

### CRUD Operations

#### Create
```javascript
// Add new item
const newItem = {
    id: generateId(),
    type: formType,
    ...formData,
    createdDate: new Date().toISOString()
};
this.items.push(newItem);
this.saveToLocalStorage();
```

#### Read
```javascript
// Get items by type
const projects = this.items.filter(item => item.type === 'project');

// Get related items
const projectTasks = this.items.filter(item => 
    item.type === 'task' && item.projectId === projectId
);
```

#### Update
```javascript
// Update existing item
const index = this.items.findIndex(item => item.id === formId);
if (index !== -1) {
    this.items[index] = { ...formData };
    this.saveToLocalStorage();
}
```

#### Delete
```javascript
// Remove item
this.items = this.items.filter(item => item.id !== itemId);
this.saveToLocalStorage();
```

### Relationship Management

#### One-to-Many Relationships
- Team → Projects
- Project → Tasks
- Project → Interactions
- Project → ADRs
- Task → Work Sessions

#### Many-to-Many Relationships
- People ↔ Teams (via people array)
- People ↔ Interactions (via people array)

### Data Validation

#### Client-Side Validation
- Required field checking
- Date format validation
- Enum value validation (status, priority)
- Unique constraint checking (team names)

#### Data Integrity
- Orphan prevention (no tasks without projects)
- Reference validation (project exists for tasks)
- Type safety (consistent data types)

## User Interface Architecture

### View System
- Single-page application with view switching
- No routing library - simple view state management
- Conditional rendering based on currentView

### Modal System
- Centralized modal for all forms
- Dynamic form rendering based on entity type
- Form validation and submission handling

### Responsive Design
- CSS Grid and Flexbox layouts
- Mobile-first approach
- Progressive enhancement for larger screens

### Theme System
- CSS variables for consistent theming
- Dark/light mode toggle
- Persistent theme preference in localStorage

## Performance Considerations

### Memory Management
- Single items array for all data
- Computed properties for filtering
- Minimal DOM manipulation through Vue

### Storage Optimization
- JSON serialization for localStorage
- Compression through data structure efficiency
- Periodic cleanup of orphaned records

### UI Responsiveness
- Debounced search input
- Efficient computed property caching
- Smooth animations with CSS transitions

### Large Dataset Handling
- Currently no pagination (future enhancement needed)
- Filter-based performance optimization
- Potential virtual scrolling for very large datasets

## Security Model

### Data Privacy
- No external network requests (except Vue.js CDN)
- No cookies or tracking
- Local storage only

### XSS Prevention
- Vue.js automatic escaping
- No innerHTML usage
- Sanitized user input display

### Data Integrity
- Input validation
- Type checking
- Schema enforcement through form validation

## Extensibility Points

### Adding New Entity Types
1. Define data structure in data model
2. Add to form system (modal template)
3. Create computed filters and getters
4. Add to export/import logic
5. Update UI views and navigation

### Adding New Views
1. Add navigation item to sidebar
2. Create view template section
3. Add view logic to currentView conditional
4. Implement view-specific computed properties
5. Add any required filters or sorting

### Adding New Export Formats
1. Create export method in methods section
2. Add UI button to sidebar
3. Implement format-specific logic
4. Update file-format.md documentation

### Customizing UI Themes
1. Modify CSS variables in :root and body.dark-mode
2. Update theme toggle logic if needed
3. Add new theme variants in localStorage handling

## Browser Compatibility

### Supported Features
- localStorage API (IE8+)
- ES6 features via Vue.js compatibility
- CSS Grid and Flexbox (IE11+)
- Modern JavaScript (ES2017+)

### Fallback Strategies
- Progressive enhancement for CSS features
- Graceful degradation for unsupported browsers
- Feature detection for advanced APIs

### Testing Matrix
- Chrome/Chromium (primary)
- Firefox (secondary)
- Safari (secondary)
- Edge (tertiary)

## Deployment Architecture

### Static Hosting Requirements
- Any web server capable of serving HTML files
- HTTPS recommended for localStorage security
- No server-side processing required

### CDN Considerations
- Vue.js loaded from unpkg CDN
- Single point of failure consideration
- Offline fallback not implemented

### Local Development
- Open jiraffe.html directly in browser
- No build process required
- File:// protocol works for development

### Distribution Strategies
- Single HTML file for easy sharing
- Self-contained except for Vue.js CDN
- Version control friendly (single file)

## Error Handling Strategy

### Data Corruption Protection
```javascript
// Array validation before operations
if (!Array.isArray(this.items)) {
    console.error('Data corruption detected');
    this.initializeDefaultData();
}
```

### Storage Quota Handling
```javascript
try {
    localStorage.setItem('jiraffe-data', JSON.stringify(this.items));
} catch (e) {
    if (e.name === 'QuotaExceededError') {
        alert('Storage quota exceeded. Please export and clean old data.');
    }
}
```

### Form Validation
- Required field validation
- Date format validation
- Type checking for numeric fields
- Graceful handling of invalid inputs

## Future Architecture Considerations

### Scalability Improvements
- Virtual scrolling for large lists
- Data pagination
- Background processing with Web Workers
- IndexedDB migration for larger datasets

### Collaboration Features
- Import/merge conflict resolution
- Multi-user support (requires significant architecture changes)
- Real-time sync capabilities

### Mobile Enhancements
- Touch gesture support
- Progressive Web App (PWA) features
- Offline-first architecture
- Mobile-specific UI patterns

### Performance Optimizations
- Lazy loading of views
- Component-based architecture migration
- Data compression techniques
- Caching strategies for computed properties

### Advanced Features
- Plugin system for extensions
- Custom field types
- Workflow automation
- Integration with external tools

## Monitoring and Observability

### Error Tracking
- Console logging for debugging
- localStorage error handling
- Form validation feedback
- Graceful degradation messages

### Performance Monitoring
- Load time measurement (manual)
- Operation duration tracking (development)
- Memory usage monitoring (browser tools)

### User Analytics
- No analytics by design (privacy-first)
- Usage patterns observable through data export
- Feature adoption trackable through data structure

## Maintenance Strategy

### Code Organization
- Single file for simplicity
- Clear separation of HTML, CSS, and JavaScript
- Consistent naming conventions
- Comprehensive commenting

### Documentation
- Inline code comments
- Separate architecture documentation
- User guide (README.md)
- Format specification (file-format.md)

### Version Control
- Single file makes diffing easy
- Feature branches for major changes
- Release tagging for versions
- Backup strategy through exports

### Testing Approach
- Manual testing for all features
- Cross-browser compatibility testing
- Data persistence testing
- Export/import workflow validation

## Conclusion

Jiraffe's architecture prioritizes simplicity, privacy, and maintainability over complex enterprise features. The single-file approach makes it easy to understand, modify, and deploy while providing a rich project management experience. The client-side-only design ensures user privacy and eliminates server infrastructure requirements, making it ideal for teams who want control over their data and deployment.

The architecture is designed to be approachable for developers of all skill levels while remaining extensible for future enhancements. The trade-off between simplicity and scalability is intentional, favoring ease of use and deployment over enterprise-scale features.
