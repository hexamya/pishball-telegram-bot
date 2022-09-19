fa2en = str.maketrans('۱۲۳۴۵۶۷۸۹۰','1234567890')
en2fa = str.maketrans('1234567890','۱۲۳۴۵۶۷۸۹۰')
standardize = lambda text : str(text.strip().translate(fa2en))
persianize = lambda text : str(text).translate(en2fa)