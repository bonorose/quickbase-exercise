/**
 * Diff C-02 property names against the live OpenAPI schema.
 * Usage: node scripts/check-contract.mjs [http://localhost:5000]
 */
const base = process.argv[2] ?? process.env.E2E_API_BASE ?? 'http://localhost:5000'
const expected = ['id', 'name', 'email', 'role', 'organization']

const response = await fetch(`${base.replace(/\/$/, '')}/openapi.json`)
if (!response.ok) {
  console.error(`Could not load OpenAPI from ${base}: HTTP ${response.status}`)
  process.exit(1)
}

const spec = await response.json()
const schemas = spec.components?.schemas ?? {}
const userSchema = schemas.UserResponse ?? schemas.User ?? Object.values(schemas).find((schema) => {
  return schema?.properties?.organization && schema?.properties?.email
})

if (!userSchema?.properties) {
  console.error('C-02 UserResponse schema was not found in /openapi.json')
  process.exit(1)
}

const actual = Object.keys(userSchema.properties)
const missing = expected.filter(name => !actual.includes(name))
const extra = actual.filter(name => !expected.includes(name) && name !== 'full_name')

if (missing.length || extra.length) {
  console.error('C-02 contract drift')
  if (missing.length) console.error('  missing:', missing.join(', '))
  if (extra.length) console.error('  extra:', extra.join(', '))
  process.exit(1)
}

console.log('C-02 property names match:', actual.join(', '))
