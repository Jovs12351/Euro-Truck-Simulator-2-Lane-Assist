# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ETS2LA (Euro Truck Simulator 2 Lane Assist) is a Python-based autonomous driving system for SCS Software's truck simulators (ETS2/ATS). The project uses computer vision, machine learning, and game telemetry to provide self-driving capabilities.

## Development Commands

### Running the Application
- `python main.py` - Main entry point, handles bootstrapping and error recovery
- `python main.py --dev` - Development mode (skips updates, enables dev features)
- `python main.py --local` - Run with local UI instead of remote mirrors
- `python main.py --no-ui` - Run backend only without opening the UI window
- `python main.py --no-console` - Close console after UI starts

### Dependencies and Updates
- `pip install -r requirements.txt` - Install Python dependencies
- `update.bat` - Update system (calls `python Updater/updater.py`)

### Development Flags
- `--dev` - Development mode (prevents updates, enables file watching)
- `--china` - China mode (uses .cn mirrors and region-specific features)
- `--high` - High priority mode for better performance

## Architecture Overview

### Core Application Flow
1. **main.py** - Bootstrap runner with admin check, dependency validation, and crash recovery
2. **ETS2LA/core.py** - Main application entry point that starts all services
3. **ETS2LA/variables.py** - Global configuration and runtime state

### Key Components

#### Backend Architecture
- **Plugin System** (`ETS2LA/Plugin/`) - Modular plugin architecture using multiprocessing
  - `ETS2LA/Plugin/classes/plugin.py` - Base plugin class with state management
  - `Plugins/` - Individual plugin implementations (AR, Map, Navigation, etc.)
- **Event System** (`ETS2LA/Events/`) - Event-driven architecture for game state changes
- **Handlers** (`ETS2LA/Handlers/`) - Core system handlers (controls, plugins, PyTorch, sounds)

#### Frontend Integration
- **Web Server** (`ETS2LA/Networking/Servers/webserver.py`) - FastAPI-based backend API
- **WebView Window** (`ETS2LA/Window/`) - PyWebView-based desktop application wrapper
- **Frontend Submodule** (`Interface/`) - Separate React/TypeScript frontend (auto-downloaded)

#### Game Integration
- **TruckSimAPI** (`Modules/TruckSimAPI/`) - Game telemetry integration via SDK
- **Screen Capture** (`Modules/ScreenCapture/`, `Modules/BetterScreenCapture/`) - Game video capture
- **SDK Controller** (`Modules/SDKController/`) - Direct game control interface

#### Computer Vision & AI
- **Camera Module** (`Modules/Camera/`) - Video processing and computer vision
- **Navigation Detection** (`Plugins/NavigationDetectionAI/`) - AI-based navigation sign recognition
- **Traffic Light Detection** (`Plugins/TrafficLightDetection/`) - Traffic signal recognition
- **End-to-End Driving** (`Plugins/End-To-End/`) - ML-based autonomous driving

#### User Interface Components
- **UI Framework** (`ETS2LA/UI/`) - Custom UI component system
- **Pages** (`Pages/`) - Application pages (settings, telemetry, plugins, etc.)
- **Controls** (`ETS2LA/Controls/`) - Input handling and control mapping

### Plugin Development
Plugins inherit from `ETS2LAPlugin` and run in separate processes:
- `description` - Plugin metadata and versioning
- `author` - Author information
- `state` - Persistent state shared with frontend
- `settings` - User-configurable plugin settings
- Message passing via multiprocessing queues

### Localization
- Translation files in `Translations/locales/` with gettext support
- `generate_translations.py` - Script to update translation files
- Multi-language UI support with regional modes (China-specific features)

## Important Development Notes

### Runtime Modes
- The application uses multiprocessing heavily - most plugins run in separate processes
- Main thread runs at 100fps (`time.sleep(0.01)`) handling UI commands and state
- Frontend can be local (development) or served from CDN mirrors
- Automatic mirror selection based on response times

### Game Integration Requirements
- Requires ETS2/ATS with compatible SDK plugin installed
- DLL files in `ETS2LA/Assets/DLLs/` for different game versions (1.53, 1.54, 1.55)
- Telemetry data extracted from game logs and memory

### Error Handling
- Comprehensive crash recovery system in main.py
- Exception queue for cross-process error handling
- Automatic restart/update mechanisms on crashes
- Development mode prevents automatic updates

### Performance Considerations
- High-performance screen capture using specialized libraries
- PyTorch/computer vision workloads run in separate processes
- Real-time game integration requires careful timing and resource management