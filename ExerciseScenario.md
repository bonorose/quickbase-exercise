# Exercise Scenario
By Simeon Marlokov | 25/10/2026

    The following document is an assumption based on the provided 'guarded-tool-use-agent-exercise.md'. To provide more
    business-relevant context for decision making during development, I have written this scenario file containing the 
    product hypothesis.
---
## The Ticketing System
The Ticketing System, or in short (TS), is a SaaS application offering multi-tenant help desk ticketing capabilities.
We integrated it for our Excellence support team 1 year ago. Generally, it is pretty simple - we aggregate submitter tickets and our
internal team then splits work betweem themselves. Once a ticket has started to be processed by our team, anyone from support team
the system records a 'Pending Revision'. This is how we execute a queue-based support administrative system.

We initially got the system as a white-label implementation, but as operations grew and end of January 2026 we released our
new product 'Quantum Workflow', we onboarded a 2nd support team dedicated to it. This required the system to be updated, 
enabling team tenancy, as we didn't want to make a seperate system for only one team. Right now the system is as follows

    TS - http://localhost:1939
    -> Excellence Team
    -> Quantum Workflow Team

This introduced some initial issues, such as teams being able to access different tickets from the other team. At this point
the vendor has mostly fixed this issue and provided us with API access. However, team members still say they see other's tickets 
from time to time.

## qAI - agentic ticketing overhaul
Welcome to qAI. After January's release during the last 6 months we've seen a raising trend of user activity to the support
system. Some are to the Excellence team, and this has been wonderful, as new clients come in. But over 75% of all tickets
are for the 'Quantum Workflow' Team. Our business analysts have gathered the following metrics:
- **Average Ticket Processing Time** - ```39:14``` minutes per ticket combined
- **Average Daily Ticket Count per Employee** - 40 total, out of which
  - 30 for **Quantum**
  - 10 for **Excellence**

These numbers haven't stopped growing and all forecasts show a continued and potentially exponential trend. Our teams
**cannot manage more work** nor can business grow the teams consistently fast enough to meet demand.

## Business use-case
Based on this we have planned building qAI. Our main KPIs with the system are:
- Increase ticket turnover speed - aiming at average of equal or less than ```10``` minutes
  - This we will achieve via AI-aided faster ticket searching and data preparation
- Eliminate the team ticket pollution for good
  - We plan on building a new database layer on our side, enabling strict team scoping and no data leaking because we
share the same organization account
- Human in the loop and human-centered - we want to integrate AI into our workflow, but not depend blindly on it. Maybe 
in the future we will build a fully automated workflow, but until then we want every key decision to be done by the 
people. All tools can be used, but the operators are responsible for the final result and decision.
- Have security and correct permissions be built-in since day 1.

## Potential Future Features
To enable system automation we plan to implement RAG the following way:
- Chunk and embed all existing tickets in the system
- Set up the following vectors:
  - Title
  - Description - a AI-generated summary of the contents, including every ticket in a discussion
  - Contents
- Team-based separation - each 'tenant' has its own different database and vectors, keeping separation in the root

---
## Data Models

### Organization
  - organization_id: incremental int
  - name: str char(255) -> the name of the team

### User
  - user_id: incremental int
  - name: str char (255)
  - email: str char(255)
  - password: str char(255)
  - organization_id: int FK

### Ticket
  - ticket_id
  - status: StatusEnum
  - priority: PriorityEnum
  - title: str char(255)
  - description: str char(500)
  - contents: str char(2000) - rich text, supporting MD-based formatting (not html)
  - submitted_by: str char(255) -> email of the client submitting the ticket
  - date_created: unix timestamp
  - updated_by: user_id
  - date_updated: unix timestamp

### Revisions
  - revision_id - uuid v4
  - ticket_id
  - user_id
  - initial_contents
  - changed_contents
  - date_created

### Pending Revisions
  - id
  - ticket_id
  - previous_revision_id - we get the ticket contents from the last available revision
  - user_id
  - changed_contents
  - date_created
  - date_updated

### Discussions
  - id
  - ticket_id
  - user_id
  - contents

### StatusEnum
  - 1 - Open
  - 2 - Blocked
  - 3 - Closed

### PriorityEnum
  - 1 - Lowest
  - 2 - Low
  - 3 - Medium
  - 4 - High
  - 5 - Critical