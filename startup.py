import time
import threading
from simulation_manager import run_isaac_sim, shutdown, keep_alive, set_keep_running

# Configuration
USD_PATH = "/uploads/Collected_lift_demo/new_lift.usd"  # Change this to your USD file path
TIMEOUT = 200  # Timeout for stage loading in seconds

def timeout_monitor():
    """Background thread to monitor timeout"""
    print(f"Timeout monitor started. Will shutdown after {TIMEOUT} seconds...")
    time.sleep(TIMEOUT)
    
    print(f"Timeout reached ({TIMEOUT}s). Stopping simulation...")
    set_keep_running(False)
    shutdown()

def main():
    """Aura CI Manager - Controls the simulation lifecycle"""
    print("=== Aura CI Manager Starting ===")
    
    # Initialize and setup Isaac Sim
    print("Initializing Isaac Sim...")
    sim_setup = run_isaac_sim(USD_PATH, headless=False)
    
    if sim_setup is None:
        print("Failed to initialize simulation. Exiting.")
        return
    
    print("Simulation started with USD path:", USD_PATH)
    
    # Start timeout monitor in background thread
    timeout_thread = threading.Thread(target=timeout_monitor, daemon=True)
    timeout_thread.start()
    
    try:
        # Let Isaac Sim run its main loop uninterrupted
        # The timeout will be handled by the background thread
        keep_alive()
        
    except KeyboardInterrupt:
        print("Simulation interrupted by user")
        set_keep_running(False)
    
    # Ensure clean shutdown
    print("=== Aura CI Manager Shutting Down ===")
    shutdown()
    print("Simulation shutdown complete.")

if __name__ == "__main__":
    main()
