declare module '#app' {
  interface PageMeta {
    /** Opt out of the global auth middleware (middleware/auth.global.ts). */
    public?: boolean
  }
}

export {}
