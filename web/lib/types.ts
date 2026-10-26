// Mirrors the API's report JSON (api/app/report.py). Numbers are null when undefined.
export type Verdict = 'significant_win' | 'significant_loss' | 'not_significant' | 'srm_invalid';
export type Kind = 'binary' | 'continuous';
export type Interval = [number | null, number | null];

export type TestOut = {
  control_mean: number | null;
  treatment_mean: number | null;
  abs_lift: number | null;
  abs_ci: Interval;
  rel_lift: number | null;
  rel_ci: Interval | null;
  p_value: number | null;
  stat: number | null;
  se: number | null;
};

export type CupedOut = { theta: number | null; variance_reduction: number | null; result: TestOut };

export type SrmOut = {
  control_n: number;
  treatment_n: number;
  expected_split: number;
  observed_split: number | null;
  chi2: number | null;
  p_value: number | null;
  flagged: boolean;
};

export type Checkpoint = { n: number; p_value: number | null; ci_low: number | null; ci_high: number | null };
export type SequentialOut = {
  tau: number | null;
  points: Checkpoint[];
  stopped_at: number | null;
  tau_from_data: boolean;
};

export type Summary = {
  control: string;
  treatment: string;
  kind: Kind;
  control_n: number;
  treatment_n: number;
  control_mean: number | null;
  treatment_mean: number | null;
  has_pre_metric: boolean;
  has_timestamp: boolean;
};

export type Report = {
  summary: Summary;
  alpha: number;
  expected_split: number;
  primary: 'raw' | 'cuped';
  verdict: Verdict;
  raw: TestOut;
  cuped: CupedOut | null;
  srm: SrmOut;
  sequential: SequentialOut | null;
};

export type Created = { id: string; report: Report };
export type StoredReport = { id: string; name: string; source: string; created_at: string; report: Report };
export type SampleInfo = { name: string; title: string; description: string; truth: Verdict };
export type PowerBody = { baseline: number; mde: number; alpha?: number; power?: number; kind?: Kind; sd?: number };
export type UploadOptions = { name?: string; control?: string; expectedSplit?: number; alpha?: number };
