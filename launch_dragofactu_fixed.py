#!/usr/bin/env python3
"""
DRAGOFACTU - Application Launcher
Configurable installation directory to keep repo clean
"""

import os
import sys
import subprocess
import sqlite3
import json
from pathlib import Path

# Default installation directory
DEFAULT_INSTALL_DIR = Path.home() / ".dragofactu"
CONFIG_FILE = Path.home() / ".dragofactu_config.json"
SCRIPT_DIR = Path(__file__).parent.resolve()


def load_config():
    """Load configuration from file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save config: {e}")


def get_install_directory():
    """Get or ask for installation directory"""
    config = load_config()

    if 'install_dir' in config:
        install_dir = Path(config['install_dir'])
        if install_dir.exists():
            return install_dir

    # First run - ask user
    print("\n" + "=" * 60)
    print("DRAGOFACTU - First Time Setup")
    print("=" * 60)
    print(f"\nDefault installation directory: {DEFAULT_INSTALL_DIR}")
    print("This is where virtual environment and data will be stored.")
    print("(The source code stays in the current directory)\n")

    while True:
        response = input(f"Use default location? [Y/n/custom path]: ").strip()

        if response.lower() in ('', 'y', 'yes', 's', 'si'):
            install_dir = DEFAULT_INSTALL_DIR
            break
        elif response.lower() in ('n', 'no'):
            custom_path = input("Enter custom path: ").strip()
            if custom_path:
                install_dir = Path(custom_path).expanduser().resolve()
                break
            else:
                print("Invalid path. Using default.")
                install_dir = DEFAULT_INSTALL_DIR
                break
        else:
            # Treat as custom path
            install_dir = Path(response).expanduser().resolve()
            break

    # Create directory structure
    install_dir.mkdir(parents=True, exist_ok=True)
    (install_dir / "data").mkdir(exist_ok=True)
    (install_dir / "exports").mkdir(exist_ok=True)
    (install_dir / "attachments").mkdir(exist_ok=True)

    # Save config
    config['install_dir'] = str(install_dir)
    config['source_dir'] = str(SCRIPT_DIR)
    save_config(config)

    print(f"\n✅ Installation directory set to: {install_dir}")
    return install_dir


def setup_display_environment():
    """Setup display environment for remote/NX systems"""
    print("🖥️  Configuring display environment...")

    if sys.platform != 'darwin':
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        os.environ['QT_SCALE_FACTOR'] = '1'
        os.environ['QT_X11_NO_MITSHM'] = '1'
        os.environ['QT_QPA_PLATFORM'] = 'xcb'

        if not os.environ.get('DISPLAY'):
            os.environ['DISPLAY'] = ':0'

        print(f"   DISPLAY: {os.environ.get('DISPLAY')}")
        print("   ✅ Remote display configured (X11)")
    else:
        print("   🍎 macOS detected - using native Cocoa")


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print("✅ Python version compatible")


def setup_virtual_environment(install_dir):
    """Create virtual environment in install directory"""
    venv_path = install_dir / "venv"
    pip_path = venv_path / "bin" / "pip"

    if not venv_path.exists():
        print(f"🔧 Creating virtual environment in {venv_path}...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return None

    # Install/upgrade dependencies
    print("📦 Installing/updating dependencies...")
    requirements = [
        "PySide6>=6.5.0",
        "SQLAlchemy>=2.0.0",
        "psycopg2-binary>=2.8.0",
        "alembic>=1.12.0",
        "reportlab>=4.0.0",
        "pillow>=9.0.0",
        "bcrypt>=3.2.0",
        "python-dotenv>=1.0.0",
        "python-dateutil>=2.8.0",
        "jinja2>=3.0.0",
        "PyJWT>=2.0.0",
        "requests>=2.28.0",  # Required for API client
    ]

    try:
        subprocess.run([str(pip_path), "install", "--upgrade", "-q"] + requirements, check=True)
        print("✅ Dependencies installed")
        return venv_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return None


def initialize_database(install_dir, venv_path):
    """Initialize database in install directory"""
    db_path = install_dir / "data" / "dragofactu.db"
    python_path = venv_path / "bin" / "python"

    # Set environment variable for database location
    os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"

    # Check if database exists and has admin user
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?',
                          (os.getenv('DEFAULT_ADMIN_USERNAME', 'admin'),))
            admin_exists = cursor.fetchone()[0] > 0
            conn.close()

            if admin_exists:
                print(f"✅ Database ready: {db_path}")
                return True
        except (sqlite3.Error, Exception):
            pass

    print(f"🔧 Initializing database at {db_path}...")
    try:
        init_script = SCRIPT_DIR / "scripts" / "init_db.py"
        subprocess.run([str(python_path), str(init_script)],
                      cwd=str(SCRIPT_DIR), check=True)
        print("✅ Database initialized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


def launch_application(install_dir, venv_path):
    """Launch the application"""
    python_path = venv_path / "bin" / "python"

    entry_points = [
        SCRIPT_DIR / "dragofactu_complete.py",
        SCRIPT_DIR / "dragofactu" / "main.py",
        SCRIPT_DIR / "main.py",
    ]

    app_entry = None
    for entry in entry_points:
        if entry.exists():
            app_entry = entry
            print(f"✅ Using entry point: {entry.name}")
            break

    if not app_entry:
        print("❌ No application entry point found")
        return False

    print("\n🚀 Launching DRAGOFACTU...")
    print("=" * 60)

    try:
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['DATABASE_URL'] = f"sqlite:///{install_dir / 'data' / 'dragofactu.db'}"
        env['DRAGOFACTU_DATA_DIR'] = str(install_dir / "data")
        env['DRAGOFACTU_EXPORTS_DIR'] = str(install_dir / "exports")

        process = subprocess.Popen(
            [str(python_path), str(app_entry)],
            env=env,
            cwd=str(SCRIPT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        print("📱 Starting GUI application...")
        if sys.platform != 'darwin':
            print("   If window doesn't appear, check X11 forwarding")
        print("")

        import time
        start_time = time.time()
        timeout = 10

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                try:
                    output, _ = process.communicate(timeout=1)
                    if output:
                        print(f"Output: {output}")
                except:
                    pass
                return process.returncode == 0
            time.sleep(0.1)

        if process.poll() is None:
            print("✅ Application launched successfully!")
            print(f"   Data directory: {install_dir / 'data'}")
            return True
        else:
            print("❌ Application failed to start")
            return False

    except Exception as e:
        print(f"❌ Failed to launch: {e}")
        return False


def main():
    """Main launcher function"""
    print("🐲 DRAGOFACTU - Business Management System")
    print("=" * 60)

    # Get installation directory (asks on first run)
    install_dir = get_install_directory()

    # Setup display environment
    setup_display_environment()

    # Check Python version
    check_python_version()

    # Setup virtual environment
    venv_path = setup_virtual_environment(install_dir)
    if not venv_path:
        sys.exit(1)

    # Initialize database
    if not initialize_database(install_dir, venv_path):
        sys.exit(1)

    # Security warnings
    if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'your-secret-key-here':
        print("\n⚠️  WARNING: Using default SECRET_KEY")

    if not os.getenv('DEFAULT_ADMIN_PASSWORD'):
        print("⚠️  WARNING: Using default admin password")

    # Show credentials
    print(f"\n🔐 Login Credentials:")
    print(f"   Username: {os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')}")
    print(f"   Password: {os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')}")

    # Show paths
    print(f"\n📁 Paths:")
    print(f"   Source: {SCRIPT_DIR}")
    print(f"   Data:   {install_dir / 'data'}")
    print(f"   Venv:   {install_dir / 'venv'}")

    if not launch_application(install_dir, venv_path):
        sys.exit(1)


if __name__ == "__main__":
    main()
