import { useState, useCallback } from 'react';
import Header from './components/Header';
import UploadZone from './components/UploadZone';
import DataView from './components/DataView';
import CleaningPanel from './components/CleaningPanel';
import ChatWithData from './components/ChatWithData';
import Footer from './components/Footer';

function App() {
    // Global state
    const [sessionId, setSessionId] = useState(null);
    const [uploadData, setUploadData] = useState(null);
    const [cleanedData, setCleanedData] = useState(null);
    const [cleaningReport, setCleaningReport] = useState(null);
    const [activeTab, setActiveTab] = useState('upload'); // upload, data, visualize
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Handle successful upload
    const handleUploadSuccess = useCallback((data) => {
        setSessionId(data.session_id);
        setUploadData(data);
        setCleanedData(null);
        setCleaningReport(null);
        setActiveTab('data');
        setError(null);
    }, []);

    // Handle cleaning complete
    const handleCleaningComplete = useCallback((report, cleanedPreview) => {
        setCleaningReport(report);
        setCleanedData(cleanedPreview);
    }, []);

    // Reset state
    const handleReset = useCallback(() => {
        setSessionId(null);
        setUploadData(null);
        setCleanedData(null);
        setCleaningReport(null);
        setActiveTab('upload');
        setError(null);
    }, []);

    return (
        <div className="min-h-screen flex flex-col">
            {/* Header */}
            <Header
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                hasData={!!sessionId}
                onReset={handleReset}
            />

            {/* Main Content */}
            <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
                {/* Error Display */}
                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
                        <p className="font-medium">Error</p>
                        <p className="text-sm mt-1">{error}</p>
                        <button
                            onClick={() => setError(null)}
                            className="mt-2 text-xs underline hover:no-underline"
                        >
                            Dismiss
                        </button>
                    </div>
                )}

                {/* Tab Content */}
                {activeTab === 'upload' && (
                    <UploadZone
                        onUploadSuccess={handleUploadSuccess}
                        setError={setError}
                        setIsLoading={setIsLoading}
                        isLoading={isLoading}
                    />
                )}

                {activeTab === 'data' && sessionId && (
                    <div className="space-y-6">
                        {/* Cleaning Panel */}
                        <CleaningPanel
                            sessionId={sessionId}
                            hasCleaned={!!cleanedData}
                            cleaningReport={cleaningReport}
                            onCleaningComplete={handleCleaningComplete}
                            setError={setError}
                            setIsLoading={setIsLoading}
                            isLoading={isLoading}
                        />

                        {/* Data Tables */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Original Data */}
                            <DataView
                                title="Original Data"
                                subtitle={uploadData?.filename}
                                data={uploadData?.preview || []}
                                profile={uploadData?.profile}
                                sessionId={sessionId}
                                isCleaned={false}
                            />

                            {/* Cleaned Data */}
                            {cleanedData && (
                                <DataView
                                    title="Cleaned Data"
                                    subtitle="AI-processed"
                                    data={cleanedData}
                                    sessionId={sessionId}
                                    isCleaned={true}
                                    cleaningReport={cleaningReport}
                                />
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'visualize' && sessionId && (
                    <ChatWithData
                        sessionId={sessionId}
                        hasCleaned={!!cleanedData}
                        setError={setError}
                    />
                )}

                {/* No Data State for non-upload tabs */}
                {activeTab !== 'upload' && !sessionId && (
                    <div className="glass-card p-12 text-center">
                        <div className="text-6xl mb-4">📊</div>
                        <h2 className="text-2xl font-semibold mb-2">No Data Loaded</h2>
                        <p className="text-dark-400 mb-6">
                            Upload a file first to start analyzing your data.
                        </p>
                        <button
                            onClick={() => setActiveTab('upload')}
                            className="btn-primary"
                        >
                            Go to Upload
                        </button>
                    </div>
                )}
            </main>

            {/* Footer */}
            <Footer />
        </div>
    );
}

export default App;
