import { defineVitestConfig } from '@nuxt/test-utils/config'

export default defineVitestConfig({
  test: {
    environment: 'happy-dom',
    include: ['tests/unit/**/*.spec.ts'],
    typecheck: {
      enabled: false,
      include: ['tests/types/**/*.test-d.ts'],
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      reportsDirectory: './coverage',
      include: [
        'app/utils/**/*.ts',
        'app/api/sse.ts',
        'app/services/auth.service.ts',
        'app/services/tickets.service.ts',
        'app/services/dashboard.service.ts',
      ],
    },
  },
})
