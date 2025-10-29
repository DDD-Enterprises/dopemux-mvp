#!/usr/bin/env python3
"""
Test Redis consumer - reads events from the stream
"""

import redis
import json
import sys

def consume_events(count=10):
    """Read last N events from Redis stream"""
    r = redis.from_url("redis://localhost:6379", decode_responses=True)
    
    # Read events
    events = r.xrange("conport:events", count=count)
    
    if not events:
        print("❌ No events found in stream")
        return
    
    print(f"📬 Found {len(events)} event(s) in Redis stream:\n")
    
    for event_id, event_data in events:
        print(f"Event ID: {event_id}")
        print(f"  Type: {event_data.get('type')}")
        print(f"  Source: {event_data.get('source')}")
        print(f"  Timestamp: {event_data.get('timestamp')}")
        
        # Parse data
        data = json.loads(event_data.get('data', '{}'))
        print(f"  Decision ID: {data.get('id')}")
        print(f"  Summary: {data.get('summary')}")
        print(f"  Rationale: {data.get('rationale', 'N/A')[:80]}")
        
        if data.get('tags'):
            try:
                tags = json.loads(data.get('tags'))
                print(f"  Tags: {', '.join(tags)}")
            except:
                pass
        
        print()
    
    r.close()

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    consume_events(count)
