# AI Spreadsheets - Product Roadmap & TODO

## User & Data Management

- [ ] Add user authentication system
- [ ] Allow users to persist datasets with ownership
- [ ] Implement dataset sharing (user-to-user and public)
- [ ] Ensure secure and private data handling
- [ ] Add audit logs and activity tracking
- [ ] Implement row-level security and permissions

## Chat & Conversation

- [ ] Add chat history persistence
- [ ] Allow clicking on prior chat answers to restore context
- [ ] Implement multi-turn conversation support
- [ ] Add natural language insights and anomaly detection

## Visualization & Reports

- [ ] Improve slide deck visualization
- [ ] Create dashboard view
- [ ] Implement customizable reports
- [ ] Enable rearranging layout of reports
- [ ] Add professional themes and branding customization
- [ ] Add chart templates and visualization library

## Data Import/Export

- [ ] Support importing datasets from Google Drive
- [ ] Support pulling data from URLs
- [ ] Add cleanup and export spreadsheet functionality
- [ ] Implement export to multiple formats (PDF, Excel, CSV, JSON)
- [ ] Add direct database connections (PostgreSQL, MySQL, etc)
- [ ] Implement drag-and-drop interface for file uploads

## Collaboration & Sharing

- [ ] Provide share options for analyses and reports
- [ ] Add real-time collaboration features
- [ ] Implement publishing workflow for reports and dashboards
- [ ] Add embedded analytics and iframe support

## Workspace Features

- [ ] Allow creating new sheets/tabs
- [ ] Implement workspace organization (folders, tags, favorites)
- [ ] Add data catalog with search and discovery
- [ ] Add mobile-responsive design

## Scheduling & Automation

- [ ] Implement scheduled reports and email delivery
- [ ] Implement data refresh and sync scheduling
- [ ] Implement alerts and notifications

## Data Quality & Governance

- [ ] Add version control for datasets and analyses
- [ ] Add data validation rules and quality checks

## Advanced Features

- [ ] Implement API access for programmatic queries
- [ ] Implement SQL editor with autocomplete
- [ ] Implement caching and query optimization

## Embedded Analytics & Enterprise Features

### Core Platform
- [ ] Headless BI architecture (separate metrics logic from visualization)
- [ ] Reusable metric definitions (define once, use everywhere)
- [ ] Multi-tenancy support (isolate data per customer/organization)
- [ ] White labeling and custom branding

### Data Warehouse Integration
- [ ] Connect to Snowflake
- [ ] Connect to Amazon Redshift
- [ ] Connect to Google BigQuery
- [ ] Connect to Azure SQL Database
- [ ] Connect to Databricks
- [ ] Live query execution on cloud data warehouses

### Developer Tools & SDKs
- [ ] React SDK for embedding analytics components
- [ ] Web Components for non-React frameworks
- [ ] Python SDK for backend automation
- [ ] API for workspace and user management
- [ ] Programmatic dashboard creation

### Embedding & Distribution
- [ ] Iframe embedding with security
- [ ] JavaScript embedding SDK
- [ ] Shareable dashboard links with permissions
- [ ] Customer-facing analytics portals
- [ ] Internal analytics embedding

### Advanced Analytics
- [ ] Saved metric library (centralized business logic)
- [ ] Cross-dataset metric calculations
- [ ] Custom aggregation functions
- [ ] Drill-down and drill-through capabilities
- [ ] Interactive filters with query pushdown

### Security & Compliance
- [ ] Row-level security with dynamic filters
- [ ] Column-level permissions
- [ ] HIPAA compliance features
- [ ] GDPR compliance tools
- [ ] SOC 2 audit logging
- [ ] Single Sign-On (SSO) integration

### Performance & Scalability
- [ ] Query result caching layer
- [ ] Incremental data refresh
- [ ] Materialized views support
- [ ] Query optimization engine
- [ ] Load balancing for embedded analytics

### Workspace Management
- [ ] Programmatic workspace provisioning
- [ ] Template workspaces for rapid deployment
- [ ] Workspace cloning and versioning
- [ ] Cross-workspace metric sharing
- [ ] Usage analytics per workspace

## Completed Features ✅

- [x] Collapsible/resizable sidebar with DataWorkspaceLayout
- [x] AI-powered column metadata descriptions
- [x] Multi-column relationship management for dataset groups
- [x] Auto-detect relationships based on column names and types
- [x] Enhanced schema view with metadata display
- [x] Tabbed settings panel for metadata, rules, and general settings
- [x] Type-aware SQL generation (DATE column handling)
- [x] Natural language to SQL query conversion
- [x] Multi-dataset group queries
- [x] Python analysis mode
- [x] Deep research mode with verbose output
- [x] Dashboard and report views
- [x] Query result visualization
