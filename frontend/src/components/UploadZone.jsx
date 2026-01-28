import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileSpreadsheet, FileJson, FileText, Loader2, Sparkles } from 'lucide-react';
import { pixllApi } from '../api';

function UploadZone({ onUploadSuccess, setError, setIsLoading, isLoading }) {
    const onDrop = useCallback(async (acceptedFiles) => {
        if (acceptedFiles.length === 0) return;

        const file = acceptedFiles[0];
        setIsLoading(true);
        setError(null);

        try {
            const response = await pixllApi.upload(file);
            onUploadSuccess(response.data);
        } catch (err) {
            setError(err.message || 'Failed to upload file');
        } finally {
            setIsLoading(false);
        }
    }, [onUploadSuccess, setError, setIsLoading]);

    const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-excel': ['.xls'],
            'application/json': ['.json'],
        },
        maxFiles: 1,
        maxSize: 10 * 1024 * 1024, // 10MB
        disabled: isLoading,
    });

    const getFileIcon = (type) => {
        switch (type) {
            case 'csv': return <FileText className="w-8 h-8" />;
            case 'xlsx':
            case 'xls': return <FileSpreadsheet className="w-8 h-8" />;
            case 'json': return <FileJson className="w-8 h-8" />;
            default: return <Upload className="w-8 h-8" />;
        }
    };

    return (
        <div className="max-w-4xl mx-auto">
            {/* Hero Section */}
            <div className="text-center mb-12">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-sm mb-6">
                    <Sparkles className="w-4 h-4" />
                    <span>AI-Powered Data Analysis</span>
                </div>
                <h1 className="text-4xl md:text-5xl font-bold mb-4">
                    <span className="glow-text">Upload your data</span>
                </h1>
                <p className="text-xl text-dark-400 max-w-2xl mx-auto">
                    Drop your CSV, Excel, or JSON file and let AI clean, analyze, and visualize your data instantly.
                </p>
            </div>

            {/* Drop Zone */}
            <div
                {...getRootProps()}
                className={`
          glass-card p-12 cursor-pointer transition-all duration-300 group
          ${isDragActive && !isDragReject ? 'border-primary-500 bg-primary-500/10 scale-[1.02]' : ''}
          ${isDragReject ? 'border-red-500 bg-red-500/10' : ''}
          ${isLoading ? 'opacity-60 cursor-not-allowed' : 'hover:border-primary-500/50'}
        `}
            >
                <input {...getInputProps()} id="file-upload" />

                <div className="flex flex-col items-center text-center">
                    {isLoading ? (
                        <>
                            <Loader2 className="w-16 h-16 text-primary-500 animate-spin mb-6" />
                            <p className="text-xl font-semibold text-white">Processing your file<span className="loading-dots"></span></p>
                            <p className="text-dark-400 mt-2">Analyzing data structure and profiling columns</p>
                        </>
                    ) : (
                        <>
                            <div className={`
                w-20 h-20 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300
                ${isDragActive
                                    ? 'bg-primary-500/20 text-primary-400 scale-110'
                                    : 'bg-dark-800/50 text-dark-400 group-hover:bg-primary-500/10 group-hover:text-primary-400'
                                }
              `}>
                                <Upload className="w-10 h-10" />
                            </div>

                            <p className="text-xl font-semibold text-white mb-2">
                                {isDragActive ? 'Drop it here!' : 'Drag & drop your file here'}
                            </p>
                            <p className="text-dark-400 mb-6">or click to browse</p>

                            {/* Supported formats */}
                            <div className="flex flex-wrap justify-center gap-3">
                                {[
                                    { type: 'csv', label: 'CSV' },
                                    { type: 'xlsx', label: 'Excel' },
                                    { type: 'json', label: 'JSON' },
                                ].map((format) => (
                                    <div
                                        key={format.type}
                                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-dark-800/50 border border-white/5"
                                    >
                                        {getFileIcon(format.type)}
                                        <span className="text-sm text-dark-300">{format.label}</span>
                                    </div>
                                ))}
                            </div>

                            <p className="text-xs text-dark-500 mt-6">Maximum file size: 10MB</p>
                        </>
                    )}
                </div>
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
                {[
                    {
                        icon: '🧹',
                        title: 'AI Auto-Clean',
                        description: 'Intelligent data cleaning that handles missing values, fixes types, and standardizes formats.',
                    },
                    {
                        icon: '💬',
                        title: 'Chat with Data',
                        description: 'Ask questions in plain English and get instant visualizations.',
                    },
                    {
                        icon: '📊',
                        title: 'Export Anywhere',
                        description: 'Download cleaned data and charts as CSV, Excel, PDF, or PNG.',
                    },
                ].map((feature, i) => (
                    <div key={i} className="glass-card-hover p-6 text-center">
                        <div className="text-4xl mb-4">{feature.icon}</div>
                        <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                        <p className="text-sm text-dark-400">{feature.description}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default UploadZone;
