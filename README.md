# Badminton League Auction System 🏸

A comprehensive auction management system built with Streamlit, featuring user authentication, player management, team budgets, and real-time auction updates.

## Features

### 🎯 Core Functionality
- **User Authentication**: Role-based access control (Admin, Auctioneer, Owner)
- **Player Management**: Add, view, and auction players
- **Team Management**: Track team rosters and budgets
- **Live Auctions**: Real-time auction updates with budget validation
- **Data Export**: Download player and team data as CSV

### 🛠️ Technical Features
- **SQLite Database**: Reliable local data storage
- **CSV Upload**: Bulk data upload functionality
- **Data Validation**: Comprehensive input validation
- **Error Handling**: Robust error handling and logging
- **Clean Architecture**: Modular code design following best practices

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd hpl-auction
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database** (optional - will be done automatically)
   ```bash
   python upload_data.py init
   ```

## Usage

## Quick Start

### Using Make (Recommended)
```bash
# Complete setup and run
make quick-start

# Or step by step
make setup          # Install dependencies and initialize database
make run            # Start the application
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/upload_data.py init

# Start application
streamlit run app.py
```

### Using Docker
```bash
# Build and run with Docker
make docker-build
make docker-run

# Or manually
docker build -t badminton-auction .
docker run -p 8501:8501 badminton-auction
```

### Default Login Credentials
- **Admin**: `admin` / `!hpl@Sumadhura`
- **Auctioneer**: `auctioneer` / `Naresh@123`
- **Owner**: `owner1` / `owner123` or `owner2` / `owner123`

## User Roles

### 🔑 Admin
- Full system access
- Can upload CSV data
- Can reset database
- Can manage all auctions

### 🎤 Auctioneer
- Can conduct auctions
- Can assign players to teams
- Can undo auctions
- Cannot manage system data

### 👥 Owner
- View-only access
- Can see team rosters
- Can view player lists
- Cannot modify auction data

## Data Management

### CSV Upload via Web Interface
1. Log in as Admin
2. Use the sidebar "Upload CSV Files" section
3. Upload files for Users, Teams, or Players

## Make Commands

The project includes a comprehensive Makefile with the following commands:

### Setup Commands
- `make setup` - Complete setup: install dependencies and initialize database
- `make install` - Install dependencies in virtual environment
- `make clean` - Clean up generated files and virtual environment

### Development Commands
- `make run` - Run the Streamlit application
- `make dev` - Run in development mode with auto-reload
- `make test` - Run tests
- `make lint` - Run linting checks
- `make format` - Format code with black and isort

### Database Commands
- `make init-db` - Initialize database with initial data
- `make reset-db` - Reset database (WARNING: Deletes all data)
- `make upload-users FILE=path/to/users.csv` - Upload users from CSV
- `make upload-players FILE=path/to/players.csv` - Upload players from CSV
- `make upload-teams FILE=path/to/teams.csv` - Upload teams from CSV
- `make backup-db` - Backup database file
- `make export-data` - Export all data to CSV files

### Quick Commands
- `make quick-start` - Quick start: setup and run the application
- `make quick-reset` - Quick reset: reset and reinitialize database
- `make help` - Show all available commands

### Docker Commands
- `make docker-build` - Build Docker image
- `make docker-run` - Run application in Docker container

Run `make help` to see all available commands with descriptions.

### CSV File Formats

#### users.csv
```csv
username,password,role
admin,!hpl@Sumadhura,admin
auctioneer,Naresh@123,auctioneer
owner1,owner123,owner
```

#### teams.csv
```csv
team_name
Team Alpha
Team Beta
Team Gamma
```

#### players.csv
```csv
name,base_price
John Doe,100000
Jane Smith,150000
Mike Johnson,120000
```

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password`: User password (plain text - consider hashing for production)
- `role`: User role (admin, auctioneer, owner)

### Teams Table
- `id`: Primary key
- `team_name`: Unique team name

### Players Table
- `id`: Primary key
- `name`: Player name
- `base_price`: Minimum auction price
- `owner`: Team that owns the player (nullable)
- `auction_price`: Final auction price (default: 0)

## Configuration

### Team Budget
- Default budget per team: ₹10,000,000
- Budget tracking is automatic
- Prevents overspending during auctions

### File Structure
```
hpl-auction/
├── Makefile                    # Build automation and common commands
├── Dockerfile                  # Docker container configuration
├── app.py                      # Main application entry point
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── README.md                   # This file
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── models.py           # Data models
│   │   ├── database.py         # Database operations
│   │   └── auth.py             # Authentication
│   ├── ui/                     # User interface components
│   │   ├── __init__.py
│   │   └── ui_manager.py       # Streamlit UI components
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       └── file_manager.py     # CSV upload utilities
│
├── config/                     # Configuration files
│   └── settings.py             # Application settings
│
├── scripts/                    # Utility scripts
│   ├── upload_data.py          # CLI data upload tool
│   └── run.sh                  # Application run script
│
├── tests/                      # Test files
│   └── test_auction.py         # Test suite
│
├── data/                       # Initial CSV data
│   ├── users.csv
│   ├── teams.csv
│   └── players.csv
│
├── assets/                     # Static assets
│   └── hbl.png                 # Logo image
│
└── exports/                    # Data export directory (auto-created)
```

## Development

### Code Structure
The application follows clean architecture principles:

- **Models**: Data structures and types
- **Database Layer**: All database operations
- **Authentication**: User management and sessions
- **File Management**: CSV upload and validation
- **UI Management**: Streamlit interface components
- **Main Application**: Application orchestration

### Logging
The application uses Python's built-in logging module. Logs include:
- Authentication events
- Database operations
- File upload activities
- Error conditions

### Error Handling
- Comprehensive exception handling
- User-friendly error messages
- Detailed error logging for debugging

## Troubleshooting

### Common Issues

1. **Login not working**
   - Ensure database is initialized: `python upload_data.py init`
   - Check if users.csv exists in data/ directory
   - Verify credentials match those in users.csv

2. **Database errors**
   - Reset database: `python upload_data.py reset`
   - Reload initial data: `python upload_data.py init`

3. **CSV upload failures**
   - Check CSV format matches expected schema
   - Ensure no duplicate entries
   - Verify required columns are present

4. **Module import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

### Logs Location
Application logs are displayed in the terminal where you run `streamlit run main.py`.

## Production Deployment

### Security Considerations
- Change default passwords before production
- Consider implementing password hashing
- Use environment variables for sensitive configuration
- Enable HTTPS for web deployment

### Performance Optimization
- Database indexes for large datasets
- Caching for frequently accessed data
- Connection pooling for high concurrency

## Contributing

1. Follow the existing code structure
2. Add comprehensive error handling
3. Include logging for significant operations
4. Update documentation for new features
5. Test thoroughly before deployment

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Contact the system administrator
