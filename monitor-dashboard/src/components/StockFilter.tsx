import { Filter } from 'lucide-react';

interface StockFilterProps {
  filters: {
    industry: string;
    minMarketCap: number;
    maxMarketCap: number;
    minChange: number;
    maxChange: number;
    minVolume: number;
  };
  onFilterChange: (filters: {
    industry: string;
    minMarketCap: number;
    maxMarketCap: number;
    minChange: number;
    maxChange: number;
    minVolume: number;
  }) => void;
}

const industries = [
  'All',
  'Tech',
  'Finance',
  'Consumer',
  'Healthcare',
  'Energy',
  'Materials',
  'Industrials',
  'Auto',
  'Real Estate',
  'Transport',
  'Telecom',
  'Utilities',
  'Media',
  'Logistics',
  'Agriculture',
];

export function StockFilter({ filters, onFilterChange }: StockFilterProps) {
  const handleChange = (key: string, value: string | number) => {
    onFilterChange({
      ...filters,
      [key]: value,
    });
  };

  const marketCapOptions = [
    { label: 'All', min: 0, max: 10000000000000 },
    { label: '< 10B', min: 0, max: 10000000000 },
    { label: '10B - 100B', min: 10000000000, max: 100000000000 },
    { label: '100B - 500B', min: 100000000000, max: 500000000000 },
    { label: '> 500B', min: 500000000000, max: 10000000000000 },
  ];

  const changeOptions = [
    { label: 'All', min: -100, max: 100 },
    { label: '< -5%', min: -100, max: -5 },
    { label: '-5% to +5%', min: -5, max: 5 },
    { label: '> +5%', min: 5, max: 100 },
  ];

  const volumeOptions = [
    { label: 'All', value: 0 },
    { label: '> 1M', value: 1000000 },
    { label: '> 5M', value: 5000000 },
    { label: '> 10M', value: 10000000 },
    { label: '> 50M', value: 50000000 },
  ];

  const formatMarketCap = (value: number) => {
    if (value >= 100000000000) return `${(value / 100000000000).toFixed(1)}00B`;
    if (value >= 1000000000) return `${(value / 1000000000).toFixed(0)}B`;
    if (value >= 1000000) return `${(value / 1000000).toFixed(0)}M`;
    return value.toString();
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-accent-cyan" />
          <h2 className="text-lg font-semibold text-text-primary">Filter Stocks</h2>
        </div>
      </div>

      <div className="p-5 space-y-5">
        <div>
          <label className="block text-sm text-text-secondary mb-2">Industry</label>
          <select
            value={filters.industry}
            onChange={(e) => handleChange('industry', e.target.value)}
            className="w-full px-3 py-2.5 bg-bg-secondary border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-accent-cyan transition-colors"
          >
            {industries.map((industry) => (
              <option key={industry} value={industry === 'All' ? '' : industry}>
                {industry}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-text-secondary mb-2">Market Cap</label>
          <div className="grid grid-cols-2 gap-2">
            {marketCapOptions.map((opt) => (
              <button
                key={opt.label}
                onClick={() => {
                  handleChange('minMarketCap', opt.min);
                  handleChange('maxMarketCap', opt.max);
                }}
                className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                  filters.minMarketCap === opt.min && filters.maxMarketCap === opt.max
                    ? 'bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/50'
                    : 'bg-bg-secondary text-text-secondary border border-border hover:border-border-light'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-text-muted">
            <span>{formatMarketCap(filters.minMarketCap)}</span>
            <span>to</span>
            <span>{formatMarketCap(filters.maxMarketCap)}</span>
          </div>
        </div>

        <div>
          <label className="block text-sm text-text-secondary mb-2">Price Change</label>
          <div className="grid grid-cols-2 gap-2">
            {changeOptions.map((opt) => (
              <button
                key={opt.label}
                onClick={() => {
                  handleChange('minChange', opt.min);
                  handleChange('maxChange', opt.max);
                }}
                className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                  filters.minChange === opt.min && filters.maxChange === opt.max
                    ? 'bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/50'
                    : 'bg-bg-secondary text-text-secondary border border-border hover:border-border-light'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm text-text-secondary mb-2">Volume Threshold</label>
          <div className="grid grid-cols-2 gap-2">
            {volumeOptions.map((opt) => (
              <button
                key={opt.label}
                onClick={() => handleChange('minVolume', opt.value)}
                className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                  filters.minVolume === opt.value
                    ? 'bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/50'
                    : 'bg-bg-secondary text-text-secondary border border-border hover:border-border-light'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={() =>
            onFilterChange({
              industry: '',
              minMarketCap: 0,
              maxMarketCap: 10000000000000,
              minChange: -100,
              maxChange: 100,
              minVolume: 0,
            })
          }
          className="w-full py-2.5 bg-bg-secondary hover:bg-bg-hover text-text-secondary rounded-lg transition-colors text-sm border border-border"
        >
          Reset Filters
        </button>
      </div>
    </div>
  );
}
