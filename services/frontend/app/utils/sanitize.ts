/** Cap attacker-controlled text so the page stays responsive. */
export function truncateForDisplay(text: string, maxChars = 20_000): string {
  if (text.length <= maxChars) return text
  return text.slice(0, maxChars)
}

export function isDisplayTruncated(text: string, maxChars = 20_000): boolean {
  return text.length > maxChars
}

const MARKDOWN_IMAGE = /!\[[^\]]*]\(\s*[^)]+\)/g
const HTML_IMAGE = /<img\b[^>]*>/gi
const HTML_SCRIPT = /<script\b[^>]*>[\s\S]*?<\/script>/gi

/** Keep assistant text inert until FE-047: no remote images, no script tags. */
export function inertAssistantText(text: string): string {
  return truncateForDisplay(
    text
      .replace(MARKDOWN_IMAGE, '[image removed]')
      .replace(HTML_IMAGE, '[image removed]')
      .replace(HTML_SCRIPT, ''),
  )
}
