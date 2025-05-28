# Jiraffe Markdown File Format Documentation

This document describes the Markdown format used by Jiraffe for importing and exporting project management data.

## Overview

Jiraffe uses a structured Markdown format that organizes projects by teams and includes all related tasks, interactions, and ADRs. This format is human-readable and can be easily edited in any text editor while maintaining compatibility with Jiraffe's import functionality.

## File Structure

```
# Jiraffe Project Management

Generated: [timestamp]

## Team: [Team Name]

**Members:** [comma-separated list of team members]
**Tags:** [comma-separated list of tags]

### Projects

#### [Project Name]

- **Priority:** [critical|urgent|important|enhancement]
- **Status:** [not-started|ongoing|complete|on-hold]
- **Start Date:** [YYYY-MM-DD]
- **End Date:** [YYYY-MM-DD] (optional)
- **Progress:** [free-form progress notes]
- **Tags:** [comma-separated list of project tags]

**Tasks:**

- [✅|⏳] [Task Title] (Due: [YYYY-MM-DD]) - [status]

**Recent Interactions:**

- [Interaction Title] ([YYYY-MM-DD]) - [meeting|chat|email]

**ADRs:**

- [ADR Title] - [status] (Due: [YYYY-MM-DD])

---
```

## Detailed Format Specification

### Header Section

Every Jiraffe export starts with:
```markdown
# Jiraffe Project Management

Generated: [ISO timestamp]
```

### Team Section

Each team is represented as a level 2 heading:
```markdown
## Team: Engineering Team
```

#### Team Metadata
- **Members:** Comma-separated list of team member names
- **Tags:** Comma-separated list of team tags/categories

Example:
```markdown
**Members:** John Doe, Jane Smith, Bob Johnson
**Tags:** backend, api, microservices
```

### Project Section

Projects are grouped under teams with level 4 headings:
```markdown
#### API Security Audit
```

#### Project Metadata
All project metadata is listed as bullet points with bold labels:

- **Priority:** One of `critical`, `urgent`, `important`, or `enhancement`
- **Status:** One of `not-started`, `ongoing`, `complete`, or `on-hold`
- **Start Date:** ISO date format (YYYY-MM-DD)
- **End Date:** ISO date format (optional, omit if ongoing)
- **Progress:** Free-form text describing current status
- **Tags:** Comma-separated list of project-specific tags

Example:
```markdown
- **Priority:** urgent
- **Status:** ongoing
- **Start Date:** 2024-01-15
- **End Date:** 2024-03-30
- **Progress:** Completed initial assessment, currently implementing fixes
- **Tags:** security, audit, compliance
```

### Tasks Section

Tasks are listed under a "Tasks:" subheading with checkboxes:

```markdown
**Tasks:**

- ✅ Complete security assessment (Due: 2024-01-30) - complete
- ⏳ Implement authentication fixes (Due: 2024-02-15) - ongoing
- ⏳ Update documentation (Due: 2024-02-28) - not-started
```

#### Task Format
- Checkbox: `✅` for completed tasks, `⏳` for pending tasks
- Title: Free-form task description
- Due date: In parentheses, format "Due: YYYY-MM-DD"
- Status: One of `not-started`, `ongoing`, or `complete`

### Interactions Section

Recent interactions are listed under "Recent Interactions:":

```markdown
**Recent Interactions:**

- Weekly Security Review (2024-01-22) - meeting
- Slack discussion on auth strategy (2024-01-20) - chat
- Security findings email (2024-01-18) - email
```

#### Interaction Format
- Title: Free-form interaction description
- Date: In parentheses, format (YYYY-MM-DD)
- Type: One of `meeting`, `chat`, or `email`

### ADRs Section

Architecture Decision Records are listed under "ADRs:":

```markdown
**ADRs:**

- OAuth 2.0 Implementation Strategy - approved (Due: 2024-02-01)
- Database Encryption Standards - waiting-for-me (Due: 2024-02-15)
- API Rate Limiting Approach - not-started (Due: 2024-03-01)
```

#### ADR Format
- Title: Free-form ADR description
- Status: One of `not-started`, `waiting-for-me`, `waiting-for-others`, `approved`, `rejected`, or `on-hold`
- Due date: In parentheses, format "Due: YYYY-MM-DD"

### Team Separator

Teams are separated by a horizontal rule:
```markdown
---
```

## Import Guidelines

When importing Markdown files into Jiraffe:

1. **File Structure:** The file must follow the exact structure outlined above
2. **Required Fields:** Team names and project names are required
3. **Date Formats:** All dates must be in ISO format (YYYY-MM-DD)
4. **Status Values:** Must match exactly the allowed values listed above
5. **Team Names:** Must be unique within the file
6. **Project Names:** Must be unique within each team

## Export Behavior

When exporting from Jiraffe:

1. **Team Ordering:** Teams are sorted alphabetically
2. **Project Ordering:** Projects within teams are sorted by priority, then name
3. **Task Limits:** Only active tasks are exported by default
4. **Interaction Limits:** Only the 5 most recent interactions per project
5. **Date Formatting:** All dates are exported in ISO format
6. **Special Teams:** The "1-1 Meetings" team is excluded from exports

## Example Complete File

```markdown
# Jiraffe Project Management

Generated: 1/15/2024, 2:30:45 PM

## Team: Backend Engineering

**Members:** Alice Johnson, Bob Smith, Carol Davis
**Tags:** backend, api, microservices

### Projects

#### User Authentication System

- **Priority:** critical
- **Status:** ongoing
- **Start Date:** 2024-01-01
- **End Date:** 2024-02-28
- **Progress:** OAuth integration complete, working on session management
- **Tags:** auth, security, oauth

**Tasks:**

- ✅ Design authentication flow (Due: 2024-01-15) - complete
- ⏳ Implement OAuth 2.0 (Due: 2024-01-30) - ongoing
- ⏳ Add session management (Due: 2024-02-15) - not-started

**Recent Interactions:**

- Sprint Planning Meeting (2024-01-15) - meeting
- OAuth implementation discussion (2024-01-12) - chat

**ADRs:**

- OAuth 2.0 Provider Selection - approved (Due: 2024-01-20)
- Session Storage Strategy - waiting-for-me (Due: 2024-02-01)

#### API Rate Limiting

- **Priority:** important
- **Status:** not-started
- **Start Date:** 2024-02-01
- **Tags:** performance, security

**Tasks:**

- ⏳ Research rate limiting strategies (Due: 2024-02-10) - not-started

**Recent Interactions:**

**ADRs:**

---

## Team: Frontend Engineering

**Members:** David Wilson, Eve Brown
**Tags:** frontend, react, ui

### Projects

#### Dashboard Redesign

- **Priority:** enhancement
- **Status:** ongoing
- **Start Date:** 2024-01-10
- **Progress:** Wireframes complete, starting implementation

**Tasks:**

- ✅ Create wireframes (Due: 2024-01-20) - complete
- ⏳ Implement new layout (Due: 2024-02-05) - ongoing

**Recent Interactions:**

- Design review meeting (2024-01-18) - meeting

**ADRs:**

---
```

## Version History

- **v1.0** (2024-01-15): Initial format specification
- Current implementation supports export only; import functionality is planned for future releases

## Notes

- This format is designed to be both human-readable and machine-parseable
- All text fields support basic Markdown formatting within their content
- Special characters in names and descriptions are preserved as-is
- Empty sections (no tasks, interactions, or ADRs) are included for completeness
