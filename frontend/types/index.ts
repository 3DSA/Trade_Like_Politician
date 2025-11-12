export interface Transaction {
  transaction_id: number;
  filing_id: number;
  doc_id: string;
  tx_number?: number;
  tx_date?: string;
  owner?: string;
  ticker?: string;
  asset_name: string;
  asset_type?: string;
  rate_coupon?: string;
  maturity_date?: string;
  tx_type: string;
  amount_range?: string;
  amount_min?: number;
  amount_max?: number;
  comment?: string;
  row_confidence?: number;
  created_at?: string;
  senator_name?: string;
  filing_date?: string;
}

export interface SenatorStats {
  full_name: string;
  total_transactions: number;
  total_volume_estimate?: number;
  earliest_trade?: string;
  latest_trade?: string;
  total_purchases?: number;
  total_sales?: number;
}

export interface TradingStats {
  total_transactions: number;
  total_filings: number;
  total_senators: number;
  total_volume_estimate?: number;
  date_range_start?: string;
  date_range_end?: string;
}
