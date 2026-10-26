import requests
import sys

def test_new_game():
    try:
        print("Testing /api/new-game...")
        response = requests.get('http://127.0.0.1:5000/api/new-game')
        if response.status_code == 200:
            data = response.json()
            grid_size = data.get('gridSize')
            words = data.get('words', [])
            
            print(f"✅ Status 200 OK")
            print(f"Grid Size: {grid_size}")
            print(f"Words Count: {len(words)}")
            
            if len(words) == 0:
                print("⚠️ WARNING: Word list is empty! Check server logs for 'Data file not found'.")
                return False
                
            if 'grid' in data:
                print("✅ Grid present")
                return True
            else:
                print("❌ Missing grid in response")
                return False
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if not test_new_game():
        sys.exit(1)
