from langdetect import detect

texts = [
    "to determine what will happen to the premier league, if an indepemission upholds the charge that they spied on one of their training sessions in the very latest.",
    "de l'équipe nationale, en arizona, cet événement s'est déroulé ce mercredi. (AFP) ... des etats-unis",
    "l'afp.-netflix.cl.uy..: le journal intime. (fr) .embed.oo.iu.en .",
    "هذا مقال باللغة العربية حول كرة القدم",
    "Este es un artículo en español sobre fútbol."
]

for t in texts:
    try:
        print(f"Text: {t[:50]}... -> Detected: {detect(t)}")
    except Exception as e:
        print(f"Error for {t[:50]}: {e}")
