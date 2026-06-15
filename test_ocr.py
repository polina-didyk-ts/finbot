import sys

from ocr import extract_amount


def main() -> None:
    if len(sys.argv) < 2:
        print("Використання: python test_ocr.py <шлях_до_зображення>")
        return

    image_path = sys.argv[1]
    result = extract_amount(image_path)
    if result:
        print(f"Результат: {result}")
    else:
        print("Сума не розпізнана")


if __name__ == "__main__":
    main()
