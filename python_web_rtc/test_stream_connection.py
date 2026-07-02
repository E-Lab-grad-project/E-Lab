"""
Test script to verify Raspberry Pi to Laptop connection
Run this on the LAPTOP FIRST, then start the Pi camera stream
"""

import cv2
import socket
import threading
import time
from datetime import datetime

def test_udp_stream():
    """Test receiving UDP stream from Raspberry Pi"""
    
    print("=" * 60)
    print("UDP STREAM TEST - Waiting for data on port 5000")
    print("=" * 60)
    print("\n📡 Make sure Raspberry Pi is streaming...")
    print("Run on Pi: python camera_stream_pi.py\n")
    
    # Try to capture from UDP stream using OpenCV
    pipeline = "udp://@:5000"
    
    print(f"Connecting to: {pipeline}")
    cap = cv2.VideoCapture(pipeline, cv2.CAP_FFMPEG)
    
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        print("❌ Failed to open UDP stream")
        return False
    
    print("✓ UDP stream opened!")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret or frame is None:
                print("❌ Failed to read frame")
                break
            
            frame_count += 1
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Display frame info every 10 frames
            if frame_count % 10 == 0:
                h, w = frame.shape[:2]
                print(f"✓ Frame {frame_count:4d} | {w}x{h} | FPS: {fps:.1f}")
            
            # Display frame
            cv2.imshow("Raspberry Pi Stream", frame)
            
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(f"Frames received: {frame_count}")
        print(f"Duration: {total_time:.1f}s")
        print(f"Average FPS: {avg_fps:.1f}")
        
        if frame_count > 0:
            print("✓ Connection successful!")
            return True
        else:
            print("❌ No frames received")
            return False


def test_network_connectivity():
    """Test if laptop can communicate with Pi network"""
    
    print("\n" + "=" * 60)
    print("NETWORK CONNECTIVITY CHECK")
    print("=" * 60)
    
    # Try to bind to port 5000
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 5000))
        print("✓ Port 5000 is available")
        sock.close()
    except OSError as e:
        print(f"❌ Port 5000 issue: {e}")
        return False
    
    # Get local IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"✓ Local IP: {local_ip}")
    except Exception as e:
        print(f"❌ Could not determine local IP: {e}")
    
    print("\nTo find Raspberry Pi IP:")
    print("  On Pi terminal: hostname -I")
    print("  Or check your router's connected devices")
    
    return True


if __name__ == "__main__":
    print("\n🔧 Raspberry Pi Stream Connectivity Test\n")
    
    # First check network
    if not test_network_connectivity():
        print("\n❌ Network check failed")
        exit(1)
    
    # Then test stream
    if test_udp_stream():
        print("\n✓ All tests passed! Your setup is working correctly.")
    else:
        print("\n❌ Stream test failed. Troubleshooting tips:")
        print("  1. Verify laptop IP in camera_stream_pi.py matches this machine")
        print("  2. Check firewall settings (allow UDP port 5000)")
        print("  3. Ensure Pi and laptop are on same network")
        print("  4. Try camera_stream_pi_simple.py if the main version fails")
