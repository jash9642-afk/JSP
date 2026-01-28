# 🎨 Pixll - AI-Powered Data Analysis Platform

> Upload your data, let AI clean it, and generate visualizations using natural language.

![Pixll](https://img.shields.io/badge/Pixll-AI%20Data%20Analysis-6366f1?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![React](https://img.shields.io/badge/React-18.3-61dafb?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square)

## ✨ Features

- **📤 Smart Data Ingestion** - Drag-and-drop upload for CSV, Excel, and JSON files
- **🧹 AI Auto-Clean Agent** - Intelligent data cleaning powered by LangChain + GPT-4
  - Handle missing values (imputation based on context)
  - Standardize date formats automatically
  - Fix data type mismatches (currency strings → floats)
- **💬 Chat with Your Data** - Natural language to visualization
  - "Show me the top 5 products by sales"
  - "Compare revenue across regions"
  - "What's the trend over time?"
- **📊 Interactive Charts** - Plotly-powered visualizations (Bar, Line, Pie, Scatter)
- **📥 Export Anywhere** - Download cleaned data as CSV, Excel, or PDF
- **📸 Chart Snapshots** - Export visualizations as high-quality PNG or PDF

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API Key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start server
python main.py
# or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## 📁 Project Structure

```
pixll/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── requirements.txt     # Python dependencies
│   ├── routers/
│   │   ├── upload.py        # File upload endpoints
│   │   ├── clean.py         # Data cleaning endpoints
│   │   └── visualize.py     # Chart generation endpoints
│   ├── services/
│   │   ├── data_parser.py   # CSV/Excel/JSON parsing
│   │   ├── ai_cleaner.py    # LangChain cleaning agent
│   │   └── chart_engine.py  # NL-to-Plotly generator
│   └── models/
│       └── schemas.py       # Pydantic models
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main application
│   │   ├── api.js           # API client
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── UploadZone.jsx
│   │       ├── DataView.jsx
│   │       ├── CleaningPanel.jsx
│   │       ├── ChatWithData.jsx
│   │       └── Footer.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
└── .env.example
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload data file |
| `POST` | `/api/clean/{session_id}` | Run AI cleaning |
| `GET` | `/api/export/{session_id}/{format}` | Export data |
| `POST` | `/api/visualize` | Generate chart from query |
| `POST` | `/api/visualize/override` | Change chart type |
| `GET` | `/api/visualize/{session_id}/export/{format}` | Export chart |

## 🎨 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.10+ |
| AI/ML | LangChain, OpenAI GPT-4 |
| Visualization | Plotly.js, React-Plotly |
| Data | Pandas, NumPy, OpenPyXL |
| Export | ReportLab (PDF), XlsxWriter |

## 📝 Environment Variables

```env
OPENAI_API_KEY=sk-...              # Required: OpenAI API key
OPENAI_MODEL=gpt-4-turbo-preview   # Model to use
HOST=0.0.0.0                       # Server host
PORT=8000                          # Server port
MAX_FILE_SIZE_MB=10                # Max upload size
```

## 🔒 Notes

- Data is stored in-memory per session (not persisted)
- Each AI operation makes API calls to OpenAI (costs apply)
- For production, add Redis for session storage and rate limiting

## 📜 License

MIT License - Feel free to use for personal and commercial projects.

---

Built with ❤️ using AI | [pixll.tech](https://pixll.tech)
