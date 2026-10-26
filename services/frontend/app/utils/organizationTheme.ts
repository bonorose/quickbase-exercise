/**
 * Tenant chips stay inside the quickAI palette and at least 4.5:1.
 * Excellence is Forest Ink. Quantum is a Teal Signal wash. Others use Muted Ink.
 */
const THEMES: Record<string, string> = {
  excellence: 'border-transparent bg-forest text-white hover:bg-forest',
  'quantum workflow': 'border-teal-signal bg-teal-wash text-forest hover:bg-teal-wash',
}

export function organizationBadgeClass(name: string): string {
  const key = name.trim().toLowerCase()
  if (key in THEMES) return THEMES[key]!
  if (key.includes('quantum')) return THEMES['quantum workflow']!
  if (key.includes('excellence')) return THEMES.excellence!
  return 'border-transparent bg-ink text-white hover:bg-ink'
}
