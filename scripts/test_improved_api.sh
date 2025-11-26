#!/bin/bash

# Script test cho Improved Final Search API
# FastAPI Server: http://localhost:8000

echo "🚀 TEST IMPROVED FINAL SEARCH API"
echo "=========================================="

# Biến base URL
BASE_URL="http://localhost:8000"
HEADER="Content-Type: application/json"

echo "📡 Base URL: $BASE_URL"
echo ""

# 1. Test root endpoint
echo "1. 📋 Testing root endpoint..."
curl -s "$BASE_URL/" | jq '.'
echo ""

# 2. Test health check
echo "2. 🩺 Testing health check..."
curl -s "$BASE_URL/health" | jq '.'
echo ""

# 3. Test get user info
echo "3. 👤 Testing get user info..."
echo "   • Employee (user001):"
curl -s "$BASE_URL/user/user001" | jq '.'
echo ""

echo "   • Manager (user003):"
curl -s "$BASE_URL/user/user003" | jq '.'
echo ""

echo "   • HR (user005):"
curl -s "$BASE_URL/user/user005" | jq '.'
echo ""

# 4. Test search với các role khác nhau
echo "4. 🔍 Testing search với different roles..."

# Employee search
echo "   👨‍💼 Employee search 'nghỉ phép':"
curl -s -X POST "$BASE_URL/search" \
  -H "$HEADER" \
  -d '{
    "user_id": "user001",
    "query": "nghỉ phép",
    "top_k": 3
  }' | jq '.'
echo ""

echo "   👨‍💼 Employee search 'lương thưởng':"
curl -s -X POST "$BASE_URL/search" \
  -H "$HEADER" \
  -d '{
    "user_id": "user001", 
    "query": "lương thưởng",
    "top_k": 3
  }' | jq '.'
echo ""

# Manager search
echo "   👨‍💼 Manager search 'lương tháng 13':"
curl -s -X POST "$BASE_URL/search" \
  -H "$HEADER" \
  -d '{
    "user_id": "user003",
    "query": "lương tháng 13", 
    "top_k": 3
  }' | jq '.'
echo ""

# HR search
echo "   👨‍💼 HR search 'bảo hiểm':"
curl -s -X POST "$BASE_URL/search" \
  -H "$HEADER" \
  -d '{
    "user_id": "user005",
    "query": "bảo hiểm",
    "top_k": 3
  }' | jq '.'
echo ""

# 5. Test smart search (threshold thấp)
echo "5. 🧠 Testing smart search (low threshold)..."
curl -s -X POST "$BASE_URL/smart-search" \
  -H "$HEADER" \
  -d '{
    "user_id": "user001",
    "query": "chế độ phúc lợi",
    "top_k": 3
  }' | jq '.'
echo ""

# 6. Test strict search (threshold cao)
echo "6. 🎯 Testing strict search (high threshold)..."
curl -s -X POST "$BASE_URL/strict-search" \
  -H "$HEADER" \
  -d '{
    "user_id": "user001", 
    "query": "nghỉ phép năm",
    "top_k": 3
  }' | jq '.'
echo ""

# 7. Test với user mới (auto-create)
echo "7. 🆕 Testing với user mới..."
curl -s -X POST "$BASE_URL/search" \
  -H "$HEADER" \
  -d '{
    "user_id": "user999",
    "query": "giờ làm việc",
    "user_info": {
      "username": "Nguyễn Thị Mới",
      "email": "newuser@company.com", 
      "role": "employee",
      "department": "IT"
    }
  }' | jq '.'
echo ""

# 8. Test categories info
echo "8. 📊 Testing categories info..."
curl -s "$BASE_URL/categories" | jq '.'
echo ""

# 9. Test vector store info
echo "9. 🗃️ Testing vector store info..."
curl -s "$BASE_URL/vector-store-info" | jq '.'
echo ""

# 10. Test comprehensive search test
echo "10. 🧪 Testing comprehensive search test..."
curl -s "$BASE_URL/test-search" | jq '.'
echo ""

# 11. Test get all users
echo "11. 👥 Testing get all users..."
curl -s "$BASE_URL/users" | jq '.'
echo ""

echo "=========================================="
echo "🎉 HOÀN THÀNH TEST IMPROVED FINAL SEARCH API"
echo "📊 Kết quả mong đợi:"
echo "   • Similarity scores: 0.4 - 0.8+"
echo "   • Phân quyền chính xác theo role"
echo "   • Semantic search tốt với tiếng Việt"
echo "=========================================="