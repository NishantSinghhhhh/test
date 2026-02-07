"""
Network Profiler: Measures real RTT, bandwidth, jitter
Runs before hybrid benchmark to characterize the actual network
"""

import requests
import time
import statistics
import json

class NetworkProfiler:
    def __init__(self, cloud_url, num_samples=10):
        self.cloud_url = cloud_url.rstrip('/')
        self.num_samples = num_samples
    
    def measure_rtt(self):
        """Measure actual round-trip time"""
        print("\n[PROFILE] Measuring RTT...")
        rtts = []
        
        for i in range(self.num_samples):
            try:
                start = time.time()
                response = requests.get(f"{self.cloud_url}/health", timeout=10)
                rtt = (time.time() - start) * 1000  # ms
                
                if response.status_code == 200:
                    rtts.append(rtt)
                    print(f"  Sample {i+1}: {rtt:.2f}ms")
            except Exception as e:
                print(f"  Sample {i+1}: FAILED - {e}")
        
        if rtts:
            return {
                "avg_rtt_ms": statistics.mean(rtts),
                "min_rtt_ms": min(rtts),
                "max_rtt_ms": max(rtts),
                "jitter_ms": statistics.stdev(rtts) if len(rtts) > 1 else 0,
                "samples": len(rtts)
            }
        return None
    
    def measure_bandwidth(self, payload_sizes=[1024, 10240, 102400]):
        """Estimate effective bandwidth"""
        print("\n[PROFILE] Measuring Bandwidth...")
        bandwidth_results = []
        
        for size in payload_sizes:
            dummy_tokens = list(range(size // 4))  # 4 bytes per token
            payload = {"tokens": dummy_tokens, "original_len": 0}
            
            try:
                start = time.time()
                response = requests.post(
                    f"{self.cloud_url}/verify",
                    json=payload,
                    timeout=30
                )
                duration = time.time() - start
                
                if response.status_code == 200:
                    # Estimate bandwidth (upload + download)
                    data_size_kb = (len(json.dumps(payload)) + len(response.text)) / 1024
                    bandwidth_kbps = (data_size_kb * 8) / duration  # kbps
                    
                    bandwidth_results.append({
                        "payload_kb": data_size_kb,
                        "bandwidth_kbps": bandwidth_kbps
                    })
                    print(f"  Payload: {data_size_kb:.1f}KB → {bandwidth_kbps:.1f} kbps")
            except Exception as e:
                print(f"  Payload {size} bytes: FAILED - {e}")
        
        if bandwidth_results:
            avg_bw = statistics.mean([r["bandwidth_kbps"] for r in bandwidth_results])
            return {
                "avg_bandwidth_kbps": avg_bw,
                "avg_bandwidth_mbps": avg_bw / 1000,
                "measurements": bandwidth_results
            }
        return None
    
    def profile(self):
        """Run complete network profile"""
        print("="*60)
        print("Network Profiling")
        print(f"Target: {self.cloud_url}")
        print("="*60)
        
        profile = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cloud_url": self.cloud_url
        }
        
        # Measure RTT
        rtt_data = self.measure_rtt()
        if rtt_data:
            profile.update(rtt_data)
        
        # Measure Bandwidth
        bw_data = self.measure_bandwidth()
        if bw_data:
            profile.update(bw_data)
        
        print("\n" + "="*60)
        print("Network Profile Summary:")
        print(f"  Average RTT: {profile.get('avg_rtt_ms', 'N/A'):.2f} ms")
        print(f"  Jitter: {profile.get('jitter_ms', 'N/A'):.2f} ms")
        print(f"  Bandwidth: {profile.get('avg_bandwidth_mbps', 'N/A'):.2f} Mbps")
        print("="*60)
        
        # Save to file
        with open("network_profile.json", "w") as f:
            json.dump(profile, f, indent=2)
        print("\n✓ Profile saved to network_profile.json")
        
        return profile


if __name__ == "__main__":
    profiler = NetworkProfiler("http://127.0.0.1:5000")
    profiler.profile()