/**
 * design-tokens.js
 * Central source of truth for SecurCoachAI design system
 * 
 * Design spec: Warp Terminal meets Linear.app precision
 * Colors, fonts, spacing, and patterns locked and normalized across all components
 */

// ──────────────────────────────────────────────────────────────────────────
// Color Tokens
// ──────────────────────────────────────────────────────────────────────────

export const colors = {
  // Backgrounds
  pageBackground: "#080B10",      // Main page bg
  sidebarBackground: "#0A0E14",   // Sidebar bg
  surfaceBackground: "#0D1117",   // Cards, containers
  
  // Text
  textBright: "#E8DFC8",           // Headings, primary text
  textMuted: "#8A8070",            // Secondary text, descriptions
  textError: "#EF5350",            // Error messages
  textSuccess: "#66BB6A",          // Success messages
  textWarning: "#FFA726",          // Warning messages
  
  // Accent (the ONLY accent color)
  accentGold: "#C1943C",           // Brand, active states, highlights
  accentGoldHover: "#D4A255",      // Gold on hover (lighter)
  accentGoldActive: "#B88630",     // Gold on active (darker)
  
  // Borders & Dividers
  borderDefault: "#1C1A16",        // 0.5px borders
  borderSubtle: "rgba(28, 26, 22, 0.5)",  // Subtle separators
  
  // Interactive states
  disabledBackground: "#3A3A3A",
  disabledText: "#8A8070",
};

// ──────────────────────────────────────────────────────────────────────────
// Typography
// ──────────────────────────────────────────────────────────────────────────

export const fonts = {
  // Font families (must be imported via @import in CSS)
  headingFamily: "'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  bodyFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  codeFamily: "'JetBrains Mono', 'Courier New', monospace",
  
  // Font sizes
  sizes: {
    xs: "12px",      // Micro-labels, small text
    sm: "14px",      // Body text, secondary
    base: "16px",    // Primary body text
    lg: "18px",      // Larger body, card titles
    xl: "20px",      // Subheadings
    xxl: "24px",     // Main headings
    xxxl: "32px",    // Page titles
  },
  
  // Font weights
  weights: {
    regular: 400,
    medium: 500,
    semibold: 600,
  },
};

// ──────────────────────────────────────────────────────────────────────────
// Spacing
// ──────────────────────────────────────────────────────────────────────────

export const spacing = {
  // Base unit: 12px
  xs: "4px",       // 4px
  sm: "8px",       // 8px
  base: "12px",    // 12px (base unit)
  md: "16px",      // 16px
  lg: "24px",      // 24px
  xl: "32px",      // 32px
  xxl: "48px",     // 48px
  xxxl: "64px",    // 64px
};

// ──────────────────────────────────────────────────────────────────────────
// Breakpoints (Mobile-first)
// ──────────────────────────────────────────────────────────────────────────

export const breakpoints = {
  mobile: "375px",   // Mobile (iPhone SE)
  tablet: "768px",   // Tablet (iPad)
  desktop: "1024px", // Desktop
  wide: "1440px",    // Wide desktop
};

// ──────────────────────────────────────────────────────────────────────────
// Component Patterns
// ──────────────────────────────────────────────────────────────────────────

export const patterns = {
  // Border styling (precision, thin borders)
  borderThin: `0.5px solid ${colors.borderDefault}`,
  borderSubtle: `0.5px solid ${colors.borderSubtle}`,
  
  // Focus ring (gold accent, no shadow)
  focusRing: {
    outline: `0.5px solid ${colors.accentGold}`,
    outlineOffset: "2px",
  },
  
  // Box shadows (minimal, dark theme)
  shadowSm: "0 2px 8px rgba(0, 0, 0, 0.3)",
  shadowMd: "0 4px 16px rgba(0, 0, 0, 0.4)",
  shadowLg: "0 8px 32px rgba(0, 0, 0, 0.5)",
  
  // Transitions (smooth, precise)
  transitionFast: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
  transitionBase: "200ms cubic-bezier(0.4, 0, 0.2, 1)",
  transitionSlow: "300ms cubic-bezier(0.4, 0, 0.2, 1)",
};

// ──────────────────────────────────────────────────────────────────────────
// Utility Functions
// ──────────────────────────────────────────────────────────────────────────

/**
 * Converts RGBA color value to CSS variable reference
 * Used for dynamic opacity changes
 */
export const withOpacity = (color, opacity) => {
  if (color.startsWith("rgba")) {
    return color.replace(/[\d.]+\)/, `${opacity})`);
  }
  return color;
};

/**
 * Get responsive spacing based on viewport
 * Example: getResponsiveSpacing('base', 'md') => 12px on mobile, 16px on desktop
 */
export const getResponsiveSpacing = (mobileKey, desktopKey) => {
  return {
    mobile: spacing[mobileKey],
    desktop: spacing[desktopKey],
  };
};

// ──────────────────────────────────────────────────────────────────────────
// CSS Custom Properties (for use in stylesheets)
// ──────────────────────────────────────────────────────────────────────────

export const cssVariables = `
:root {
  /* Colors */
  --color-page-bg: ${colors.pageBackground};
  --color-sidebar-bg: ${colors.sidebarBackground};
  --color-surface: ${colors.surfaceBackground};
  --color-text-bright: ${colors.textBright};
  --color-text-muted: ${colors.textMuted};
  --color-text-error: ${colors.textError};
  --color-accent-gold: ${colors.accentGold};
  --color-accent-gold-hover: ${colors.accentGoldHover};
  --color-border: ${colors.borderDefault};
  
  /* Typography */
  --font-heading: ${fonts.headingFamily};
  --font-body: ${fonts.bodyFamily};
  --font-code: ${fonts.codeFamily};
  --font-size-xs: ${fonts.sizes.xs};
  --font-size-sm: ${fonts.sizes.sm};
  --font-size-base: ${fonts.sizes.base};
  --font-size-lg: ${fonts.sizes.lg};
  
  /* Spacing */
  --spacing-xs: ${spacing.xs};
  --spacing-sm: ${spacing.sm};
  --spacing-base: ${spacing.base};
  --spacing-md: ${spacing.md};
  --spacing-lg: ${spacing.lg};
  
  /* Transitions */
  --transition-fast: ${patterns.transitionFast};
  --transition-base: ${patterns.transitionBase};
}
`;
