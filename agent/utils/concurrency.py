
import asyncio

# Global semaphore to limit parallel LLM requests across all agents
# Reduced to 4 to avoid 500 INTERNAL errors on heavy image payloads.
SEM = asyncio.Semaphore(4)
