import { useState } from 'react';
import { Sparkles, Loader2, CheckCircle2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { pixllApi } from '../api';

function CleaningPanel({ sessionId, hasCleaned, cleaningReport, onCleaningComplete, setError, setIsLoading, isLoading }) {
    const [isCleaning, setIsCleaning] = useState(false);
    const [showDetails, setShowDetails] = useState(false);

    const handleClean = async () => {
        setIsCleaning(true);
        setError(null);

        try {
            const response = await pixllApi.cleanData(sessionId);
            onCleaningComplete(response.data.report, response.data.cleaned_preview);
        } catch (err) {
            setError(err.message || 'Cleaning failed');
        } finally {
            setIsCleaning(false);
        }
    };

    return (
        <div className="glass-card p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Left: Info */}
                <div className="flex items-start gap-4">
                    <div className={`
            w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0
            ${hasCleaned
                            ? 'bg-green-500/20'
                            : 'bg-gradient-to-br from-primary-500/20 to-purple-500/20'
                        }
          `}>
                        {hasCleaned ? (
                            <CheckCircle2 className="w-6 h-6 text-green-400" />
                        ) : (
                            <Sparkles className="w-6 h-6 text-primary-400" />
                        )}
                    </div>

                    <div>
                        <h2 className="text-lg font-semibold text-white mb-1">
                            {hasCleaned ? 'Data Cleaned Successfully' : 'AI Auto-Clean Agent'}
                        </h2>
                        <p className="text-sm text-dark-400">
                            {hasCleaned
                                ? `${cleaningReport?.total_actions || 0} cleaning actions performed on your data.`
                                : 'One-click intelligent data cleaning powered by AI. Handles missing values, fixes types, and standardizes formats.'
                            }
                        </p>
                    </div>
                </div>

                {/* Right: Action Button */}
                <div className="flex-shrink-0">
                    {!hasCleaned ? (
                        <button
                            onClick={handleClean}
                            disabled={isCleaning}
                            className="btn-primary flex items-center gap-2 min-w-[160px] justify-center"
                        >
                            {isCleaning ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    <span>Cleaning<span className="loading-dots"></span></span>
                                </>
                            ) : (
                                <>
                                    <Sparkles className="w-5 h-5" />
                                    <span>Auto-Clean Data</span>
                                </>
                            )}
                        </button>
                    ) : (
                        <button
                            onClick={handleClean}
                            disabled={isCleaning}
                            className="btn-secondary flex items-center gap-2"
                        >
                            {isCleaning ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    <span>Re-cleaning...</span>
                                </>
                            ) : (
                                <>
                                    <Sparkles className="w-5 h-5" />
                                    <span>Re-clean Data</span>
                                </>
                            )}
                        </button>
                    )}
                </div>
            </div>

            {/* Cleaning Report Details */}
            {cleaningReport && (
                <div className="mt-6 pt-6 border-t border-white/5">
                    <button
                        onClick={() => setShowDetails(!showDetails)}
                        className="flex items-center gap-2 text-sm text-dark-400 hover:text-white transition-colors"
                    >
                        {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        <span>View cleaning details</span>
                    </button>

                    {showDetails && (
                        <div className="mt-4 space-y-4">
                            {/* Stats */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="bg-dark-800/50 rounded-lg p-3 text-center">
                                    <p className="text-xl font-bold text-white">{cleaningReport.rows_before}</p>
                                    <p className="text-xs text-dark-400">Rows Before</p>
                                </div>
                                <div className="bg-dark-800/50 rounded-lg p-3 text-center">
                                    <p className="text-xl font-bold text-green-400">{cleaningReport.rows_after}</p>
                                    <p className="text-xs text-dark-400">Rows After</p>
                                </div>
                                <div className="bg-dark-800/50 rounded-lg p-3 text-center">
                                    <p className="text-xl font-bold text-white">{cleaningReport.columns_before}</p>
                                    <p className="text-xs text-dark-400">Cols Before</p>
                                </div>
                                <div className="bg-dark-800/50 rounded-lg p-3 text-center">
                                    <p className="text-xl font-bold text-green-400">{cleaningReport.columns_after}</p>
                                    <p className="text-xs text-dark-400">Cols After</p>
                                </div>
                            </div>

                            {/* Actions List */}
                            {cleaningReport.actions && cleaningReport.actions.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-medium text-white mb-2">Actions Performed</h4>
                                    <div className="space-y-2 max-h-48 overflow-y-auto">
                                        {cleaningReport.actions.map((action, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 bg-dark-800/30 rounded-lg">
                                                <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm text-white">
                                                        <span className="font-medium">{action.column}</span>
                                                        <span className="text-dark-400"> • {action.action.replace(/_/g, ' ')}</span>
                                                    </p>
                                                    <p className="text-xs text-dark-400 truncate">{action.details}</p>
                                                </div>
                                                <span className="text-xs text-dark-500">{action.rows_affected} rows</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Recommendations */}
                            {cleaningReport.recommendations && cleaningReport.recommendations.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-medium text-white mb-2">Recommendations</h4>
                                    <div className="space-y-2">
                                        {cleaningReport.recommendations.map((rec, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                                                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                                                <p className="text-sm text-dark-300">{rec}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default CleaningPanel;
