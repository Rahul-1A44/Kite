import requests

# ⚠️ PASTE YOUR KEY HERE
MY_KEY = "AIzaSyCwdf6e0cXWmqxZoNAtSnBRlGCMToDg_ko"

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={MY_KEY}"

try:
    print("📡 Asking Google for available models...")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS! Here are the models you can use:")
        print("-" * 40)
        found_any = False
        for model in data.get('models', []):
            # We only care about models that can 'generateContent'
            if "generateContent" in model.get('supportedGenerationMethods', []):
                print(f"🌟 {model['name']}")
                found_any = True
        
        if not found_any:
            print("❌ No text generation models found. You might need to enable them in Google Cloud Console.")
        print("-" * 40)
    else:
        print(f"\n❌ FAILURE (Status {response.status_code})")
        print("Error Message:", response.text)

except Exception as e:
    print(f"\n❌ CONNECTION ERROR: {e}")