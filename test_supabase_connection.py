"""
Test Supabase Connection
Run this script to verify your Supabase configuration is working correctly
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import json

# Load environment variables
load_dotenv()

print("=" * 60)
print("🧪 SUPABASE CONNECTION TEST")
print("=" * 60)
print()

# Step 1: Check environment variables
print("📋 Step 1: Checking Environment Variables...")
print("-" * 60)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url:
    print("❌ SUPABASE_URL is not set!")
    print("   Please set it in your .env file")
    sys.exit(1)
else:
    print(f"✅ SUPABASE_URL: {supabase_url}")

if not supabase_key:
    print("❌ SUPABASE_KEY is not set!")
    print("   Please set it in your .env file")
    sys.exit(1)
else:
    # Only show first and last 8 characters for security
    masked_key = f"{supabase_key[:8]}...{supabase_key[-8:]}" if len(supabase_key) > 16 else "***"
    print(f"✅ SUPABASE_KEY: {masked_key}")

print()

# Step 2: Check bucket names
print("📋 Step 2: Checking Bucket Configuration...")
print("-" * 60)
buckets = {
    'images': os.getenv('BUCKET_IMAGES', 'images'),
    'audio': os.getenv('BUCKET_AUDIO', 'audio'),
    'video': os.getenv('BUCKET_VIDEO', 'video'),
    'metadata': os.getenv('BUCKET_METADATA', 'metadata'),
    'text': os.getenv('BUCKET_TEXT', 'text')
}

for key, value in buckets.items():
    print(f"  {key}: {value}")

print()

# Step 3: Test Supabase client initialization
print("📋 Step 3: Testing Supabase Client Initialization...")
print("-" * 60)

try:
    client = create_client(supabase_url, supabase_key)
    print("✅ Supabase client created successfully!")
except Exception as e:
    print(f"❌ Failed to create Supabase client: {e}")
    sys.exit(1)

print()

# Step 4: Test storage buckets access
print("📋 Step 4: Testing Storage Buckets Access...")
print("-" * 60)

bucket_status = {}
for bucket_name in ['images', 'audio', 'video', 'metadata', 'text']:
    try:
        # Try to list files in the bucket
        result = client.storage.from_(bucket_name).list()
        bucket_status[bucket_name] = {
            'accessible': True,
            'file_count': len(result),
            'error': None
        }
        print(f"✅ Bucket '{bucket_name}': Accessible ({len(result)} items)")
    except Exception as e:
        bucket_status[bucket_name] = {
            'accessible': False,
            'file_count': 0,
            'error': str(e)
        }
        print(f"❌ Bucket '{bucket_name}': {e}")

print()

# Step 5: Test file upload (create a small test file)
print("📋 Step 5: Testing File Upload...")
print("-" * 60)

test_bucket = 'metadata'
test_file_path = 'test_connection.json'
test_data = json.dumps({
    'test': True,
    'message': 'Supabase connection test',
    'timestamp': str(os.times())
}).encode('utf-8')

try:
    # Try to upload test file
    upload_result = client.storage.from_(test_bucket).upload(
        path=test_file_path,
        file=test_data,
        file_options={"content-type": "application/json", "upsert": "true"}
    )
    print(f"✅ Successfully uploaded test file to {test_bucket}/{test_file_path}")
    
    # Get public URL
    public_url = client.storage.from_(test_bucket).get_public_url(test_file_path)
    print(f"   Public URL: {public_url}")
    
except Exception as e:
    print(f"❌ Failed to upload test file: {e}")
    print(f"   This might mean the bucket doesn't exist or isn't public")

print()

# Step 6: Test file download
print("📋 Step 6: Testing File Download...")
print("-" * 60)

try:
    # Try to download the test file we just uploaded
    download_result = client.storage.from_(test_bucket).download(test_file_path)
    print(f"✅ Successfully downloaded test file from {test_bucket}/{test_file_path}")
    
    # Parse and display content
    content = json.loads(download_result.decode('utf-8'))
    print(f"   Content: {content}")
    
except Exception as e:
    print(f"❌ Failed to download test file: {e}")

print()

# Step 7: Clean up test file
print("📋 Step 7: Cleaning Up Test File...")
print("-" * 60)

try:
    client.storage.from_(test_bucket).remove([test_file_path])
    print(f"✅ Successfully deleted test file from {test_bucket}/{test_file_path}")
except Exception as e:
    print(f"⚠️  Could not delete test file: {e}")
    print(f"   You may need to delete it manually from Supabase dashboard")

print()

# Final Summary
print("=" * 60)
print("📊 TEST SUMMARY")
print("=" * 60)

all_buckets_accessible = all(status['accessible'] for status in bucket_status.values())

if all_buckets_accessible:
    print("✅ ALL TESTS PASSED!")
    print("   Your Supabase configuration is working correctly.")
    print("   You can now use the Flask backend with Supabase storage.")
else:
    print("⚠️  SOME ISSUES DETECTED")
    print("   Buckets with issues:")
    for bucket, status in bucket_status.items():
        if not status['accessible']:
            print(f"   - {bucket}: {status['error']}")
    print()
    print("📝 To fix bucket issues:")
    print("   1. Go to your Supabase dashboard: https://app.supabase.com")
    print("   2. Navigate to Storage")
    print("   3. Create the missing buckets:")
    for bucket, status in bucket_status.items():
        if not status['accessible']:
            print(f"      - {bucket}")
    print("   4. Make sure buckets are set to 'Public' if you want public URLs")

print()
print("=" * 60)
print("🎉 Test Complete!")
print("=" * 60)

