# scripts/validate_step1_2.py
import os
import json
import sys

def validate_step1_2():
    print("🔍 KIỂM TRA HOÀN THÀNH BƯỚC 1.2")
    print("=" * 50)
    
    # Kiểm tra dependencies
    print("1. Kiểm tra dependencies:")
    required_packages = [
        "PyPDF2", "docx", "langchain", 
        "langchain_text_splitters", "sentence_transformers"
    ]
    
    deps_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - CHƯA CÀI ĐẶT")
            deps_ok = False
    
    # Kiểm tra file output
    print("\n2. Kiểm tra kết quả xử lý:")
    output_file = 'outputs/document_chunks.json'
    
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats = data.get('statistics', {})
            chunks = data.get('chunks', [])
            
            print(f"   ✅ {output_file}")
            print(f"   • Documents processed: {stats.get('processed_documents', 0)}")
            print(f"   • Total chunks: {stats.get('total_chunks', 0)}")
            print(f"   • Error documents: {stats.get('error_documents', 0)}")
            
            # Kiểm tra chất lượng chunks
            if chunks:
                sample_chunk = chunks[0]
                print(f"   • Sample chunk ID: {sample_chunk.get('id')}")
                print(f"   • Sample word count: {sample_chunk.get('word_count')}")
                
        except Exception as e:
            print(f"   ❌ {output_file} - LỖI: {e}")
            deps_ok = False
    else:
        print(f"   ❌ {output_file} - CHƯA ĐƯỢC TẠO")
        deps_ok = False
    
    # Kiểm tra chunks quality
    print("\n3. Kiểm tra chất lượng chunks:")
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get('chunks', [])
        if chunks:
            # Kiểm tra kích thước chunks
            chunk_sizes = [len(chunk['content'].split()) for chunk in chunks[:10]]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            
            print(f"   • Avg words per chunk: {avg_size:.1f}")
            
            if 50 < avg_size < 150:  # Khoảng hợp lý
                print(f"   ✅ Kích thước chunks phù hợp")
            else:
                print(f"   ⚠️  Kích thước chunks có thể không tối ưu")
            
            # Kiểm tra metadata
            first_chunk = chunks[0]
            required_fields = ['id', 'content', 'category', 'allowed_roles', 'title']
            missing_fields = [field for field in required_fields if field not in first_chunk]
            
            if not missing_fields:
                print(f"   ✅ Metadata đầy đủ")
            else:
                print(f"   ❌ Thiếu fields: {missing_fields}")
                deps_ok = False
    
    # Tổng kết
    print("\n" + "=" * 50)
    if deps_ok:
        print("🎉 HOÀN THÀNH BƯỚC 1.2 - CHUYỂN ĐỔI TEXT THÀNH CÔNG")
        print("\n📊 KẾT QUẢ:")
        print(f"   • Documents đã xử lý: {stats.get('processed_documents')}")
        print(f"   • Tổng số chunks: {stats.get('total_chunks')}")
        print(f"   • Dependencies: Đầy đủ")
        return True
    else:
        print("❌ CHƯA HOÀN THÀNH - Vui lòng kiểm tra và thử lại")
        return False

if __name__ == "__main__":
    success = validate_step1_2()
    sys.exit(0 if success else 1)