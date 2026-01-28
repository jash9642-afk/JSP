import { Sparkles, Database, BarChart3, Upload, RefreshCw } from 'lucide-react';

const navItems = [
    { id: 'upload', label: 'Upload', icon: Upload },
    { id: 'data', label: 'Data', icon: Database },
    { id: 'visualize', label: 'Visualize', icon: BarChart3 },
];

function Header({ activeTab, setActiveTab, hasData, onReset }) {
    return (
        <header className="sticky top-0 z-50 glass-card rounded-none border-x-0 border-t-0">
            <div className="container mx-auto px-4 py-4 max-w-7xl">
                <div className="flex items-center justify-between">
                    {/* Logo */}
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
                            <Sparkles className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold glow-text">Pixll</h1>
                            <p className="text-xs text-dark-400">AI Data Analysis</p>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex items-center gap-2">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = activeTab === item.id;
                            const isDisabled = item.id !== 'upload' && !hasData;

                            return (
                                <button
                                    key={item.id}
                                    onClick={() => !isDisabled && setActiveTab(item.id)}
                                    disabled={isDisabled}
                                    className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-300
                    ${isActive
                                            ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                                            : 'text-dark-400 hover:text-white hover:bg-dark-800/50'
                                        }
                    ${isDisabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                                >
                                    <Icon className="w-4 h-4" />
                                    <span className="hidden sm:inline">{item.label}</span>
                                </button>
                            );
                        })}

                        {/* Reset Button */}
                        {hasData && (
                            <button
                                onClick={onReset}
                                className="ml-2 p-2 rounded-lg text-dark-400 hover:text-white hover:bg-dark-800/50 transition-all"
                                title="Start Over"
                            >
                                <RefreshCw className="w-5 h-5" />
                            </button>
                        )}
                    </nav>
                </div>
            </div>
        </header>
    );
}

export default Header;
