import type { Verdict } from './types';

// Mirrors the API's built-in samples so the home page renders instantly, even while the free API sleeps.
export const SAMPLES: { name: string; title: string; description: string; truth: Verdict; note: string }[] = [
  {
    name: 'checkout_win',
    title: 'Checkout redesign',
    description: 'Conversion rate, 40,000 users, with past visits as a covariate.',
    truth: 'significant_win',
    note: 'a real +10% lift',
  },
  {
    name: 'pricing_null',
    title: 'Pricing page copy',
    description: "Revenue per user, 20,000 users, with last month's revenue as a covariate.",
    truth: 'not_significant',
    note: 'no real effect',
  },
  {
    name: 'broken_split',
    title: 'Onboarding email',
    description: 'Conversion rate, where a logging bug silently dropped some treatment users.',
    truth: 'srm_invalid',
    note: 'a broken split',
  },
];

export const MAX_UPLOAD_MB = 20;
