import asyncio
from pathlib import Path
from isaacsim import SimulationApp


class SimulationSetup:
    """Class that sets up and manages the Isaac Sim application."""
    
    def __init__(self, usd_path: str, headless: bool = False):
        self.usd_path = usd_path
        # SimulationApp MUST be initialized first before any other imports
        self.simulation_app = SimulationApp({"headless": headless})
        
        # Import Omniverse extensions AFTER SimulationApp initialization
        import carb.settings
        import carb.tokens
        import omni.kit.app
        import omni.usd
        
        # Store references for later use
        self.carb_settings = carb.settings
        self.carb_tokens = carb.tokens
        self.omni_kit_app = omni.kit.app
        self.omni_usd = omni.usd
        self.settings = carb.settings.get_settings()
        
    def setup_sync(self):
        """Initialize the simulation and load the USD stage synchronously."""
        print("Setting up simulation...")
        
        # Load the USD stage
        if self.usd_path and Path(self.usd_path).exists():
            self._open_stage_sync(self.usd_path)
        else:
            print(f"Warning: USD file not found at {self.usd_path}")
            print("Continuing with empty stage...")
        
        print("Simulation setup complete.")
        
    def start_simulation(self):
        """Start the simulation playback."""
        print("Starting simulation playback...")
        try:
            # Get the timeline interface to control playback
            import omni.timeline
            timeline = omni.timeline.get_timeline_interface()
            
            if timeline:
                timeline.play()
                print("Simulation playback started successfully")
                return True
            else:
                print("Failed to get timeline interface")
                return False
                
        except Exception as e:
            print(f"Error starting simulation: {e}")
            return False
        
    def _open_stage_sync(self, url: str):
        """Opens the provided USD stage synchronously."""
        print(f"Loading USD file: {url}")
        
        usd_context = self.omni_usd.get_context()
        
        try:
            # Open stage synchronously
            result = usd_context.open_stage(url)
            if result:
                print("USD stage loaded successfully")
                
                # Load render settings from stage
                if not bool(self.settings.get("/app/content/emptyStageOnStart")):
                    usd_context.load_render_settings_from_stage(
                        usd_context.get_stage_id()
                    )
            else:
                print("Failed to load USD stage")
                
        except Exception as e:
            print(f"Error loading USD stage: {e}")
            
    def keep_alive(self):
        """Keep the application running without blocking the event loop."""
        print("Application is running. Press Ctrl+C to exit.")
        
        # Instead of an async loop, just keep the app running
        # Isaac Sim will handle the event loop internally
        app = self.omni_kit_app.get_app()
        
        try:
            # This will run the application until shutdown
            while app.is_running():
                app.update()
        except KeyboardInterrupt:
            print("Application stopped by user")
        except Exception as e:
            print(f"Application error: {e}")
            
    def shutdown(self):
        """Shutdown the simulation application."""
        print("Shutting down simulation...")
        if self.simulation_app:
            self.simulation_app.close()


# Global reference to simulation setup for external control
_global_sim_setup = None
_keep_running = True

def set_keep_running(value):
    """Set the keep running flag from external control."""
    global _keep_running
    _keep_running = value

def keep_alive():
    """Keep the simulation running."""
    global _global_sim_setup, _keep_running
    if _global_sim_setup:
        try:
            while _keep_running and _global_sim_setup.omni_kit_app.get_app().is_running():
                _global_sim_setup.omni_kit_app.get_app().update()
        except Exception as e:
            print(f"Error in keep_alive: {e}")
    else:
        print("No simulation running.")


def run_isaac_sim(usd_path: str, headless: bool = False):
    """Main function to run Isaac Sim with the given USD file."""
    global _global_sim_setup
    
    _global_sim_setup = SimulationSetup(usd_path, headless)
    
    try:
        # Setup and load the USD stage synchronously
        _global_sim_setup.setup_sync()
        print("Isaac Sim setup complete. Ready for external control.")
        
        # Return control to caller (startup.py / Aura CI Manager)
        return _global_sim_setup
        
    except Exception as e:
        print(f"Error running application: {e}")
        if _global_sim_setup:
            _global_sim_setup.shutdown()
        return None


def shutdown():
    """Global shutdown function for external control."""
    global _global_sim_setup, _keep_running
    _keep_running = False
    if _global_sim_setup:
        _global_sim_setup.shutdown()
        _global_sim_setup = None
    else:
        print("No simulation to shutdown.")


def start_simulation():
    """Global function to start simulation playback."""
    global _global_sim_setup
    if _global_sim_setup:
        return _global_sim_setup.start_simulation()
    else:
        print("No simulation setup available to start.")
        return False


def keep_alive():
    """Keep the simulation running."""
    global _global_sim_setup, _keep_running
    if _global_sim_setup:
        try:
            while _keep_running and _global_sim_setup.omni_kit_app.get_app().is_running():
                _global_sim_setup.omni_kit_app.get_app().update()
        except Exception as e:
            print(f"Error in keep_alive: {e}")
    else:
        print("No simulation running.")
