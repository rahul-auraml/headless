import subprocess
import json
import logging
from typing import Dict, List, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerManager:
    """
    Docker Manager class to handle Docker operations like checking images and running containers.
    """
    
    def __init__(self):
        """Initialize Docker Manager and check if Docker is available."""
        self.docker_available = self._check_docker_availability()
        if not self.docker_available:
            logger.error("Docker is not available on this system")
    
    def _check_docker_availability(self) -> bool:
        """Check if Docker is installed and running."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Docker is available: {result.stdout.strip()}")
                return True
            else:
                logger.error("Docker command failed")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Docker not found or not responding: {e}")
            return False
    
    def check_image(self, image_name: str) -> bool:
        """
        Check if a Docker image exists locally.
        
        Args:
            image_name (str): Name of the Docker image (e.g., 'ubuntu:20.04')
            
        Returns:
            bool: True if image exists locally, False otherwise
        """
        if not self.docker_available:
            logger.error("Docker is not available")
            return False
        
        try:
            result = subprocess.run(
                ["docker", "images", "-q", image_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"Image '{image_name}' found locally")
                return True
            else:
                logger.info(f"Image '{image_name}' not found locally")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout checking image '{image_name}'")
            return False
        except Exception as e:
            logger.error(f"Error checking image '{image_name}': {e}")
            return False
    
    def pull_image(self, image_name: str) -> bool:
        """
        Pull a Docker image from registry.
        
        Args:
            image_name (str): Name of the Docker image to pull
            
        Returns:
            bool: True if pull successful, False otherwise
        """
        if not self.docker_available:
            logger.error("Docker is not available")
            return False
        
        try:
            logger.info(f"Pulling image '{image_name}'...")
            result = subprocess.run(
                ["docker", "pull", image_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout for pulling
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully pulled image '{image_name}'")
                return True
            else:
                logger.error(f"Failed to pull image '{image_name}': {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout pulling image '{image_name}'")
            return False
        except Exception as e:
            logger.error(f"Error pulling image '{image_name}': {e}")
            return False
    
    def run_docker(
        self,
        image_name: str,
        command: Optional[str] = None,
        volumes: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, str]] = None,
        environment: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
        detach: bool = False,
        remove: bool = True,
        interactive: bool = False,
        tty: bool = False,
        working_dir: Optional[str] = None,
        user: Optional[str] = None,
        network: Optional[str] = None,
        extra_args: Optional[List[str]] = None
    ) -> Dict[str, Union[bool, str, int]]:
        """
        Run a Docker container with specified parameters.
        
        Args:
            image_name (str): Docker image to run
            command (str, optional): Command to run in container
            volumes (dict, optional): Volume mappings {host_path: container_path}
            ports (dict, optional): Port mappings {host_port: container_port}
            environment (dict, optional): Environment variables {key: value}
            name (str, optional): Container name
            detach (bool): Run container in background
            remove (bool): Remove container after it stops
            interactive (bool): Keep STDIN open
            tty (bool): Allocate a pseudo-TTY
            working_dir (str, optional): Working directory in container
            user (str, optional): User to run as
            network (str, optional): Network to connect to
            extra_args (list, optional): Additional docker run arguments
            
        Returns:
            dict: Result containing success status, output, error, and return code
        """
        if not self.docker_available:
            logger.error("Docker is not available")
            return {
                "success": False,
                "output": "",
                "error": "Docker is not available",
                "return_code": -1
            }
        
        # Check if image exists locally, pull if not
        if not self.check_image(image_name):
            logger.info(f"Image '{image_name}' not found locally, attempting to pull...")
            if not self.pull_image(image_name):
                return {
                    "success": False,
                    "output": "",
                    "error": f"Failed to pull image '{image_name}'",
                    "return_code": -1
                }
        
        # Build docker run command
        cmd = ["docker", "run"]
        
        # Add flags
        if detach:
            cmd.append("-d")
        if remove:
            cmd.append("--rm")
        if interactive:
            cmd.append("-i")
        if tty:
            cmd.append("-t")
        
        # Add name
        if name:
            cmd.extend(["--name", name])
        
        # Add volumes
        if volumes:
            for host_path, container_path in volumes.items():
                cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        # Add ports
        if ports:
            for host_port, container_port in ports.items():
                cmd.extend(["-p", f"{host_port}:{container_port}"])
        
        # Add environment variables
        if environment:
            for key, value in environment.items():
                cmd.extend(["-e", f"{key}={value}"])
        
        # Add working directory
        if working_dir:
            cmd.extend(["-w", working_dir])
        
        # Add user
        if user:
            cmd.extend(["-u", user])
        
        # Add network
        if network:
            cmd.extend(["--network", network])
        
        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        # Add image name
        cmd.append(image_name)
        
        # Add command
        if command:
            if isinstance(command, str):
                cmd.extend(command.split())
            elif isinstance(command, list):
                cmd.extend(command)
        
        # Execute the command
        try:
            logger.info(f"Running Docker container: {' '.join(cmd)}")
            
            if detach:
                # For detached containers, don't wait for completion
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip(),
                    "return_code": result.returncode
                }
            else:
                # For non-detached containers, capture output
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr,
                    "return_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout running container '{image_name}'"
            logger.error(error_msg)
            return {
                "success": False,
                "output": "",
                "error": error_msg,
                "return_code": -1
            }
        except Exception as e:
            error_msg = f"Error running container '{image_name}': {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "output": "",
                "error": error_msg,
                "return_code": -1
            }
    
    def list_containers(self, all_containers: bool = False) -> List[Dict]:
        """
        List Docker containers.
        
        Args:
            all_containers (bool): List all containers (including stopped ones)
            
        Returns:
            list: List of container information dictionaries
        """
        if not self.docker_available:
            logger.error("Docker is not available")
            return []
        
        try:
            cmd = ["docker", "ps", "--format", "json"]
            if all_containers:
                cmd.append("-a")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        containers.append(json.loads(line))
                return containers
            else:
                logger.error(f"Failed to list containers: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []
    
    def stop_container(self, container_id: str) -> bool:
        """
        Stop a running Docker container.
        
        Args:
            container_id (str): Container ID or name
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.docker_available:
            logger.error("Docker is not available")
            return False
        
        try:
            result = subprocess.run(
                ["docker", "stop", container_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully stopped container '{container_id}'")
                return True
            else:
                logger.error(f"Failed to stop container '{container_id}': {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping container '{container_id}': {e}")
            return False


# Global Docker manager instance
_docker_manager = None

def get_docker_manager() -> DockerManager:
    """Get the global Docker manager instance."""
    global _docker_manager
    if _docker_manager is None:
        _docker_manager = DockerManager()
    return _docker_manager

# Convenience functions for external use
def check_image(image_name: str) -> bool:
    """Check if a Docker image exists locally."""
    return get_docker_manager().check_image(image_name)

def run_docker(
    image_name: str,
    command: Optional[str] = None,
    **kwargs
) -> Dict[str, Union[bool, str, int]]:
    """Run a Docker container with specified parameters."""
    return get_docker_manager().run_docker(image_name, command, **kwargs)

def pull_image(image_name: str) -> bool:
    """Pull a Docker image from registry."""
    return get_docker_manager().pull_image(image_name)

def list_containers(all_containers: bool = False) -> List[Dict]:
    """List Docker containers."""
    return get_docker_manager().list_containers(all_containers)

def stop_container(container_id: str) -> bool:
    """Stop a running Docker container."""
    return get_docker_manager().stop_container(container_id)
