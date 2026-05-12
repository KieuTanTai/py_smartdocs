from pathlib import Path
import nltk

CURRENT_DIR = Path(__file__).parent.resolve()
TEST_DATA_DIR = CURRENT_DIR / "output"
TEST_FILE = TEST_DATA_DIR / "normalized_ece34920-8637-4706-9d52-4deb5e064976.md"
from langchain_text_splitters import NLTKTextSplitter

def test_nltk_text_splitter():
    try:
        text_splitter = NLTKTextSplitter(chunk_size=1000, chunk_overlap=200)
        text = TEST_FILE.read_text()
        chunks = text_splitter.split_text(text)
        if len(chunks) == 0:
            raise ValueError("No chunks were created. The text splitter may not be working correctly.")
        with open(TEST_DATA_DIR / "chunks_output.txt", "w") as f:
            for i, chunk in enumerate(chunks):
                f.write(f"Chunk {i}:\n{chunk}\n\n")
        print(f"Total chunks created: {len(chunks)}. Chunks have been written to {TEST_DATA_DIR / 'chunks_output.txt'} for review.")
    except LookupError as e:
        print(f"Error occurred while downloading NLTK data: {e}")
    except ValueError as e:
        nltk.download("punkt_tab")
        test_nltk_text_splitter()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_nltk_text_splitter()
    print("NLTKTextSplitter test completed successfully.")
