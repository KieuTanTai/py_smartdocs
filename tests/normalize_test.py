import re
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
TEST_DATA_DIR = CURRENT_DIR / "output"
TEST_FILE = TEST_DATA_DIR / "output_5e166ad9-f829-4524-acb1-321adbce55de.md"
def test_normalize():
    if not TEST_FILE.exists():
        raise FileNotFoundError(f"Test file {TEST_FILE} does not exist.")
    with open(TEST_FILE, 'r') as file:
        content = file.read()
    normalized_content = content.strip()
    normalized_content = re.sub(r'\n+', '\n', normalized_content)
    normalized_content = re.sub(r'[ \t]+', ' ', normalized_content)
    output_file = TEST_DATA_DIR / "normalized_test.md"
    with open(output_file, 'w') as file:        
        file.write(normalized_content)

if __name__ == "__main__":
    test_normalize()
    print("All tests passed.")
