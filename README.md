# 🏥 Pharmacy Inventory Dashboard
 
Modern, interactive Streamlit dashboard for real-time pharmacy inventory monitoring.

## Deploy

#### Live Pharmo App available at 
<a href="https://pharmo.streamlit.app"><img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" width="300" alt="Streamlit App"></a>

## Features
 
✅ **Multi-Page Dashboard** - 8 interactive pages covering all aspects  
✅ **Dark/Light Theme** - Toggle between themes  
✅ **Real-time Data** - Connected to NeonDB PostgreSQL  
✅ **Interactive Charts** - Plotly visualizations with cross-filtering  
✅ **Responsive Design** - Works on all devices  
✅ **Advanced Analytics** - Customer churn, bundle analysis, ABC classification  
✅ **Export Capabilities** - Download data as CSV  
✅ **Alert System** - Notifications for critical events  
 
## Quick Start
 
### Prerequisites
- Python 3.8+
- PostgreSQL (NeonDB)
- Git
### Installation
 
1. **Clone and setup**
```bash
git clone <your-repo>
cd pharmacy-dashboard
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```
 
2. **Install dependencies**
```bash
pip install -r requirements.txt
```
 
3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your NeonDB credentials
```
 
4. **Run locally**
```bash
streamlit run app.py
```
 
Open browser: `http://localhost:8501`
 
### Deploy to Streamlit Cloud
 
1. Push code to GitHub
2. Go to https://share.streamlit.io
3. New app → Select repo & branch
4. Set main file: `app.py`
5. Add secrets (NEON_HOST, NEON_DATABASE, etc.)
6. Deploy ✅
## Project Structure
 
```
pharmacy-dashboard/
├── app.py                      # Main entry point
├── pages/                      # Multi-page apps
│   ├── 1_📊_Executive_Overview.py
│   ├── 2_📦_Reorder_Management.py
│   ├── 3_💰_Transactions_Revenue.py
│   ├── 4_💊_Drugs_Inventory.py
│   ├── 5_👥_Customers_Analysis.py
│   ├── 6_📈_ABC_Analysis.py
│   ├── 7_🔗_Bundle_Analysis.py
│   └── 8_⚙️_Settings.py
├── lib/                        # Utilities
│   ├── __init__.py
│   ├── theme.py               # Dark/light theme manager
│   ├── colors.py              # Color palettes for charts
│   ├── db.py                  # Database queries
│   ├── session_state.py       # State management
│   └── calculations.py        # Advanced calculations
├── .streamlit/
│   └── config.toml            # Streamlit config
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```
 
## Pages Overview
 
### 1. 📊 Executive Overview
- Monthly KPIs (revenue, profit, customers)
- Top 5 & Bottom 5 drugs by revenue
- Profit trend chart (90 days)
- Customer growth metrics
### 2. 📦 Reorder Management
- Real-time reorder alerts
- Supplier contact details
- Suggested reorder quantities
- Lead time information
### 3. 💰 Transactions & Revenue
- Monthly revenue chart
- Profit trends
- Daily transaction analysis
- Category-wise breakdown
### 4. 💊 Drugs Inventory
- Stock heatmap by category
- Search functionality
- Brand alternatives
- Stock status indicators
### 5. 👥 Customers Analysis
- Regular customers list
- Purchase frequency
- Spending patterns
- Churn metrics
### 6. 📈 ABC Analysis
- Revenue classification (A/B/C)
- Category metrics
- Inventory recommendations
- Strategic insights
### 7. 🔗 Bundle Analysis
- Frequently bought together
- Co-purchase patterns
- Recommendation engine
- Revenue opportunities
### 8. ⚙️ Settings
- Database connection status
- Admin panel
- User preferences
- System configuration
## Color Scheme
 
### Dark Theme (Default)
- Background: #0F1419
- Surface: #1E2329
- Primary: #FF6B6B (Red)
- Text: #E8E8E8
### Light Theme
- Background: #FFFFFF
- Surface: #F5F5F5
- Primary: #FF6B6B (Red)
- Text: #1F1F1F
## Data Sources
 
All data comes from NeonDB (PostgreSQL) which is populated by the ETL pipeline:
- `pharmacy-etl-pipeline/` (Extract-Transform-Load)
- Runs twice daily via GitHub Actions
- Generates synthetic + real data
## Usage Tips
 
**Interactive Features:**
- Hover over charts for details
- Zoom by selecting area
- Pan by dragging
- Click legend to toggle series
**Theme Toggle:**
- Use sidebar buttons (🌙 Dark / ☀️ Light)
- Theme persists in session
**Data Export:**
- Click table → Download CSV
- Use browser's print-to-PDF
## Performance
 
- Database caching: 5 minutes
- Page load: <2 seconds
- Auto-refresh: Every 5 minutes
- Supports 1000+ drugs
## Troubleshooting
 
**Can't connect to database?**
- Check NeonDB credentials in `.env`
- Verify IP whitelisting in NeonDB console
- Test connection: `python -c "from lib.db import DatabaseManager; DatabaseManager.test_connection()"`
**Charts not showing?**
- Clear cache: `streamlit cache clear`
- Refresh page: F5
- Check browser console for errors
**Slow performance?**
- Reduce time window in queries
- Disable browser extensions
- Use latest Streamlit version
## Development
 
### Add New Page
1. Create `pages/N_📋_Page_Name.py`
2. Use template from existing pages
3. Import utilities: `from lib.db import DatabaseManager`
4. Test locally before pushing
### Add New Chart Type
1. Edit relevant page
2. Import Plotly: `import plotly.graph_objects as go`
3. Create figure with theme colors
4. Use `ColorPalette.get_chart_colors()`
### Database Query
1. Add function in `lib/db.py`
2. Use `@st.cache_data(ttl=300)` decorator
3. Always close connection: `conn.close()`
4. Handle exceptions gracefully
## Support
 
📧 Email: support@pharmacy.com  
🐛 Issues: GitHub Issues  
💬 Discord: [Join our server]
 
## License
 
MIT License - See LICENSE file
 
## Authors
 
- **Shalini** - Product Owner & Dashboard Designer
- **Claude** - Development & Architecture
## Changelog
 
### v1.0.0 (2024)
- Initial release
- 8 pages with complete functionality
- Dark/light theme
- Real-time data sync
- Cross-filtering
- Advanced analytics
---
 
Made with ❤️ for pharmacy management
 
