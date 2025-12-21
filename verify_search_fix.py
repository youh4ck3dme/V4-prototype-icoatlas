import asyncio
import sys
from backend.services.search_by_name import search_by_name

async def main():
    print("Running verify_search_fix.py...")
    try:
        # Test case that caused 500 error
        query = "56760892"
        print(f"Searching for: {query}")
        results = await search_by_name(query, country="SK", limit=5)
        print(f"✅ Search successful! Found {len(results)} results.")
        for r in results:
            print(f" - {r['name']} ({r['identifier']})")
    except Exception as e:
        print(f"❌ Search FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
