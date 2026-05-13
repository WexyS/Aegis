/**
 * ══════════════════════════════════════════════════════════════════════
 * AEGIS DESIGN TOKENS v1.0
 * ══════════════════════════════════════════════════════════════════════
 *
 * Central registry for all visual constants.
 * Every component MUST reference these tokens — no hardcoded values.
 *
 * This prevents "3-week UI rot" where spacing/colors drift apart.
 * ══════════════════════════════════════════════════════════════════════
 */

export const tokens = {
  // ─── SPACING ─────────────────────────────────────────────────────
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
  },

  // ─── RADIUS ──────────────────────────────────────────────────────
  radius: {
    sm: '0.5rem',    // 8px  — badges, pills
    md: '0.75rem',   // 12px — cards, inputs
    lg: '1rem',      // 16px — panels
    xl: '1.5rem',    // 24px — main containers
    full: '9999px',  // pills, avatars
  },

  // ─── TYPOGRAPHY ──────────────────────────────────────────────────
  fontSize: {
    micro: '8px',    // system labels, badges
    tiny: '9px',     // metadata, secondary labels
    xs: '10px',      // section headers, timestamps
    sm: '11px',      // compact UI text
    base: '13px',    // body text, messages
    lg: '16px',      // headings
    xl: '20px',      // page titles
    '2xl': '28px',   // hero numbers
  },

  // ─── TRANSITIONS ─────────────────────────────────────────────────
  transition: {
    fast: '150ms ease-out',
    normal: '300ms ease-out',
    slow: '500ms ease-out',
    spring: '300ms cubic-bezier(0.34, 1.56, 0.64, 1)',
  },

  // ─── SHADOWS (Glassmorphism stack) ───────────────────────────────
  shadow: {
    card: 'inset 0 1px 0 rgba(255, 255, 255, 0.05)',
    cardHover: '0 8px 30px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
    panel: '0 4px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
    glow: {
      accent: '0 0 20px rgba(6, 182, 212, 0.2)',
      accentStrong: '0 0 30px rgba(6, 182, 212, 0.4), inset 0 0 10px rgba(6, 182, 212, 0.2)',
      success: '0 0 10px rgba(16, 185, 129, 0.5)',
      danger: '0 0 10px rgba(244, 63, 94, 0.5)',
      secondary: '0 0 15px rgba(139, 92, 246, 0.3)',
    },
  },

  // ─── Z-INDEX LAYERS ──────────────────────────────────────────────
  zIndex: {
    base: 0,
    content: 10,
    sidebar: 50,
    header: 40,
    console: 20,
    overlay: 100,
    modal: 200,
    toast: 300,
  },

  // ─── ANIMATION BUDGET ────────────────────────────────────────────
  // Max simultaneous framer-motion animations before throttling
  animation: {
    maxConcurrent: 8,
    staggerDelay: 0.05,       // seconds between staggered items
    maxTimelineItems: 50,     // virtualize beyond this
    maxChatMessages: 100,     // virtualize beyond this
    blurBudget: 3,            // max simultaneous backdrop-blur elements
  },
} as const;

export type DesignTokens = typeof tokens;
