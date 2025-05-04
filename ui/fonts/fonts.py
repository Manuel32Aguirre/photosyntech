from PyQt6.QtGui import QFontDatabase, QFont

NORMAL_FONT = 'Arial' #Default font
BOLD_FONT = 'Arial Black'

def setup_fonts() -> None:
    mont_id = QFontDatabase.addApplicationFont('SpaceGrotesk-Regular.ttf')
    bold_id = QFontDatabase.addApplicationFont('SpaceGrotesk-Bold.ttf')

    if mont_id != -1 and bold_id != -1:
        global NORMAL_FONT, BOLD_FONT
        NORMAL_FONT = QFontDatabase.applicationFontFamilies(mont_id)[0]
        BOLD_FONT = QFontDatabase.applicationFontFamilies(bold_id)[0]
        print('loaded')

TITLE = QFont(BOLD_FONT, 18, weight=QFont.Weight.Bold)
NORMAL = QFont(NORMAL_FONT, 14)
