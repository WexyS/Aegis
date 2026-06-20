const SECRET_PATTERNS = [
  { pattern: /\bsk-[A-Za-z0-9_-]{8,}/i, reason: 'Secret-like key pattern detected.' },
  { pattern: /\b(?:API_KEY|TOKEN|PASSWORD)\s*=\s*\S+/i, reason: 'Credential assignment pattern detected.' },
] as const;

export function detectSecretLikeMemoryContent(value: string): string | null {
  for (const candidate of SECRET_PATTERNS) {
    if (candidate.pattern.test(value)) return candidate.reason;
  }
  return null;
}
