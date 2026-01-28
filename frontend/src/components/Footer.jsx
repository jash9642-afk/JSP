import { Heart, Github, ExternalLink } from 'lucide-react';

function Footer() {
    return (
        <footer className="mt-auto py-6 border-t border-white/5">
            <div className="container mx-auto px-4 max-w-7xl">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                    {/* Left: Brand */}
                    <div className="flex items-center gap-2 text-dark-400 text-sm">
                        <span>Built with</span>
                        <Heart className="w-4 h-4 text-red-400 fill-current" />
                        <span>using AI</span>
                    </div>

                    {/* Center: Tech Stack */}
                    <div className="flex items-center gap-3 text-xs text-dark-500">
                        <span>React</span>
                        <span className="text-dark-700">•</span>
                        <span>FastAPI</span>
                        <span className="text-dark-700">•</span>
                        <span>LangChain</span>
                        <span className="text-dark-700">•</span>
                        <span>Plotly</span>
                    </div>

                    {/* Right: Links */}
                    <div className="flex items-center gap-4">
                        <a
                            href="https://pixll.tech"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-dark-400 hover:text-primary-400 transition-colors flex items-center gap-1 text-sm"
                        >
                            <ExternalLink className="w-4 h-4" />
                            <span>pixll.tech</span>
                        </a>
                    </div>
                </div>

                {/* Copyright */}
                <div className="text-center mt-4 text-xs text-dark-600">
                    © {new Date().getFullYear()} Pixll. AI-Powered Data Analysis Platform.
                </div>
            </div>
        </footer>
    );
}

export default Footer;
