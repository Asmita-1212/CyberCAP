from libretranslatepy import LibreTranslateAPI

lt = LibreTranslateAPI("https://translate.argosopentech.com/")

text = "मुझे धोखा दिया गया ऑनलाइन"
translated = lt.translate(text, "hi", "en")

print("Translated:", translated)
