import socket
import json
import os
import threading
import time
import signal
import sys

# Initialize high scores
high_scores = []
SCORES_FILE = "high_scores.json"
clients = []
running = True

def load_scores():
    global high_scores
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, 'r') as f:
            high_scores = json.load(f)
    return high_scores

def save_scores():
    with open(SCORES_FILE, 'w') as f:
        json.dump(high_scores, f)

def broadcast_scores():
    """Send current scores to all connected clients"""
    message = json.dumps({"type": "scores", "data": high_scores})
    for client in clients[:]:  # Create a copy of the list to safely iterate
        try:
            client.send(message.encode())
        except:
            if client in clients:
                clients.remove(client)

def handle_client(client_socket):
    """Handle individual client connections"""
    while running:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            message = json.loads(data)
            if message["type"] == "new_score":
                new_score = message["score"]
                high_scores.append(new_score)
                high_scores.sort(reverse=True)
                high_scores[:] = high_scores[:5]  # Keep only top 5 scores
                save_scores()
                broadcast_scores()

        except:
            break

    if client_socket in clients:
        clients.remove(client_socket)
    try:
        client_socket.close()
    except:
        pass

def cleanup():
    """Clean up resources before shutting down"""
    global running
    running = False
    
    print("\nShutting down server...")
    print("Closing client connections...")
    
    # Close all client connections
    for client in clients[:]:
        try:
            client.close()
        except:
            pass
    clients.clear()
    
    # Save final scores
    save_scores()
    print("Scores saved.")
    print("Server shutdown complete.")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal...")
    cleanup()
    sys.exit(0)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', 5000))
        server.listen(5)
        print("Server started on port 5000")
        print("Press Ctrl+C to stop the server")

        # Load initial scores
        load_scores()

        while running:
            try:
                server.settimeout(1)  # Set timeout to check running status
                client_socket, address = server.accept()
                print(f"New connection from {address}")
                clients.append(client_socket)
                
                # Send current scores to new client
                message = json.dumps({"type": "scores", "data": high_scores})
                client_socket.send(message.encode())
                
                # Start new thread to handle client
                client_thread = threading.Thread(target=handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                continue
            except:
                if running:  # Only print error if we're still running
                    print("Error accepting connection")
                break

    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.close()
        cleanup()

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received...")
        cleanup()
        sys.exit(0)
