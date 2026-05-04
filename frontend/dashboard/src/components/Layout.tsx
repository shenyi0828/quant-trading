import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, BarChart3, LayoutDashboard, Settings, TrendingUp, PieChart, Layers, GitCompare, LineChart, SlidersHorizontal } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/strategies', label: '策略管理', icon: BarChart3 },
    { path: '/factors', label: '因子分析', icon: TrendingUp },
    { path: '/backtest', label: '回测分析', icon: PieChart },
    { path: '/pool', label: '股票池', icon: Layers },
    { path: '/spread', label: '价差交易', icon: GitCompare },
    { path: '/analytics', label: '高级分析', icon: LineChart },
    { path: '/portfolio-opt', label: '组合优化', icon: SlidersHorizontal },
    { path: '/settings', label: '设置', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-bg-primary">
      <header className="sticky top-0 z-50 bg-bg-secondary/95 backdrop-blur-md border-b border-border">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-blue flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gradient">QuantMon</h1>
                <p className="text-xs text-text-muted">Quantitative Trading Monitor</p>
              </div>
            </div>

            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path ||
                  (item.path !== '/' && location.pathname.startsWith(item.path));
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`
                      px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                      flex items-center gap-2
                      ${isActive
                        ? 'bg-accent-blue/20 text-accent-cyan-light border border-accent-blue/30'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                      }
                    `}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </header>

      <main className="p-6">
        {children}
      </main>
    </div>
  );
}
