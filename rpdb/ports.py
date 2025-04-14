import socket


def is_port_in_use(host, port):
    """Check if a port is in use by attempting to connect to it.

    This is less intrusive than binding to the port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)  # Short timeout for quick check
        try:
            # If connect succeeds, port is in use
            s.connect((host, port))
            return True
        except socket.error:
            # Connection refused means port is available
            return False


def find_available_port(host, start_port, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(host, port):
            return port
    raise RuntimeError(
        f"No available ports found after {max_attempts} attempts starting from {start_port}"
    )
