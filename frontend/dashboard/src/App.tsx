import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Strategies } from './pages/Strategies';
import { Factors } from './pages/Factors';
import { Backtest } from './pages/Backtest';
import { StockPool } from './pages/StockPool';
import { StrategyDetail } from './pages/StrategyDetail';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/factors" element={<Factors />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/pool" element={<StockPool />} />
          <Route path="/strategy/:id" element={<StrategyDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
