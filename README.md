# Hotel Prices Scraper

A Python-based web scraper for extracting hotel prices from Booking.com using Selenium and Bright Data's scraping browser infrastructure. The scraper targets the Colombian market and focuses on Medellín hotels with enhanced connection stability and reliability.

## 🚀 Features

- **Multi-Hotel Processing**: Process multiple hotels from configuration files
- **Date Range Scraping**: Automatically scrapes prices for 30-day date ranges
- **Enhanced Modal Handling**: Automatically detects and closes sign-in and promotional modals
- **Colombian Market Focus**: Configured for Colombian market with COP currency
- **Advanced Error Recovery**: Robust connection handling with automatic session recreation
- **Connection Health Monitoring**: Real-time connection health checks and recovery
- **Enhanced Text Input**: Improved search field handling with multiple clearing methods
- **Smart Session Management**: Optimized browser session lifecycle to prevent connection issues
- **Comprehensive Logging**: Detailed progress tracking with emoji-based status indicators
- **CSV Output Format**: Results exported in multiple CSV formats for easy analysis
- **Bright Data Integration**: Uses Bright Data's residential proxy network with retry logic

## 🛠️ Prerequisites

- Python 3.7+
- Bright Data account with scraping browser access
- Stable internet connection
- Virtual environment (recommended)

## 📦 Installation

1. **Clone the repository**:

   ```bash
   git clone <git@github.com:Rafaell416/hotel-price-scraper.git>
   cd hotel-prices-scrapper
   ```

2. **Create and activate virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   BRIGHT_DATA_USERNAME=your_username
   BRIGHT_DATA_PASSWORD=your_password
   BRIGHT_DATA_HOST=your_host
   BRIGHT_DATA_PORT=your_port
   ```

## 🔧 Configuration

### Bright Data Setup

1. Sign up for a [Bright Data](https://brightdata.com) account
2. Create a scraping browser zone
3. Get your credentials from the Bright Data dashboard
4. Add credentials to your `.env` file

### Hotel Configuration

Create a `hotel_names.txt` file in the project root with one hotel name per line:

```txt
Loft Apartamentos Lleras
Apartamento loft medellin by Casa Lucca
Loft Exclusivo en La Candelaria
Venecia Loft Hotel
Energy Living - Ultimate Condo in Medellin
```

### Browser Configuration

The scraper includes enhanced configurations:

- **Country**: Colombia (`co`)
- **Language**: Spanish Colombia (`es-CO`)
- **Currency**: Colombian Peso (`COP`)
- **Session Management**: Smart session recreation every 4 searches
- **Connection Recovery**: Automatic retry with exponential backoff
- **Health Monitoring**: Real-time connection health checks
- **Timeouts**: 60-second page load timeout with DNS resolution optimization

## 🎯 Usage

### Basic Usage

Run the scraper to process all configured hotels:

```bash
python main.py
```

### Understanding the Output

The scraper provides detailed logging with emoji indicators:

- 🔍 **Searching**: Looking for elements or performing searches
- 🏨 **Hotel**: Hotel-related operations
- 📅 **Dates**: Date selection operations
- 💰 **Price**: Price extraction
- ✅ **Success**: Successful operations
- ❌ **Error**: Failed operations
- 🔄 **Retry**: Retry attempts
- 🔌 **Connection**: Connection status updates
- 🧹 **Reset**: Search field reset operations

## 📊 Output Files

The scraper generates **two CSV files** with timestamped filenames:

### 1. Main CSV (`hotel_prices_YYYYMMDD_HHMMSS.csv`)

**Matrix format** - Perfect for spreadsheet analysis and price comparison

```csv
Check-in Date,Check-out Date,Date Range,Loft Apartamentos Lleras,Apartamento loft medellin by Casa Lucca,Loft Exclusivo en La Candelaria
2025-07-07,2025-07-08,2025-07-07 → 2025-07-08,COP 178140,COP 250000,N/A
2025-07-08,2025-07-09,2025-07-08 → 2025-07-09,COP 185000,ERROR,COP 220000
2025-07-09,2025-07-10,2025-07-09 → 2025-07-10,N/A,COP 275000,COP 195000
```

**Structure:**

- **Rows**: Each date range (check-in → check-out)
- **Columns**: Hotels as separate columns
- **Values**:
  - `COP XXXXX` - Actual price found
  - `N/A` - Hotel not available for this date
  - `ERROR` - Technical error occurred
  - `NO DATA` - No search performed

### 2. Summary CSV (`hotel_summary_YYYYMMDD_HHMMSS.csv`)

**Statistics format** - Aggregated performance metrics per hotel

```csv
Hotel Name,Total Searches,Successful Prices,Not Available,Errors,Success Rate (%),Min Price (COP),Max Price (COP),Avg Price (COP),Price Range
Loft Apartamentos Lleras,31,15,12,4,48.4%,165000,285000,225000,165000 - 285000
Apartamento loft medellin by Casa Lucca,31,18,8,5,58.1%,180000,320000,245000,180000 - 320000
```

**Columns:**

- `Hotel Name`: Full hotel name
- `Total Searches`: Total number of date searches performed
- `Successful Prices`: Number of successful price extractions
- `Not Available`: Number of dates where hotel was not available
- `Errors`: Number of technical errors
- `Success Rate (%)`: Percentage of successful price extractions
- `Min Price (COP)`: Lowest price found
- `Max Price (COP)`: Highest price found
- `Avg Price (COP)`: Average price across all successful searches
- `Price Range`: Min - Max price range

## 📈 Data Analysis

### Excel/Google Sheets Analysis

1. **Main CSV**: Open in Excel for quick price comparison across hotels and dates
2. **Summary CSV**: Perfect for hotel performance comparison

### Example Analysis Queries

- **Best Price Days**: Filter Main CSV to find lowest prices across all hotels
- **Hotel Availability**: Use Summary CSV to compare success rates
- **Price Trends**: Sort Main CSV by date to identify pricing patterns
- **Performance Analysis**: Use Summary CSV to compare hotel success rates

## 🔄 Error Handling & Recovery

### Enhanced Search Reliability

The scraper includes advanced search field management:

- **Complete Field Reset**: Aggressive clearing of accumulated search state
- **Multiple Search Attempts**: Up to 3 attempts per hotel search with different strategies
- **JavaScript-Based Input**: Reliable text input using DOM events
- **Autocomplete Recovery**: Smart waiting and triggering of autocomplete results
- **Consecutive Failure Detection**: Automatic session restart on repeated failures

### Connection Issues

The scraper includes advanced connection management:

- **Automatic Retry**: Up to 3 attempts for failed connections
- **Health Checks**: Connection validation before each operation
- **Session Recreation**: Smart session restart on connection failures
- **Exponential Backoff**: Progressive delay between retry attempts

### Common Issues & Solutions

1. **Text Input Problems**:

   - Enhanced clearing with multiple methods
   - JavaScript-based text input as fallback
   - Complete field reset between searches

2. **Autocomplete Failures**:

   - Multiple autocomplete triggering strategies
   - Flexible partial matching
   - Debug output for troubleshooting

3. **Connection Timeouts**:
   - Automatic session recreation
   - Consecutive failure detection
   - Reduced session length to prevent degradation

## 📊 Performance Optimization

- **Session Lifecycle**: Maximum 4 searches per session to prevent state accumulation
- **Random Delays**: Randomized wait times to avoid rate limiting
- **Enhanced Error Recovery**: Proactive session management
- **Memory Management**: Proper driver cleanup and resource management

## 🐛 Troubleshooting

### Analyzing Results

1. **Low Success Rate**: Check Summary CSV for error patterns
2. **Specific Hotel Issues**: Filter Detailed CSV by hotel name
3. **Date-Specific Problems**: Use Main CSV to identify problematic date ranges
4. **Connection Issues**: Look for "ERROR" status in Detailed CSV

### Debug Information

The scraper automatically provides:

- Available autocomplete options when hotel search fails
- Detailed error messages with specific failure points
- Connection health status updates
- Search field reset confirmations

## 💡 Tips for Better Results

1. **Hotel Names**: Use exact names as they appear on Booking.com
2. **Internet Stability**: Ensure stable connection for best results
3. **Rate Limiting**: The scraper includes built-in delays - don't modify them
4. **Batch Processing**: Process hotels in smaller batches if experiencing issues

## 🔒 Security & Best Practices

- Keep your `.env` file secure and never commit it to version control
- Use stable internet connection for best results
- Monitor Bright Data usage to stay within your plan limits
- The scraper includes built-in rate limiting to respect website policies

## 📈 Expected Performance

With stable internet and proper configuration:

- **Success Rate**: 75-90% for available hotels
- **Processing Speed**: ~2-3 minutes per hotel (31 dates)
- **Data Quality**: Accurate prices in COP currency
- **Error Recovery**: Automatic handling of 90%+ of common issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add appropriate tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

### 📋 Quick Start Checklist

- [ ] Install Python 3.7+
- [ ] Set up virtual environment
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Create `.env` file with Bright Data credentials
- [ ] Create `hotel_names.txt` with your hotel list
- [ ] Run `python main.py`
- [ ] Check generated CSV files for results
- [ ] Analyze data in Excel/Google Sheets
