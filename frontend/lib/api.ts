import axios from 'axios';
import { Transaction, SenatorStats, TradingStats } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getRecentTrades = async (params?: {
  limit?: number;
  offset?: number;
  ticker?: string;
  tx_type?: string;
  min_amount?: number;
}): Promise<Transaction[]> => {
  const response = await api.get('/api/trades/recent', { params });
  return response.data;
};

export const getSenatorTrades = async (
  senatorName: string,
  params?: { limit?: number; offset?: number }
): Promise<Transaction[]> => {
  const response = await api.get(`/api/trades/senator/${encodeURIComponent(senatorName)}`, { params });
  return response.data;
};

export const getSenators = async (params?: {
  limit?: number;
  order_by?: 'total_transactions' | 'total_volume_estimate' | 'latest_trade';
}): Promise<SenatorStats[]> => {
  const response = await api.get('/api/senators', { params });
  return response.data;
};

export const getSenatorStats = async (senatorName: string): Promise<SenatorStats> => {
  const response = await api.get(`/api/senators/${encodeURIComponent(senatorName)}/stats`);
  return response.data;
};

export const getOverallStats = async (): Promise<TradingStats> => {
  const response = await api.get('/api/stats');
  return response.data;
};
