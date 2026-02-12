import asyncio
import os

from kagi_client import KagiClient


async def main() -> None:
    session = os.environ.get("KAGI_SESSION", "")
    if not session:
        print("Set KAGI_SESSION environment variable to your kagi_session cookie value")
        return

    async with KagiClient(kagi_session=session) as client:
        # Proofread
        result = await client.proofread("Ths is a tset of the proofreading API.")
        print(f"Proofread: {result.analysis and result.analysis.corrected_text}")

        # Summarize
        summary = await client.summarize("https://example.com")
        print(f"Summary: {summary.title}")

        # Assistant
        assistant = await client.prompt("What is 2+2?")
        print(f"Assistant: {assistant.message.md}")

        # Search
        search = await client.search("python async")
        print(f"Search: {search.info.next_batch} more batches available")


if __name__ == "__main__":
    asyncio.run(main())
