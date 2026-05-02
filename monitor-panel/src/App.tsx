import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { StrategyDetail } from './pages/StrategyDetail';
import { FactorAnalysis } from './pages/FactorAnalysis';
import { BacktestAnalysis } from './pages/BacktestAnalysis';
import { StrategyManagement } from './pages/StrategyManagement';
import { StockPool } from './pages/StockPool';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/strategy/:id" element={<StrategyDetail />} />
          <Route path="/factors" element={<FactorAnalysis />} />
          <Route path="/backtest" element={<BacktestAnalysis />} />
          <Route path="/strategies" element={<StrategyManagement />} />
          <Route path="/pool" element={<StockPool />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
