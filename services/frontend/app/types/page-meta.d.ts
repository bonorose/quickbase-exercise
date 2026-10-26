declare module '#app' {
  interface PageMeta {
    /** Opt out of the global auth middleware (middleware/auth.global.ts). */
    public?: boolean
    /** Use the full width and height below the header; the page manages its own scrolling. */
    fullBleed?: boolean
  }
}

export {}
