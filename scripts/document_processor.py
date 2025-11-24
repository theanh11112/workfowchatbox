# scripts/document_processor.py
import os
import json
import sys
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,      # Kích thước mỗi chunk
            chunk_overlap=200,    # Độ chồng lấp giữa các chunk
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
    
    def extract_text_from_file(self, file_path):
        """Extract text từ nhiều định dạng file"""
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif file_extension in ['.txt', '.md']:
                return self._extract_from_text(file_path)
            else:
                print(f"⚠️  Định dạng không hỗ trợ: {file_extension}")
                return ""
        except Exception as e:
            print(f"❌ Lỗi đọc file {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path):
        """Extract text từ PDF"""
        try:
            from PyPDF2 import PdfReader
            
            print(f"   📄 Đọc PDF: {file_path}")
            reader = PdfReader(file_path)
            text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                print(f"     📖 Đã xử lý trang {i+1}/{len(reader.pages)}")
            return text
        except ImportError:
            print("❌ PyPDF2 chưa được cài đặt")
            return ""
        except Exception as e:
            print(f"❌ Lỗi đọc PDF {file_path}: {e}")
            return ""
    
    def _extract_from_docx(self, file_path):
        """Extract text từ DOCX"""
        try:
            from docx import Document
            
            print(f"   📄 Đọc DOCX: {file_path}")
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            return text
        except ImportError:
            print("❌ python-docx chưa được cài đặt")
            return ""
        except Exception as e:
            print(f"❌ Lỗi đọc DOCX {file_path}: {e}")
            return ""
    
    def _extract_from_text(self, file_path):
        """Extract text từ TXT/MD"""
        try:
            print(f"   📄 Đọc text file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                print(f"❌ Lỗi encoding file {file_path}: {e}")
                return ""
        except Exception as e:
            print(f"❌ Lỗi đọc file {file_path}: {e}")
            return ""
    
    def clean_text(self, text):
        """Làm sạch text"""
        # Loại bỏ khoảng trắng thừa
        text = ' '.join(text.split())
        # Loại bỏ ký tự không in được nhưng giữ tiếng Việt
        text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t', ' '])
        return text
    
    def process_documents(self, metadata_file, output_file):
        """Xử lý tất cả documents và tạo chunks"""
        print("📖 Bắt đầu xử lý documents...")
        
        # Đảm bảo thư mục output tồn tại
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Load metadata
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except FileNotFoundError:
            print(f"❌ File metadata không tồn tại: {metadata_file}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi định dạng JSON trong file metadata: {e}")
            return None
        
        all_chunks = []
        processed_count = 0
        error_count = 0
        
        for doc_meta in metadata['documents']:
            file_path = doc_meta['file_path']
            print(f"\n🔍 Đang xử lý: {file_path}")
            
            if not os.path.exists(file_path):
                print(f"❌ File không tồn tại: {file_path}")
                error_count += 1
                continue
            
            # Extract text
            raw_text = self.extract_text_from_file(file_path)
            
            if not raw_text.strip():
                print(f"⚠️  File rỗng hoặc không đọc được: {file_path}")
                error_count += 1
                continue
            
            # Clean text
            cleaned_text = self.clean_text(raw_text)
            
            # Split thành chunks
            try:
                chunks = self.text_splitter.split_text(cleaned_text)
                print(f"   ✅ Đã chia thành {len(chunks)} chunks")
            except Exception as e:
                print(f"❌ Lỗi khi split text: {e}")
                error_count += 1
                continue
            
            # Thêm metadata vào từng chunk
            for i, chunk in enumerate(chunks):
                chunk_data = {
                    "id": f"{doc_meta['id']}_chunk_{i:03d}",
                    "content": chunk,
                    "document_id": doc_meta['id'],
                    "category": doc_meta['category'],
                    "allowed_roles": doc_meta['allowed_roles'],
                    "title": doc_meta['title'],
                    "description": doc_meta.get('description', ''),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "file_path": file_path,
                    "word_count": len(chunk.split())
                }
                all_chunks.append(chunk_data)
            
            processed_count += 1
        
        # Lưu kết quả
        output_data = {
            "statistics": {
                "total_documents": len(metadata['documents']),
                "processed_documents": processed_count,
                "error_documents": error_count,
                "total_chunks": len(all_chunks),
                "average_chunks_per_doc": len(all_chunks) / processed_count if processed_count > 0 else 0
            },
            "chunks": all_chunks
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 THỐNG KÊ XỬ LÝ:")
        print(f"   • Tổng documents: {len(metadata['documents'])}")
        print(f"   • Xử lý thành công: {processed_count}")
        print(f"   • Lỗi: {error_count}")
        print(f"   • Tổng chunks: {len(all_chunks)}")
        print(f"   • File output: {output_file}")
        
        return output_data

def main():
    processor = DocumentProcessor()
    
    # Xử lý documents
    result = processor.process_documents(
        metadata_file='config/documents_metadata.json',
        output_file='outputs/document_chunks.json'
    )
    
    if result and result['chunks']:
        # Hiển thị sample chunks
        print(f"\n📝 SAMPLE CHUNKS:")
        for i, chunk in enumerate(result['chunks'][:2]):  # Hiển thị 2 chunks đầu
            print(f"\n--- Chunk {i+1} ---")
            print(f"ID: {chunk['id']}")
            print(f"Title: {chunk['title']}")
            print(f"Content preview: {chunk['content'][:100]}...")
            print(f"Word count: {chunk['word_count']}")
    else:
        print("❌ Không có chunks nào được tạo ra")

if __name__ == "__main__":
    main()