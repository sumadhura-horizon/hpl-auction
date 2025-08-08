# HPL Auction System - PostgreSQL Setup Guide

## Quick Setup

### 🍎 macOS Development Setup (ONE COMMAND!)

```bash
make macos-setup
```

**If you encounter database connection errors after running macos-setup:**

```bash
make fix-postgres-auth
make init-db
make run
```

This will:
- Install PostgreSQL via Homebrew
- Setup database and user
- Create Python virtual environment
- Install all dependencies
- Initialize database with sample data

### 🐧 Ubuntu Server Setup (ONE COMMAND!)

```bash
make ubuntu-setup
```

This will:
- Install PostgreSQL and system dependencies
- Setup database and user
- Create Python virtual environment
- Install all dependencies
- Initialize database with sample data

## Manual Setup

If you prefer manual setup or need to troubleshoot:

### Prerequisites

#### macOS
```bash
# Install PostgreSQL
make -f Makefile.macos install-postgres

# Setup database
make -f Makefile.macos setup-postgres
```

#### Ubuntu/Debian
```bash
# Install system dependencies
make -f Makefile.ubuntu install-system-deps

# Setup database
make -f Makefile.ubuntu setup-postgres
```

### Application Setup
```bash
# Install Python dependencies
make install

# Initialize database
make init-db

# Start application
make run
```

## Database Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hpl_auction
DB_USER=postgres
DB_PASSWORD=postgres
```

### Manual Database Setup

If automatic setup fails:

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE hpl_auction;
ALTER USER postgres PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE hpl_auction TO postgres;
```

## Application Structure

### Enhanced Features

✅ **PostgreSQL Database** - Scalable, robust database backend  
✅ **Captain Assignment System** - Dedicated interface for captain selection  
✅ **Marquee Player Auction** - Special category with 10 lakh base price  
✅ **Budget Validation** - Smart max bid calculation ensuring minimum player requirements  
✅ **Observer Interface** - Real-time auction view for spectators  
✅ **Photo Support** - Player profile pictures with avatar fallback  

### Auction System Details

- **36 Total Players**: 4 Captains + 12 Marquee + 20 Regular
- **4 Teams**: 9 players each (1 captain + 8 others)  
- **₹1 Crore Budget** per team
- **Base Prices**: Captains (₹0), Marquee (₹10L), Regular (₹2L)

## Usage Commands

### Basic Operations
```bash
make help           # Show all available commands
make run            # Start the application
make clean          # Clean and restart fresh
make info           # Show system information
```

### Database Operations
```bash
make init-db        # Initialize with sample data
make reset-db       # Reset database (WARNING: Deletes all data!)
make test           # Test database connection
```

### PostgreSQL Management
```bash
# macOS (Homebrew)
make postgres-start
make postgres-stop
make postgres-status
make postgres-restart

# Ubuntu (systemd)
make postgres-start
make postgres-stop
make postgres-status
make postgres-restart
```

### Database Access
```bash
make db-connect     # Connect to database using psql
```

## Troubleshooting

### Common Issues

#### PostgreSQL Connection Failed (macOS)
```bash
# Fix authentication issues
make fix-postgres-auth

# Check if PostgreSQL is running
make postgres-status

# Start PostgreSQL service
make postgres-start

# Test database connection
make db-connect
```

#### GSSAPI/Kerberos Errors (macOS)
If you see errors like "Cannot find KDC for realm KERBEROS.MICROSOFTONLINE.COM":

```bash
# This is a known macOS issue with PostgreSQL authentication
# Run the fix command:
make fix-postgres-auth

# Then retry setup:
make init-db
```

#### "role postgres does not exist" Error
```bash
# Create the postgres user and database
make fix-postgres-auth

# Verify connection
psql -d hpl_auction -c '\dt'
```

#### Permission Errors (Ubuntu)
```bash
# Ubuntu: Make sure PostgreSQL user has proper permissions
sudo -u postgres psql -c "ALTER USER postgres CREATEDB;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hpl_auction TO postgres;"
```

#### Import Errors
```bash
# Install missing dependencies
make clean
make install
```

### Verify Installation

After successful setup, verify everything works:

```bash
# Check database tables
psql -d hpl_auction -c '\dt'

# Check player data
psql -d hpl_auction -c 'SELECT category, COUNT(*) FROM players GROUP BY category;'

# Test application
make test

# Start application
make run
```

### Platform-Specific Help

#### macOS
```bash
make -f Makefile.macos help
```

#### Ubuntu
```bash
make -f Makefile.ubuntu help
```

## Production Deployment (Ubuntu)

### Create System Service
```bash
make -f Makefile.ubuntu create-service

# Start service
sudo systemctl start hpl-auction
sudo systemctl enable hpl-auction
```

### Setup Firewall
```bash
make -f Makefile.ubuntu setup-firewall
```

### Production Run
```bash
make -f Makefile.ubuntu run-production
```

## Default Credentials

- **Username**: admin
- **Password**: admin

## Application URLs

- **Local Development**: http://localhost:8501
- **Production**: http://YOUR_SERVER_IP:8501

## File Structure

```
hpl-auction/
├── Makefile                # Platform dispatcher
├── Makefile.macos         # macOS-specific setup
├── Makefile.ubuntu        # Ubuntu-specific setup
├── .env.example           # Environment configuration template
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies (includes psycopg2)
├── src/core/database.py   # PostgreSQL database manager
├── data/                  # Sample CSV data files
└── scripts/               # Database initialization scripts
```

---

**🏸 Ready to run your badminton league auction with PostgreSQL!**