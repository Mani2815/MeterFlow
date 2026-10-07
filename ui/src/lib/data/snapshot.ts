/**
 * src/lib/data/snapshot.ts
 *
 * Low-level loader for the static demo data snapshots in /public/data/.
 * In a live deployment this would be replaced with fetch() to the FastAPI backend.
 *
 * All files are fetched at runtime (client-side) so no Node.js build-time
 * access is required and Vercel can serve them as plain static assets.
 */

const BASE = "/data";

async function load<T>(filename: string): Promise<T> {
  const res = await fetch(`${BASE}/${filename}`);
  if (!res.ok) throw new Error(`Failed to load snapshot: ${filename} (${res.status})`);
  return res.json() as Promise<T>;
}

// ─── Raw snapshot types ────────────────────────────────────────────────────

export interface DatasetSummary {
  generated_at: string;
  source: string;
  source_url: string;
  gold_file: string;
  storage_zone: string;
  total_rows: number;
  distinct_households: number;
  total_consumption_kwh: number;
  tariff_std_count: number;
  tariff_tou_count: number;
  date_range: { from: string | null; to: string | null };
  columns: string[];
}

export interface TariffDistribution {
  generated_at: string;
  distribution: { tariff: string; count: number; pct: number }[];
}

export interface DailyConsumption {
  generated_at: string;
  daily: { date: string; total_kwh: number; reading_count: number }[];
}

export interface PipelineStage {
  name: string;
  status: string;
  description?: string;
  format?: string;
  fields?: string[];
  rows?: number | null;
  rejected?: number;
  dlq?: number;
  quality_score?: number;
}

export interface PipelineSummary {
  generated_at: string;
  note: string;
  stages: PipelineStage[];
}

export interface DataQuality {
  generated_at: string;
  source: string;
  total_rows: number;
  valid_rows: number;
  null_tariff: number;
  null_kwh: number;
  duplicates: number;
  quality_score: number;
  dimensions: {
    completeness: number;
    validity: number;
    uniqueness: number;
  };
}

export interface SchemaColumn {
  name: string;
  type: string;
  nullable: boolean;
  origin: string;
  description: string;
}

export interface Schema {
  generated_at: string;
  table: string;
  description: string;
  columns: SchemaColumn[];
}

// ─── Loader functions ──────────────────────────────────────────────────────

export const loadDatasetSummary = () => load<DatasetSummary>("dataset-summary.json");
export const loadTariffDistribution = () => load<TariffDistribution>("tariff-distribution.json");
export const loadDailyConsumption = () => load<DailyConsumption>("daily-consumption.json");
export const loadPipelineSummary = () => load<PipelineSummary>("pipeline-summary.json");
export const loadDataQuality = () => load<DataQuality>("data-quality.json");
export const loadSchema = () => load<Schema>("schema.json");

export const loadMasterCustomers = () => load<any[]>("master-data-customers.json");
export const loadMasterAccounts = () => load<any[]>("master-data-accounts.json");
export const loadMasterContracts = () => load<any[]>("master-data-contracts.json");
export const loadMasterServicePoints = () => load<any[]>("master-data-service-points.json");
export const loadMasterMeters = () => load<any[]>("master-data-meters.json");
