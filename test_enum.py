from backend.apps.core.enums.e_provider_name import EProviderName

# Test 1: Create enum from string
provider = EProviderName("gemini")
print(f"provider type: {type(provider)}")
print(f"provider value: {provider}")
print(f"provider == 'gemini': {provider == 'gemini'}")
print(f"provider == EProviderName.GEMINI: {provider == EProviderName.GEMINI}")
print(f"provider == EProviderName.GEMINI.value: {provider == EProviderName.GEMINI.value}")

# Test 2: Direct enum comparison
print(f"\nEProviderName.GEMINI == 'gemini': {EProviderName.GEMINI == 'gemini'}")
print(f"EProviderName.GEMINI.value == 'gemini': {EProviderName.GEMINI.value == 'gemini'}")
