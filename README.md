# Hotel Price Scraper 🏨

A comprehensive Python tool for scraping hotel prices from Booking.com using Selenium WebDriver and Bright Data proxy service.

## 🌟 Features

- **Multi-Hotel Support**: Scrape single hotels or multiple hotels from a file
- **Date Range Scanning**: Automatically checks prices across multiple date ranges
- **Smart Retry System**: Retry only failed searches from existing results
- **Robust Error Handling**: Handles network issues, missing data, and WebDriver problems
- **JSON Output**: Well-structured JSON output with statistics and metadata
- **Professional Architecture**: Modular, maintainable, and extensible codebase

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Bright Data account with WebDriver credentials
- Chrome browser (for local testing)

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd hotel-prices-scrapper
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file with your Bright Data credentials:
   ```env
   BRIGHT_DATA_USERNAME=your_username
   BRIGHT_DATA_PASSWORD=your_password
   BRIGHT_DATA_HOST=your_host
   BRIGHT_DATA_PORT=your_port
   ```

### Basic Usage

```bash
# Scrape a single hotel
python main.py --hotel "Hotel Dann Carlton Bogotá"

# Scrape multiple hotels from file
python main.py --file hotel_names.txt

# Retry failed searches from existing JSON
python main.py --retry outputs/hotel_results_20241220_143022.json
```

## 📖 Detailed Usage

### Command Line Options

- `--hotel "Hotel Name"`: Scrape a single hotel by exact name
- `--file path/to/hotels.txt`: Scrape hotels listed in a text file (one per line)
- `--retry path/to/results.json`: Retry only failed searches from existing JSON output

### Hotel Names File Format

Create a text file with one hotel name per line:

```
Hotel Dann Carlton Bogotá
Hotel Tequendama
Hotel Casa Dann Carlton
```

### Example Commands

```bash
# Single hotel with exact name
python main.py --hotel "Hotel Dann Carlton Bogotá"

# Multiple hotels from file
python main.py --file hotel_names.txt

# Retry failed searches (smart retry)
python main.py --retry outputs/hotel_dann_carlton_bogota_20241220_143022.json

# Get help
python main.py --help
```

## 📊 Output Format

Results are saved as JSON files in the `outputs/` directory with timestamps:

### Single Hotel Output

```json
{
  "metadata": {
    "scrape_timestamp": "2024-12-20T14:30:22",
    "hotel_name": "Hotel Dann Carlton Bogotá",
    "total_searches": 3,
    "total_successful": 2,
    "overall_success_rate": 66.7
  },
  "hotel_name": "Hotel Dann Carlton Bogotá",
  "searches": [
    {
      "checkin_date": "2024-12-21",
      "checkout_date": "2024-12-22",
      "date_range": "2024-12-21 → 2024-12-22",
      "price": "COP 180,000",
      "availability": "Available",
      "error": null,
      "timestamp": "2024-12-20T14:30:22"
    }
  ],
  "summary": {
    "total_searches": 3,
    "successful_prices": 2,
    "not_available": 1,
    "errors": 0,
    "success_rate": 66.7,
    "min_price": 180000,
    "max_price": 220000,
    "avg_price": 200000
  }
}
```

## 🔧 Configuration

### Environment Variables

| Variable               | Description          | Required |
| ---------------------- | -------------------- | -------- |
| `BRIGHT_DATA_USERNAME` | Bright Data username | Yes      |
| `BRIGHT_DATA_PASSWORD` | Bright Data password | Yes      |
| `BRIGHT_DATA_HOST`     | Bright Data host     | Yes      |
| `BRIGHT_DATA_PORT`     | Bright Data port     | Yes      |

### Scraper Settings

Default settings can be modified in `src/utils/config.py`:

```python
{
    'max_searches_per_session': 6,      # Restart browser after N searches
    'page_load_timeout': 60,            # Page load timeout (seconds)
    'implicit_wait': 20,                # WebDriver implicit wait (seconds)
    'search_delay': 3,                  # Delay between searches (seconds)
    'hotel_delay': 10,                  # Delay between hotels (seconds)
    'session_restart_delay': 5,         # Delay when restarting browser (seconds)
    'country': 'co',                    # Country code for Booking.com
    'language': 'es-CO',                # Language preference
    'currency': 'COP'                   # Currency preference
}
```

## 🏗️ Project Structure

```
hotel-prices-scrapper/
├── main.py                     # Main entry point
├── main_old.py                 # Backup of original monolithic file
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── hotel_names.txt             # Sample hotel names file
├── outputs/                    # Generated JSON results
└── src/                        # Source code modules
    ├── cli/                    # Command line interface
    │   ├── __init__.py
    │   └── parser.py           # Argument parsing
    ├── scraper/                # Web scraping logic
    │   ├── __init__.py
    │   ├── driver.py           # WebDriver management
    │   ├── booking.py          # Booking.com interactions
    │   └── core.py             # Scraping orchestration
    ├── data/                   # Data handling
    │   ├── __init__.py
    │   ├── storage.py          # JSON operations
    │   └── retry.py            # Retry functionality
    └── utils/                  # Utilities
        ├── __init__.py
        ├── config.py           # Configuration management
        ├── dates.py            # Date calculations
        └── files.py            # File operations
```

## 🔄 Retry Functionality

The scraper includes intelligent retry functionality that can resume failed searches:

1. **Automatic Detection**: Identifies failed searches in existing JSON files
2. **Selective Retry**: Only re-scrapes the specific dates that failed
3. **In-Place Updates**: Updates the original JSON file with new results
4. **Data Preservation**: Maintains all successful results and metadata

### What Gets Retried

- Technical failures (network errors, timeouts)
- Search failures (hotel not found, date selection errors)
- Price extraction failures

### What Doesn't Get Retried

- Hotels genuinely not available for specific dates
- Successful price extractions

## 🛠️ Development

### Adding New Features

The modular architecture makes it easy to extend:

- **New scrapers**: Add modules in `src/scraper/`
- **New output formats**: Extend `src/data/storage.py`
- **New CLI options**: Modify `src/cli/parser.py`
- **New utilities**: Add to `src/utils/`

### Running Tests

```bash
# Future: Unit tests can be added for each module
python -m pytest tests/
```

### Code Structure

Each module follows the single responsibility principle:

- **CLI**: Handles command-line arguments only
- **Scraper**: Manages WebDriver and Booking.com interactions
- **Data**: Handles result storage and retry logic
- **Utils**: Provides shared utilities and configuration

## 🐛 Troubleshooting

### Common Issues

1. **Environment Variables Missing**:

   ```
   ❌ Missing required environment variables
   ```

   **Solution**: Ensure all Bright Data credentials are set in `.env`

2. **Hotel Not Found**:

   ```
   ❌ Hotel not found in autocomplete results
   ```

   **Solution**: Use exact hotel name as it appears on Booking.com

3. **WebSocket Errors**:
   ```
   🔌 WebSocket lost, restarting...
   ```
   **Solution**: The scraper automatically handles this by restarting the browser

### Debug Mode

For detailed logging, the scraper provides verbose output showing:

- Browser session status
- Search progress
- Error details
- Success/failure statistics

## 📈 Performance

- **Session Management**: Automatically restarts browser sessions to prevent memory leaks
- **Error Recovery**: Continues processing even if individual searches fail
- **Rate Limiting**: Built-in delays to respect Booking.com's servers
- **Efficient Retry**: Only re-processes failed searches, not successful ones

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is for educational and research purposes. Please respect Booking.com's terms of service and robots.txt when using this scraper.

## 🙏 Acknowledgments

- Built with Selenium WebDriver for reliable browser automation
- Uses Bright Data proxy service for robust web scraping
- Structured following Python best practices and PEP 8 guidelines

---

**Note**: This tool is designed for research and educational purposes. Always respect website terms of service and implement appropriate rate limiting when scraping web content.
