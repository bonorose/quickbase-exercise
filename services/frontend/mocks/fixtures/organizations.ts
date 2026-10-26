import type { OrganizationSummary } from '~/types/api/responses'

export const organizations = {
  excellence: { id: 1, name: 'Excellence' } satisfies OrganizationSummary,
  quantum: { id: 2, name: 'Quantum Workflow' } satisfies OrganizationSummary,
}
