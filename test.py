def reverse_string():
    # 사용자로부터 입력 받기
    user_input = "print(\"Hello, World\")"
    
    # 텍스트 뒤집기
    result = user_input[::-1]
    
    print("-" * 30)
    print(f"결과: {result}")
    print("-" * 30)

# 프로그램 실행
if __name__ == "__main__":
    reverse_string()