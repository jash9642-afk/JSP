import { useState, useRef, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { Send, Loader2, BarChart3, LineChart, PieChart, ScatterChart, Download, Image, FileText, Lightbulb, Sparkles } from 'lucide-react';
import { pixllApi } from '../api';

const CHART_TYPES = [
    { value: 'bar', label: 'Bar', icon: BarChart3 },
    { value: 'line', label: 'Line', icon: LineChart },
    { value: 'pie', label: 'Pie', icon: PieChart },
    { value: 'scatter', label: 'Scatter', icon: ScatterChart },
    { value: 'histogram', label: 'Histogram', icon: BarChart3 },
];

const EXAMPLE_QUERIES = [
    "Show me the top 5 items by value",
    "Compare categories as a bar chart",
    "Show the distribution of values",
    "What's the trend over time?",
];

function ChatWithData({ sessionId, hasCleaned, setError }) {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [chartData, setChartData] = useState(null);
    const [chartType, setChartType] = useState('bar');
    const [explanation, setExplanation] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [history, setHistory] = useState([]);
    const inputRef = useRef(null);

    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const handleSubmit = async (e) => {
        e?.preventDefault();
        if (!query.trim() || isLoading) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await pixllApi.visualize(sessionId, query.trim());
            const data = response.data;

            setChartData(data.plotly_figure);
            setChartType(data.chart_type);
            setExplanation(data.explanation);
            setSuggestions(data.suggested_queries || []);

            // Add to history
            setHistory(prev => [...prev, { query: query.trim(), chartType: data.chart_type }]);
            setQuery('');
        } catch (err) {
            setError(err.message || 'Failed to generate visualization');
        } finally {
            setIsLoading(false);
        }
    };

    const handleChartTypeChange = async (newType) => {
        if (newType === chartType || !chartData) return;

        setIsLoading(true);
        try {
            const response = await pixllApi.overrideChartType(sessionId, newType);
            setChartData(response.data.plotly_figure);
            setChartType(response.data.chart_type);
            setExplanation(response.data.explanation);
        } catch (err) {
            setError(err.message || 'Failed to change chart type');
        } finally {
            setIsLoading(false);
        }
    };

    const handleExportChart = async (format) => {
        try {
            const response = await pixllApi.exportChart(sessionId, format);

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `pixll_chart.${format}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            setError(`Export failed: ${err.message}`);
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setQuery(suggestion);
        inputRef.current?.focus();
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="glass-card p-6">
                <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center">
                        <Sparkles className="w-6 h-6 text-primary-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-white">Chat with Your Data</h2>
                        <p className="text-sm text-dark-400">
                            Ask questions in plain English and get instant visualizations
                            {!hasCleaned && <span className="text-amber-400 ml-1">(Using original data)</span>}
                        </p>
                    </div>
                </div>

                {/* Query Input */}
                <form onSubmit={handleSubmit} className="relative">
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g., Show me the top 5 products by revenue..."
                        className="input-field pr-14"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!query.trim() || isLoading}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-primary-500 text-white hover:bg-primary-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Send className="w-5 h-5" />
                        )}
                    </button>
                </form>

                {/* Example Queries */}
                {!chartData && (
                    <div className="mt-4">
                        <p className="text-xs text-dark-500 mb-2">Try these examples:</p>
                        <div className="flex flex-wrap gap-2">
                            {EXAMPLE_QUERIES.map((example, i) => (
                                <button
                                    key={i}
                                    onClick={() => handleSuggestionClick(example)}
                                    className="px-3 py-1.5 text-xs bg-dark-800/50 border border-white/5 rounded-lg text-dark-400 hover:text-white hover:border-primary-500/30 transition-all"
                                >
                                    {example}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Chart Display */}
            {chartData && (
                <div className="glass-card p-6">
                    {/* Chart Controls */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                        {/* Chart Type Selector */}
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-dark-400">Chart Type:</span>
                            <div className="flex gap-1">
                                {CHART_TYPES.map((type) => {
                                    const Icon = type.icon;
                                    const isActive = chartType === type.value;
                                    return (
                                        <button
                                            key={type.value}
                                            onClick={() => handleChartTypeChange(type.value)}
                                            disabled={isLoading}
                                            className={`
                        p-2 rounded-lg transition-all flex items-center gap-1.5
                        ${isActive
                                                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                                                    : 'text-dark-400 hover:text-white hover:bg-dark-800/50 border border-transparent'
                                                }
                        disabled:opacity-50
                      `}
                                            title={type.label}
                                        >
                                            <Icon className="w-4 h-4" />
                                            <span className="text-xs hidden sm:inline">{type.label}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Export Options */}
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-dark-400">Export:</span>
                            <button
                                onClick={() => handleExportChart('png')}
                                className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
                            >
                                <Image className="w-4 h-4" />
                                PNG
                            </button>
                            <button
                                onClick={() => handleExportChart('pdf')}
                                className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
                            >
                                <FileText className="w-4 h-4" />
                                PDF
                            </button>
                        </div>
                    </div>

                    {/* Plotly Chart */}
                    <div className="plotly-chart-container bg-dark-900/50 rounded-xl p-4">
                        {isLoading ? (
                            <div className="h-96 flex items-center justify-center">
                                <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
                            </div>
                        ) : (
                            <Plot
                                data={chartData.data}
                                layout={{
                                    ...chartData.layout,
                                    autosize: true,
                                    height: 400,
                                }}
                                config={{
                                    responsive: true,
                                    displayModeBar: true,
                                    displaylogo: false,
                                    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                                }}
                                style={{ width: '100%', height: '400px' }}
                            />
                        )}
                    </div>

                    {/* Explanation */}
                    {explanation && (
                        <div className="mt-4 p-4 bg-dark-800/30 rounded-lg border border-white/5">
                            <p className="text-sm text-dark-300">{explanation}</p>
                        </div>
                    )}

                    {/* Suggested Follow-ups */}
                    {suggestions.length > 0 && (
                        <div className="mt-4">
                            <div className="flex items-center gap-2 text-sm text-dark-400 mb-2">
                                <Lightbulb className="w-4 h-4" />
                                <span>Try asking:</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {suggestions.map((suggestion, i) => (
                                    <button
                                        key={i}
                                        onClick={() => handleSuggestionClick(suggestion)}
                                        className="px-3 py-1.5 text-xs bg-primary-500/10 border border-primary-500/20 rounded-lg text-primary-400 hover:bg-primary-500/20 transition-all"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Query History */}
            {history.length > 0 && (
                <div className="glass-card p-4">
                    <h3 className="text-sm font-medium text-dark-400 mb-3">Recent Queries</h3>
                    <div className="flex flex-wrap gap-2">
                        {history.slice(-5).reverse().map((item, i) => (
                            <button
                                key={i}
                                onClick={() => handleSuggestionClick(item.query)}
                                className="px-3 py-1.5 text-xs bg-dark-800/50 border border-white/5 rounded-lg text-dark-400 hover:text-white transition-all truncate max-w-xs"
                            >
                                {item.query}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default ChatWithData;
