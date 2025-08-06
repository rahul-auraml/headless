import time
import threading
from simulation_manager import run_isaac_sim, shutdown, keep_alive, set_keep_running, start_simulation
from docker_manager import run_docker, check_image, stop_and_remove_container

# Configuration
USD_PATH = "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5/Isaac/Environments/Simple_Warehouse/warehouse.usd"  # Change this to your USD file path
TIMEOUT = 200  # Timeout for stage loading in seconds
ROBOT_IMAGE = "alpine:latest"  # Example robot image, change as needed

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
    
    # Start the simulation playback
    print("Starting simulation playback...")
    if start_simulation():
        print("Simulation is now running!")
    else:
        print("Failed to start simulation playback")
        return
    
    # Start the robot Docker container
    print(f"Starting robot container with image: {ROBOT_IMAGE}")
    robot_result = run_docker(
        image_name=ROBOT_IMAGE,
        name="robot_container",
        command="sleep 3600",  # Keep container alive for 1 hour
        detach=True,
        remove=False,
        environment={
            "SIMULATION_ACTIVE": "true",
            "USD_PATH": USD_PATH
        }
    )
    
    if robot_result["success"]:
        print(f"✅ Robot container started successfully!")
        print(f"   Container ID: {robot_result['output']}")
    else:
        print(f"❌ Failed to start robot container")
        print(f"   Error: {robot_result['error']}")
        # Continue with simulation even if robot container fails
    
    
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
    
    # Stop and remove robot container
    print("Stopping and removing robot container...")
    if stop_and_remove_container("robot_container"):
        print("✅ Robot container stopped and removed successfully")
    else:
        print("⚠️  Robot container may not have been running or failed to stop/remove")
    
    # Shutdown simulation
    shutdown()
    print("Simulation shutdown complete.")

if __name__ == "__main__":
    main()
