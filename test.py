def fill_zeros(number):
    if not (0 <= number <= 9999):
        raise ValueError("Число должно быть в диапазоне от 0 до 9999")
    return f"{number:04d}"

# Примеры использования
print(fill_zeros(1))     # "0001"
print(fill_zeros(123))   # "0123"
print(fill_zeros(9999))  # "9999"

print(fill_zeros(10000))  # Ошибка ValueError
