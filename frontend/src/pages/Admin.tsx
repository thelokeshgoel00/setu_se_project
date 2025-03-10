import { useState, useEffect } from 'react';
import { fetchAdminMetrics, MetricsData } from '../api/adminService';

const MetricTile = ({ title, value, bgColor }: { title: string; value: number; bgColor: string }) => (
  <div className={`${bgColor} rounded-lg shadow-md p-6 text-white`}>
    <h3 className="text-xl font-semibold mb-2">{title}</h3>
    <p className="text-3xl font-bold">{value}</p>
  </div>
);

const Admin = () => {
  const [metrics, setMetrics] = useState<MetricsData>({
    totalKycAttempted: 0,
    totalKycSuccessful: 0,
    totalKycFailed: 0,
    totalKycFailedDueToPan: 0,
    totalKycFailedDueToBankAccount: 0,
    totalKycFailedDueToBoth: 0,
    totalPanWithoutRpd: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noData, setNoData] = useState(false);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        setError(null);
        setNoData(false);
        
        // Fetch metrics from the backend API using the service
        const data = await fetchAdminMetrics();
        setMetrics(data);
        
        // Check if there's any data
        const hasData = Object.values(data).some(value => value > 0);
        setNoData(!hasData);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching metrics:', err);
        setError('Failed to load metrics data.');
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  const handleRefresh = () => {
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Admin Dashboard</h1>
        <button 
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          onClick={handleRefresh}
        >
          Refresh Data
        </button>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      
      {noData && !error && (
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">No Data:</strong>
          <span className="block sm:inline"> There is no KYC data available yet. Complete some KYC verifications to see metrics.</span>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <MetricTile 
          title="Total KYC Attempted" 
          value={metrics.totalKycAttempted} 
          bgColor="bg-blue-600" 
        />
        <MetricTile 
          title="Total KYC Successful" 
          value={metrics.totalKycSuccessful} 
          bgColor="bg-green-600" 
        />
        <MetricTile 
          title="Total KYC Failed" 
          value={metrics.totalKycFailed} 
          bgColor="bg-red-600" 
        />
        <MetricTile 
          title="Failed Due to PAN" 
          value={metrics.totalKycFailedDueToPan} 
          bgColor="bg-orange-600" 
        />
        <MetricTile 
          title="Failed Due to Bank Account" 
          value={metrics.totalKycFailedDueToBankAccount} 
          bgColor="bg-purple-600" 
        />
        <MetricTile 
          title="PAN without Bank Verification" 
          value={metrics.totalPanWithoutRpd} 
          bgColor="bg-indigo-600" 
        />
        {/*
        // THis metric makes no sense for now based on the flow.
        <MetricTile 
          title="Failed Due to Both" 
          value={metrics.totalKycFailedDueToBoth} 
          bgColor="bg-indigo-600" 
        /> */}
      </div>
    </div>
  );
};

export default Admin; 