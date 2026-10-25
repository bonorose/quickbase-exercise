interface JwtPayload {
  exp?: number
  sub?: string
}

function base64UrlDecode(input: string): string {
  const base64 = input.replace(/-/g, '+').replace(/_/g, '/')
  return atob(base64 + '='.repeat((4 - (base64.length % 4)) % 4))
}

/** Decode the payload without verifying the signature (client-side expiry check only). */
export function decodeJwtPayload(token: string): JwtPayload | null {
  const payload = token.split('.')[1]
  if (!payload) return null
  try {
    return JSON.parse(base64UrlDecode(payload)) as JwtPayload
  }
  catch {
    return null
  }
}

/** True when the token is missing, malformed, or past `exp` (minus a small skew). */
export function isJwtExpired(token: string | null | undefined, skewSeconds = 30): boolean {
  if (!token) return true
  const exp = decodeJwtPayload(token)?.exp
  return !exp || exp <= Math.floor(Date.now() / 1000) + skewSeconds
}
