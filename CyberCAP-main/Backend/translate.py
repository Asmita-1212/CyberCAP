from deep_translator import GoogleTranslator

def translate_to_english(text: str) -> str:
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print("Translation error:", e)
        return text

if __name__ == "__main__":
    text = "मेरे बैंक खाते से धोखाधड़ी के कारण 5000 रुपये खो गए हैं।"
    print("Original:", text)
    translated = translate_to_english(text)
    print("Translated:", translated)
