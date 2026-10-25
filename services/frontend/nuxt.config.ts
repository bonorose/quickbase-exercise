import tailwindcss from '@tailwindcss/vite'

/**
 * Browsers cannot fetch `0.0.0.0`; map a bind address to loopback.
 * On Windows `localhost` may resolve to IPv6 first, so prefer 127.0.0.1 for local API URLs.
 */
function publicApiBaseFromEnv(fallback: string): string {
  let base = process.env.NUXT_PUBLIC_API_BASE ?? fallback
  if (base.includes('://0.0.0.0')) {
    base = base.replace('://0.0.0.0', '://127.0.0.1')
  }
  return base.replace(/\/$/, '')
}

export default defineNuxtConfig({
  ssr: false,
  compatibilityDate: '2026-10-01',

  devServer: {
    host: '0.0.0.0',
    port: 3000,
  },

  modules: ['shadcn-nuxt', '@pinia/nuxt'],

  shadcn: {
    prefix: '',
    componentDir: './app/components/ui',
  },

  // Feature components register by filename (LoginForm, StatCard, ...); ui/ is registered by shadcn-nuxt
  components: [
    { path: '~/components', pathPrefix: false, ignore: ['ui/**'] },
  ],

  css: ['~/assets/css/tailwind.css'],

  vite: {
    plugins: [tailwindcss()] as never,
    // Docker Desktop on Windows/macOS does not forward fs events into bind mounts
    server: process.env.NUXT_WATCH_POLLING === 'true'
      ? { watch: { usePolling: true, interval: 300 } }
      : {},
  },

  typescript: {
    strict: true,
    typeCheck: false,
  },

  // Only stores + composables are auto-imported; api/ and services/ are imported explicitly
  // so the layer boundaries stay visible in each file's imports.
  imports: {
    dirs: ['stores', 'composables'],
  },

  runtimeConfig: {
    public: {
      apiBase: publicApiBaseFromEnv('http://127.0.0.1:5000'),
      apiPrefix: process.env.NUXT_PUBLIC_API_PREFIX ?? '/api/v1',
    },
  },
})
