#!/usr/bin/env python3
import sys

def main():
    print("Replay Fixture Helper")
    print("---------------------")
    print("Since OpenAI webhooks require a valid signature using the real secret,")
    print("synthetic test payloads will be rejected with 401 Unauthorized unless signed.")
    print("To test the full flow and deduplication:")
    print("  1. Go to OpenAI Dashboard -> Webhooks")
    print("  2. Click 'Send test' on the configured endpoint.")
    print("  3. To test deduplication, click 'Send test' again for the same event.")
    print("  4. Monitor 'make webhook-logs' for 'Webhook accepted' and 'duplicate ignored'.")
    sys.exit(0)

if __name__ == "__main__":
    main()
