# scripts/vector_store_improved.py
import json
import os
import sys
import numpy as np
from collections import Counter
import re
import math

class ImprovedVectorStore:
    def __init__(self, persist_directory="./improved_vector_store"):
        """Vector store được cải tiến với embedding tốt hơn"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        self.vectors = {}
        self.metadata = {}
        self.vocab = {}
        self.vocab_size = 1000
        self.vector_dim = 300  # Tăng dimension để capture nhiều thông tin hơn
        print("✅ Đã khởi tạo Improved Vector Store")
    
    def preprocess_text(self, text):
        """Tiền xử lý text tốt hơn"""
        # Chuyển thành chữ thường
        text = text.lower()
        
        # Loại bỏ ký tự đặc biệt, giữ lại chữ cái, số và khoảng trắng
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Thay thế nhiều khoảng trắng bằng một khoảng trắng
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def build_vocabulary(self, chunks):
        """Xây dựng vocabulary từ tất cả documents"""
        print("📚 Đang xây dựng vocabulary...")
        
        all_text = " ".join([chunk['content'] for chunk in chunks])
        processed_text = self.preprocess_text(all_text)
        words = processed_text.split()
        
        # Đếm tần suất từ
        word_freq = Counter(words)
        
        # Lấy các từ phổ biến nhất
        most_common = word_freq.most_common(self.vocab_size)
        
        # Tạo vocabulary với TF-IDF weights
        total_docs = len(chunks)
        doc_freq = {}
        
        # Tính document frequency cho mỗi từ
        for chunk in chunks:
            chunk_words = set(self.preprocess_text(chunk['content']).split())
            for word in chunk_words:
                doc_freq[word] = doc_freq.get(word, 0) + 1
        
        # Tạo vocab với id và weights
        self.vocab = {}
        for idx, (word, freq) in enumerate(most_common):
            # Tính IDF weight
            idf = math.log(total_docs / (doc_freq.get(word, 1) + 1)) + 1
            self.vocab[word] = {
                'id': idx,
                'freq': freq,
                'idf': idf
            }
        
        print(f"✅ Đã xây dựng vocabulary với {len(self.vocab)} từ")
    
    def create_improved_embedding(self, text):
        """Tạo embedding cải tiến sử dụng TF-IDF"""
        processed_text = self.preprocess_text(text)
        words = processed_text.split()
        
        # Khởi tạo vector
        vector = np.zeros(self.vector_dim)
        
        # Tính term frequency
        word_count = len(words)
        if word_count == 0:
            return vector.tolist()
        
        word_freq = Counter(words)
        
        # Tạo embedding sử dụng TF-IDF
        for word, count in word_freq.items():
            if word in self.vocab:
                word_info = self.vocab[word]
                # TF-IDF weight
                tf = count / word_count
                tf_idf = tf * word_info['idf']
                
                # Sử dụng multiple hash functions để phân phối tốt hơn
                for seed in range(3):  # 3 hash functions khác nhau
                    hash_val = (hash(word + str(seed)) % (self.vector_dim // 3)) + (seed * (self.vector_dim // 3))
                    vector[hash_val] += tf_idf
        
        # Thêm biểu diễn cho cụm từ thông dụng
        common_phrases = {
            'nghỉ phép': [0.8, 0.6, 0.4],
            'lương thưởng': [0.7, 0.5, 0.3],
            'bảo hiểm': [0.6, 0.4, 0.2],
            'giờ làm việc': [0.5, 0.3, 0.1],
            'hợp đồng': [0.4, 0.2, 0.1]
        }
        
        for phrase, weights in common_phrases.items():
            if phrase in text.lower():
                for i, weight in enumerate(weights):
                    if i * 3 < self.vector_dim:
                        vector[i * 3] += weight
        
        # Chuẩn hóa vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()
    
    def add_documents(self, chunks):
        """Thêm documents vào vector store"""
        print("📥 Đang thêm documents vào vector store...")
        
        # Xây dựng vocabulary trước
        self.build_vocabulary(chunks)
        
        for chunk in chunks:
            chunk_id = chunk['id']
            content = chunk['content']
            
            # Tạo embedding cải tiến
            embedding = self.create_improved_embedding(content)
            
            # Lưu vector và metadata
            self.vectors[chunk_id] = embedding
            self.metadata[chunk_id] = {
                "document_id": chunk['document_id'],
                "category": chunk['category'],
                "allowed_roles": chunk['allowed_roles'],
                "title": chunk['title'],
                "content": content[:200] + "..." if len(content) > 200 else content,
                "word_count": chunk['word_count'],
                "full_content": content  # Lưu toàn bộ content để hiển thị kết quả tốt hơn
            }
        
        print(f"✅ Đã thêm {len(chunks)} documents")
        
        # Thống kê
        categories = {}
        for chunk in chunks:
            cat = chunk['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"📊 Phân bố theo category:")
        for cat, count in categories.items():
            print(f"   • {cat}: {count} chunks")
    
    def enhanced_cosine_similarity(self, vec1, vec2):
        """Cosine similarity được cải tiến"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        base_similarity = dot_product / (norm1 * norm2)
        
        # Tăng cường similarity cho các vector có cùng pattern
        if base_similarity > 0.3:  # Chỉ áp dụng cho các kết quả khá tương đồng
            # Thêm trọng số cho các dimensions có giá trị cao
            significant_dims = (vec1 > 0.1) & (vec2 > 0.1)
            if np.any(significant_dims):
                enhanced_similarity = np.mean((vec1[significant_dims] + vec2[significant_dims]) / 2)
                base_similarity = 0.7 * base_similarity + 0.3 * enhanced_similarity
        
        return min(base_similarity, 1.0)  # Đảm bảo không vượt quá 1
    
    def search(self, query, n_results=5, similarity_threshold=0.1):
        """Tìm kiếm cải tiến với threshold"""
        print(f"\n🔍 TÌM KIẾM: '{query}'")
        
        # Tạo embedding cho query
        query_embedding = self.create_improved_embedding(query)
        
        # Tính similarity với tất cả documents
        similarities = []
        for chunk_id, vector in self.vectors.items():
            similarity = self.enhanced_cosine_similarity(query_embedding, vector)
            if similarity >= similarity_threshold:  # Lọc kết quả có similarity thấp
                similarities.append((chunk_id, similarity))
        
        # Sắp xếp theo similarity (cao nhất trước)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Lấy kết quả top n
        top_results = similarities[:n_results]
        
        print(f"✅ Tìm thấy {len(top_results)} kết quả phù hợp (threshold: {similarity_threshold}):")
        
        results = []
        for i, (chunk_id, similarity) in enumerate(top_results):
            metadata = self.metadata[chunk_id]
            print(f"\n--- Kết quả {i+1} (similarity: {similarity:.4f}) ---")
            print(f"ID: {chunk_id}")
            print(f"Title: {metadata['title']}")
            print(f"Category: {metadata['category']}")
            print(f"Roles: {metadata['allowed_roles']}")
            print(f"Content: {metadata['content']}")
            
            results.append({
                'id': chunk_id,
                'similarity': similarity,
                'metadata': metadata
            })
        
        return results
    
    def semantic_search(self, query, n_results=5, boost_categories=None):
        """Tìm kiếm ngữ nghĩa với khả năng boost categories"""
        if boost_categories is None:
            boost_categories = []
        
        results = self.search(query, n_results * 2, similarity_threshold=0.05)  # Lấy nhiều kết quả hơn
        
        # Boost kết quả trong categories được ưu tiên
        boosted_results = []
        normal_results = []
        
        for result in results:
            if result['metadata']['category'] in boost_categories:
                # Tăng similarity cho các kết quả trong category được boost
                result['similarity'] *= 1.2
                boosted_results.append(result)
            else:
                normal_results.append(result)
        
        # Kết hợp và sắp xếp lại
        final_results = boosted_results + normal_results
        final_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return final_results[:n_results]
    
    def save(self):
        """Lưu vector store"""
        import pickle
        
        data = {
            'vectors': self.vectors,
            'metadata': self.metadata,
            'vocab': self.vocab,
            'vocab_size': self.vocab_size,
            'vector_dim': self.vector_dim
        }
        
        with open(f'{self.persist_directory}/vector_store.pkl', 'wb') as f:
            pickle.dump(data, f)
        
        # Lưu vocabulary riêng để debug
        with open(f'{self.persist_directory}/vocab.json', 'w', encoding='utf-8') as f:
            json_vocab = {k: v for k, v in self.vocab.items()}
            json.dump(json_vocab, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Đã lưu vector store tại: {self.persist_directory}/vector_store.pkl")
    
    def load(self):
        """Tải vector store"""
        import pickle
        
        try:
            with open(f'{self.persist_directory}/vector_store.pkl', 'rb') as f:
                data = pickle.load(f)
            
            self.vectors = data['vectors']
            self.metadata = data['metadata']
            self.vocab = data.get('vocab', {})
            self.vocab_size = data.get('vocab_size', 1000)
            self.vector_dim = data.get('vector_dim', 300)
            
            print(f"📂 Đã tải vector store với {len(self.vectors)} documents")
            print(f"📚 Vocabulary size: {len(self.vocab)}")
            return True
        except FileNotFoundError:
            print("ℹ️  Chưa có vector store được lưu")
            return False

def main():
    print("🚀 BẮT ĐẦU THIẾT LẬP IMPROVED VECTOR STORE")
    print("=" * 50)
    
    # Khởi tạo vector store cải tiến
    vector_store = ImprovedVectorStore()
    
    # Thử tải vector store đã lưu
    if not vector_store.load():
        # Nếu chưa có, tạo mới từ chunks
        try:
            with open('outputs/document_chunks.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = data['chunks']
            print(f"📖 Đã load {len(chunks)} chunks từ file")
            
            # Thêm documents vào vector store
            vector_store.add_documents(chunks)
            
            # Lưu vector store
            vector_store.save()
            
        except FileNotFoundError:
            print("❌ File outputs/document_chunks.json không tồn tại")
            print("   Hãy chạy Bước 1.2 trước")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            sys.exit(1)
    
    # Test tìm kiếm với các cải tiến
    print("\n" + "=" * 50)
    print("🧪 TEST TÌM KIẾM CẢI TIẾN")
    print("=" * 50)
    
    # Test cơ bản
    print("\n1. 🔍 TÌM KIẾM CƠ BẢN:")
    vector_store.search("nghỉ phép năm", n_results=3)
    vector_store.search("lương thưởng hàng tháng", n_results=3)
    vector_store.search("giờ làm việc công ty", n_results=3)
    
    # Test semantic search với boost category
    print("\n2. 🔍 TÌM KIẾM NGỮ NGHĨA (BOOST CATEGORY):")
    semantic_results = vector_store.semantic_search(
        "bảo hiểm", 
        n_results=3, 
        boost_categories=["Bảo Hiểm Xã Hội"]
    )
    
    for i, result in enumerate(semantic_results):
        print(f"\n--- Semantic Result {i+1} (similarity: {result['similarity']:.4f}) ---")
        print(f"Category: {result['metadata']['category']}")
        print(f"Title: {result['metadata']['title']}")
    
    # Test với query phức tạp
    print("\n3. 🔍 TÌM KIẾM QUERY PHỨC TẠP:")
    vector_store.search("chế độ nghỉ phép và lương thưởng", n_results=3)
    vector_store.search("điều kiện hưởng bảo hiểm xã hội", n_results=3)
    
    print(f"\n🎉 HOÀN THÀNH THIẾT LẬP IMPROVED VECTOR STORE")
    print(f"📁 Vector store location: ./improved_vector_store")
    print(f"📊 Vector dimension: {vector_store.vector_dim}")
    print(f"📚 Vocabulary size: {len(vector_store.vocab)}")

if __name__ == "__main__":
    main()