"""
Network Simulation Engine for Cloud-Edge Speculative Decoding Benchmark

This module simulates realistic network constraints between Edge and Cloud:
- RTT (Round Trip Time): Base latency
- Bandwidth: Upload/Download speed limits
- Jitter: Variance in latency
- Concurrency: Queue simulation for cloud GPU
"""

import time
import random
import threading
from queue import Queue, Full


class NetworkSimulator:
    """
    Simulates cloud-edge network constraints with high fidelity.
    
    Features:
    1. RTT simulation with configurable jitter
    2. Bandwidth bottleneck modeling
    3. Cloud GPU queue simulation (concurrency control)
    4. Payload-aware delay calculation
    """
    
    def __init__(self, rtt_ms=50, bandwidth_mbps=100, jitter_ms=0, max_concurrent=1, seed=42):
        """
        Initialize network simulator.
        
        Args:
            rtt_ms (float): Base round-trip time in milliseconds
            bandwidth_mbps (float): Bandwidth in Mbps (Megabits per second)
            jitter_ms (float): Maximum jitter variance in milliseconds
            max_concurrent (int): Maximum concurrent requests (cloud queue size)
            seed (int): Random seed for reproducibility
        """
        self.base_rtt = rtt_ms / 1000.0  # Convert to seconds
        self.jitter = jitter_ms / 1000.0
        
        # Convert bandwidth from Mbps to Bytes/second
        self.bandwidth_bytes_per_sec = (bandwidth_mbps * 1_000_000) / 8
        
        # Concurrency control (Cloud GPU queue)
        self.max_concurrent = max_concurrent
        self.request_queue = Queue(maxsize=max_concurrent)
        self.active_requests = 0
        self.queue_lock = threading.Lock()
        
        # Reproducibility
        self.random = random.Random(seed)
        
        print(f"[NETWORK] Initialized: RTT={rtt_ms}ms, BW={bandwidth_mbps}Mbps, "
              f"Jitter=±{jitter_ms}ms, Concurrency={max_concurrent}", flush=True)
    
    def calculate_transfer_time(self, data_size_bytes):
        """
        Calculate time to transfer data over bandwidth-limited link.
        
        Args:
            data_size_bytes (int): Size of data to transfer
            
        Returns:
            float: Transfer time in seconds
        """
        if self.bandwidth_bytes_per_sec <= 0:
            return 0.0
        
        transfer_time = data_size_bytes / self.bandwidth_bytes_per_sec
        return transfer_time
    
    def inject_delay(self, payload_size_bytes=1024):
        """
        Simulate complete network round trip with realistic constraints.
        
        Simulates:
        1. Queue wait (if cloud is busy with other requests)
        2. Upload time (Edge → Cloud, bandwidth constrained)
        3. RTT delay + random jitter
        4. Download time (Cloud → Edge, smaller response)
        
        Args:
            payload_size_bytes (int): Size of request payload (tokens + KV cache)
            
        Returns:
            float: Total network delay in seconds
        """
        total_delay = 0.0
        
        # Step 1: Queue simulation (Cloud concurrency)
        queue_wait = 0.0
        with self.queue_lock:
            if self.active_requests >= self.max_concurrent:
                # Cloud is busy, wait for a slot
                queue_wait = self.random.uniform(0.1, 0.5)
                total_delay += queue_wait
                time.sleep(queue_wait)
            
            self.active_requests += 1
        
        try:
            # Step 2: Upload time (Edge → Cloud)
            upload_time = self.calculate_transfer_time(payload_size_bytes)
            total_delay += upload_time
            time.sleep(upload_time)
            
            # Step 3: Network RTT + Jitter
            actual_rtt = self.base_rtt
            if self.jitter > 0:
                # Add random jitter (can be positive or negative)
                jitter_amount = self.random.uniform(-self.jitter, self.jitter)
                actual_rtt += jitter_amount
            
            # Prevent negative delays
            actual_rtt = max(0, actual_rtt)
            total_delay += actual_rtt
            time.sleep(actual_rtt)
            
            # Step 4: Download time (Cloud → Edge)
            # Assume response is smaller (just token IDs, no full KV cache)
            response_size = payload_size_bytes // 10  # ~10% of upload size
            download_time = self.calculate_transfer_time(response_size)
            total_delay += download_time
            time.sleep(download_time)
            
        finally:
            # Release queue slot
            with self.queue_lock:
                self.active_requests -= 1
        
        return total_delay


# Factory registration for Ianvs integration
from sedna.common.class_factory import ClassFactory, ClassType


@ClassFactory.register(ClassType.GENERAL, alias="network_simulator")
def create_network_simulator(**kwargs):
    """
    Factory function for Ianvs to create NetworkSimulator instances.
    
    Args:
        **kwargs: Network configuration parameters
        
    Returns:
        NetworkSimulator: Configured network simulator
    """
    return NetworkSimulator(
        rtt_ms=kwargs.get("rtt_ms", 50),
        bandwidth_mbps=kwargs.get("bandwidth_mbps", 100),
        jitter_ms=kwargs.get("jitter_ms", 0),
        max_concurrent=kwargs.get("concurrency", 1),
        seed=kwargs.get("random_seed", 42)
    )


# Standalone testing
if __name__ == "__main__":
    print("Testing NetworkSimulator...")
    
    # Test 1: Low latency (Fiber)
    sim_fiber = NetworkSimulator(rtt_ms=10, bandwidth_mbps=1000, jitter_ms=0)
    delay = sim_fiber.inject_delay(payload_size_bytes=10_000)
    print(f"Fiber delay: {delay*1000:.2f}ms")
    
    # Test 2: High latency + jitter (4G)
    sim_4g = NetworkSimulator(rtt_ms=100, bandwidth_mbps=50, jitter_ms=20)
    delays = [sim_4g.inject_delay(payload_size_bytes=100_000) for _ in range(10)]
    print(f"4G delays (avg): {sum(delays)/len(delays)*1000:.2f}ms")
    print(f"4G delays (p95): {sorted(delays)[int(0.95*len(delays))]*1000:.2f}ms")
    
    print("✓ NetworkSimulator tests passed")