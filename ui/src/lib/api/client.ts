import { 
  loadDatasetSummary, 
  loadTariffDistribution, 
  loadDailyConsumption, 
  loadPipelineSummary, 
  loadDataQuality, 
  loadSchema,
  loadMasterCustomers,
  loadMasterAccounts,
  loadMasterContracts,
  loadMasterServicePoints,
  loadMasterMeters
} from "../data/snapshot";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const DATA_MODE = process.env.NEXT_PUBLIC_DATA_MODE || "api";

export async function fetcher(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  return response.json();
}

const liveApi = {
  dashboard: {
    getSummary: () => fetcher('/dashboard/summary'),
  },
  pipelines: {
    list: () => fetcher('/pipelines'),
    get: (id: string) => fetcher(`/pipelines/${id}`),
    getRuns: (id: string) => fetcher(`/pipelines/${id}/runs`),
    triggerRun: (id: string) => fetcher(`/pipelines/${id}/run`, { method: 'POST', body: JSON.stringify({ trigger_type: 'MANUAL' }) }),
  },
  backfills: {
    list: () => fetcher('/backfills'),
    create: (dataset: string, start_date: string, end_date: string) => 
      fetcher('/backfills', { method: 'POST', body: JSON.stringify({ dataset, start_date, end_date }) }),
  },
  quality: {
    getSummary: () => fetcher('/data-quality/summary'),
    getIssues: () => fetcher('/data-quality/issues')
  },
  dlq: {
    list: () => fetcher('/dlq'),
    replay: (id: string) => fetcher(`/dlq/${id}/replay`, { method: 'POST' }),
  },
  ingestion: {
    getStatus: () => fetcher('/ingestion/status'),
    trigger: (resource: string, mode: string = 'test') => fetcher('/ingestion/smartmeter', { method: 'POST', body: JSON.stringify({ resource, mode }) })
  },
  processing: {
    getStatus: () => fetcher('/processing/status'),
    listRuns: () => fetcher('/processing/runs'),
    trigger: (ingestion_run_id: string) => fetcher('/processing/standardize', { method: 'POST', body: JSON.stringify({ ingestion_run_id }) })
  },
  analytics: {
    getSummary: () => fetcher('/analytics/summary'),
    getDailyConsumption: () => fetcher('/analytics/consumption/daily'),
    getHouseholds: () => fetcher('/analytics/households'),
    getGoldStats: () => fetcher('/analytics/gold-stats'),
    getPipelineSummary: () => fetcher('/analytics/pipeline-summary'),
    getTariffs: () => fetcher('/analytics/tariffs'),
  },
  masterData: {
    getCustomers: () => fetcher('/master-data/customers'),
    getAccounts: () => fetcher('/master-data/accounts'),
    getContracts: () => fetcher('/master-data/contracts'),
    getServicePoints: () => fetcher('/master-data/service-points'),
    getMeters: () => fetcher('/master-data/meters'),
  }
};

const demoApi = {
  dashboard: {
    getSummary: async () => {
      const ds = await loadDatasetSummary();
      const dq = await loadDataQuality();
      return {
        records_processed_today: ds.total_rows,
        quality_score: dq.quality_score,
        failed_runs: 0,
        dlq_count: 0,
        active_sources: 1
      };
    }
  },
  pipelines: {
    list: async () => [],
    get: async () => ({}),
    getRuns: async () => [],
    triggerRun: async () => { throw new Error("Not available in frontend demo") }
  },
  backfills: {
    list: async () => [],
    create: async () => { throw new Error("Not available in frontend demo") }
  },
  quality: {
    getSummary: async () => {
      const dq = await loadDataQuality();
      return {
        overall_score: dq.quality_score,
        completeness: dq.dimensions.completeness,
        validity: dq.dimensions.validity,
        uniqueness: dq.dimensions.uniqueness,
        consistency: 100,
        timeliness: 100
      };
    },
    getIssues: async () => []
  },
  dlq: {
    list: async () => [],
    replay: async () => { throw new Error("Not available in frontend demo") }
  },
  ingestion: {
    getStatus: async () => ({ status: 'ACTIVE', sources: 1 }),
    trigger: async () => { throw new Error("Not available in frontend demo") }
  },
  processing: {
    getStatus: async () => ({ status: 'ACTIVE', last_run: new Date().toISOString() }),
    listRuns: async () => {
      const ds = await loadDatasetSummary();
      return [{
        run_id: "demo-run",
        dataset: "UKPN SmartMeter",
        status: "SUCCESS",
        started_at: ds.generated_at,
        rows_processed: ds.total_rows,
        source_file: ds.gold_file
      }];
    },
    trigger: async () => { throw new Error("Not available in frontend demo") }
  },
  analytics: {
    getSummary: async () => ({}),
    getDailyConsumption: async () => {
      const dc = await loadDailyConsumption();
      return dc.daily.map(d => ({ day: d.date, consumption: d.total_kwh }));
    },
    getHouseholds: async () => [],
    getGoldStats: async () => {
      const ds = await loadDatasetSummary();
      return {
        available: true,
        total_rows: ds.total_rows,
        distinct_households: ds.distinct_households,
        total_consumption_kwh: ds.total_consumption_kwh,
        date_range: ds.date_range,
        storage_zone: ds.storage_zone,
        tariff_distribution: {
          Std: ds.tariff_std_count,
          ToU: ds.tariff_tou_count
        }
      };
    },
    getPipelineSummary: async () => {
      return await loadPipelineSummary();
    },
    getTariffs: async () => {
      const td = await loadTariffDistribution();
      return td.distribution;
    }
  },
  masterData: {
    getCustomers: async () => await loadMasterCustomers(),
    getAccounts: async () => await loadMasterAccounts(),
    getContracts: async () => await loadMasterContracts(),
    getServicePoints: async () => await loadMasterServicePoints(),
    getMeters: async () => await loadMasterMeters(),
  }
};

export const api = DATA_MODE === "demo" ? demoApi : liveApi;
