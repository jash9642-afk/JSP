import { useState } from 'react';
import { Download, ChevronDown, ChevronUp, FileSpreadsheet, FileText, FileDown, AlertCircle, CheckCircle2 } from 'lucide-react';
import { pixllApi } from '../api';

function DataView({ title, subtitle, data, profile, sessionId, isCleaned, cleaningReport }) {
    const [isExpanded, setIsExpanded] = useState(true);
    const [isExporting, setIsExporting] = useState(false);
    const [exportFormat, setExportFormat] = useState('csv');
    const [showExportMenu, setShowExportMenu] = useState(false);

    const columns = data.length > 0 ? Object.keys(data[0]) : [];

    const handleExport = async (format) => {
        setIsExporting(true);
        setShowExportMenu(false);

        try {
            const response = await pixllApi.exportData(sessionId, format, isCleaned);

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `data_${isCleaned ? 'cleaned' : 'original'}.${format}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Export failed:', err);
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="glass-card overflow-hidden">
            {/* Header */}
            <div
                className="flex items-center justify-between p-4 border-b border-white/5 cursor-pointer hover:bg-dark-800/30 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3">
                    {isCleaned ? (
                        <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
                            <CheckCircle2 className="w-5 h-5 text-green-400" />
                        </div>
                    ) : (
                        <div className="w-10 h-10 rounded-xl bg-dark-800/50 flex items-center justify-center">
                            <FileSpreadsheet className="w-5 h-5 text-dark-400" />
                        </div>
                    )}
                    <div>
                        <h3 className="font-semibold text-white">{title}</h3>
                        <p className="text-xs text-dark-400">{subtitle}</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {/* Export Dropdown */}
                    <div className="relative">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setShowExportMenu(!showExportMenu);
                            }}
                            disabled={isExporting}
                            className="btn-secondary py-2 px-3 text-sm flex items-center gap-2"
                        >
                            <Download className="w-4 h-4" />
                            <span className="hidden sm:inline">Export</span>
                        </button>

                        {showExportMenu && (
                            <div className="absolute right-0 mt-2 w-40 glass-card rounded-lg py-2 z-10 shadow-xl">
                                {[
                                    { format: 'csv', icon: FileText, label: 'CSV' },
                                    { format: 'xlsx', icon: FileSpreadsheet, label: 'Excel' },
                                    { format: 'pdf', icon: FileDown, label: 'PDF Report' },
                                ].map((item) => (
                                    <button
                                        key={item.format}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleExport(item.format);
                                        }}
                                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-dark-300 hover:bg-dark-800/50 hover:text-white transition-colors"
                                    >
                                        <item.icon className="w-4 h-4" />
                                        {item.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Expand/Collapse */}
                    <button className="p-2 text-dark-400 hover:text-white transition-colors">
                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                </div>
            </div>

            {/* Profile Stats */}
            {profile && isExpanded && (
                <div className="grid grid-cols-3 gap-4 p-4 border-b border-white/5 bg-dark-800/20">
                    <div className="text-center">
                        <p className="text-2xl font-bold text-white">{profile.row_count.toLocaleString()}</p>
                        <p className="text-xs text-dark-400">Rows</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-white">{profile.column_count}</p>
                        <p className="text-xs text-dark-400">Columns</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-white">{profile.memory_usage_mb.toFixed(2)}</p>
                        <p className="text-xs text-dark-400">MB</p>
                    </div>
                </div>
            )}

            {/* Cleaning Summary */}
            {cleaningReport && isExpanded && (
                <div className="p-4 border-b border-white/5 bg-green-500/5">
                    <div className="flex items-center gap-2 mb-2">
                        <CheckCircle2 className="w-4 h-4 text-green-400" />
                        <span className="text-sm font-medium text-green-400">{cleaningReport.total_actions} cleaning actions performed</span>
                    </div>
                    {cleaningReport.issues_detected.length > 0 && (
                        <div className="text-xs text-dark-400">
                            Issues fixed: {cleaningReport.issues_detected.slice(0, 2).join(', ')}
                            {cleaningReport.issues_detected.length > 2 && ` +${cleaningReport.issues_detected.length - 2} more`}
                        </div>
                    )}
                </div>
            )}

            {/* Data Table */}
            {isExpanded && (
                <div className="overflow-x-auto max-h-96 overflow-y-auto">
                    {data.length > 0 ? (
                        <table className="data-table">
                            <thead className="sticky top-0">
                                <tr>
                                    {columns.map((col) => (
                                        <th key={col}>{col}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {data.map((row, i) => (
                                    <tr key={i}>
                                        {columns.map((col) => (
                                            <td key={col} className="max-w-xs truncate" title={String(row[col] ?? '')}>
                                                {row[col] === null || row[col] === undefined ? (
                                                    <span className="text-dark-500 italic">null</span>
                                                ) : (
                                                    String(row[col])
                                                )}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <div className="p-8 text-center text-dark-400">
                            No data to display
                        </div>
                    )}
                </div>
            )}

            {/* Footer */}
            {isExpanded && data.length > 0 && (
                <div className="p-3 border-t border-white/5 bg-dark-800/20">
                    <p className="text-xs text-dark-500 text-center">
                        Showing first {data.length} rows • Scroll for more columns
                    </p>
                </div>
            )}
        </div>
    );
}

export default DataView;
