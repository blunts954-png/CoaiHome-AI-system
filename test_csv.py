import io
import csv
import asyncio
from main import export_products_csv
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

async def test_csv_export():
    print("🧪 Testing CSV Export Logic...")
    try:
        response = await export_products_csv()
        print(f"   Response type: {type(response)}")
        
        if isinstance(response, StreamingResponse):
            content = b""
            async for chunk in response.body_iterator:
                content += chunk
            
            csv_text = content.decode("utf-8")
            reader = csv.reader(io.StringIO(csv_text))
            rows = list(reader)
            print(f"✅ CSV Generated. Total rows: {len(rows)}")
            if len(rows) > 0:
                print(f"   Header: {rows[0][:3]}")
        else:
            print(f"❌ Surprise response: {response}")
    except HTTPException as he:
        print(f"❌ HTTPException: {he.status_code} - {he.detail}")
    except Exception as e:
        print(f"❌ General Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_csv_export())
