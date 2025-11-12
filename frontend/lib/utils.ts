export function formatCurrency(amount?: number): string {
  if (!amount) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(dateString?: string): string {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
}

export function getTransactionTypeColor(txType?: string): string {
  if (!txType) return 'bg-gray-100 text-gray-800';
  const lower = txType.toLowerCase();
  if (lower.includes('purchase')) return 'bg-green-100 text-green-800';
  if (lower.includes('sale')) return 'bg-red-100 text-red-800';
  if (lower.includes('exchange')) return 'bg-blue-100 text-blue-800';
  return 'bg-gray-100 text-gray-800';
}

export function formatTransactionType(txType?: string): string {
  if (!txType) return 'Unknown';
  return txType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}
