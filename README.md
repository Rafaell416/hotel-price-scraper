# Hotel Prices Scraper

A Python-based web scraper for extracting hotel prices from Booking.com using Selenium and Bright Data's scraping browser infrastructure.

## 🚀 Features

- **Automated Hotel Search**: Search for specific hotels on Booking.com
- **Modal Handling**: Automatically detects and closes sign-in modals
- **Colombian Market Focus**: Configured for Colombian market with COP currency
- **Retry Mechanism**: Robust error handling with automatic retries
- **Screenshot Capture**: Takes screenshots for verification and debugging
- **Bright Data Integration**: Uses Bright Data's residential proxy network

## 🛠️ Prerequisites

- Python 3.7+
- Bright Data account with scraping browser access
- Virtual environment (recommended)

## 📦 Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd hotel-prices-scrapper
   ```

2. **Create and activate virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install selenium python-dotenv requests urllib3
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

### Browser Configuration

The scraper is configured with the following settings:

- **Country**: Colombia (`co`)
- **Language**: Spanish Colombia (`es-CO`)
- **Currency**: Colombian Peso (`COP`)
- **Session Management**: Automatic session handling
- **Timeouts**: 60-second page load timeout

## 🎯 Usage

### Basic Usage

Run the scraper to test modal handling:

```bash
python main.py
```

### Search for Specific Hotel

The scraper is currently configured to search for "Loft 32 Medellin Living". To modify the search term, update the `search_text` variable in the code:

```python
search_text = "Your Hotel Name Here"
```

### Example Output
