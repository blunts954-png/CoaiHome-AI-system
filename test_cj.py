import asyncio
import traceback
from api_clients.cj_dropshipping_client import get_cj_client

__test__ = False

async def test():
    cj = get_cj_client()
    try:
        res = await cj._make_request("GET", "product/listV2")
        print("CJ Response keys:", res.keys() if isinstance(res, dict) else type(res))
    except Exception as e:
        traceback.print_exc()
    finally:
        await cj.close()

if __name__ == "__main__":
    asyncio.run(test())
