# Import libraries
from docx.shared import Inches
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.section import WD_ORIENT
from PIL import ImageFont, ImageDraw, Image
import shutil
import os
import numpy as np
import cv2
from natsort import natsort_keygen
from fpdf import FPDF

# Declare constant variables
NATSORT_KEY = natsort_keygen()
TEXT_FILE = 'Scripts/output.txt'
IMAGES_LOCATION = 'Scrpts/Images/'
if not os.path.exists(IMAGES_LOCATION): os.makedirs(IMAGES_LOCATION)
OUTPUT_LOCATION = 'Scripts/Output/'
if not os.path.exists(OUTPUT_LOCATION): os.makedirs(OUTPUT_LOCATION)
TEXT_FILE_CONTENTS = None

# Output options
DPI = 300
TOP_MARGIN = int(0.75*DPI)  # Inches
BOTTOM_MARGIN = int(0.75*DPI)  # Inches
LEFT_MARGIN = int(0.75*DPI)  # Inches
RIGHT_MARGIN = int(0.75*DPI)  # Inches
MARGIN_SIZE = (TOP_MARGIN, BOTTOM_MARGIN, LEFT_MARGIN, RIGHT_MARGIN)
PAPER_SIZE = (11, 8.5)  # INCHES
PIXEL_SIZE = (int(PAPER_SIZE[0]*DPI), int(PAPER_SIZE[1]*DPI))
COL_SIZE = ((PIXEL_SIZE[0]//2-(LEFT_MARGIN+RIGHT_MARGIN)),
            PIXEL_SIZE[1]-(TOP_MARGIN+BOTTOM_MARGIN))

# Controls
INCLUDE_PAGE_NUMBERS = True
PAGE_NUMBERS_TOP = False
PAGE_NUMBERS_BOTTOM = True

LINES_PER_PAGE = 35
CHARACTERS_PER_LINE = 40

FONT_SIZE = 49
FONT = ImageFont.truetype('arial.ttf', FONT_SIZE)

'''
<COL_EMPTY> Leave coloumn empty and start in next one.
<TITLE> Your title </TITLE> WIll give 2 lines extra space to add title.
'''

def clear_folders(folders):
    for folder in folders:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


def add_margin(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result


def change_orientation(document, new_section):
    current_section = document.sections[-1]
    new_width, new_height = current_section.page_height, current_section.page_width
    new_section.orientation = WD_ORIENT.LANDSCAPE
    new_section.page_width = new_width
    new_section.page_height = new_height
    return new_section


def convert_text_to_image():
    # Declare local variables
    orginized_text_file_contents = []
    page_layout_text = []
    orginized_line = ''
    char_count = 0
    line_count = 0

    # Read text file
    with open(TEXT_FILE, 'r', encoding='utf-8') as file:
        TEXT_FILE_CONTENTS = file.read()

    # Orginize text to fit on pages (start to end)
    lines = TEXT_FILE_CONTENTS.split('\n')
    text = []
    found_title = False
    titles = ''
    for line in lines:
        text += line.split(' ')
    for _, word in enumerate(text):
        if word == '':
            orginized_text_file_contents.append([orginized_line])
            orginized_text_file_contents.append(['\n'])
            orginized_line = ''
            char_count = 0
        elif word == '<TITLE>':
            if len(orginized_line) > 0:
                orginized_text_file_contents.append([orginized_line])
                orginized_line = ''
                char_count = 0
            found_title = True
            continue
        elif word == '</TITLE>' and found_title:
            found_title = False
            orginized_text_file_contents.append(['\n'])
            orginized_text_file_contents.append([titles])
            orginized_text_file_contents.append(['\n'])
            continue
        elif word == '<COL_EMPTY>':
            if len(orginized_line) > 0:
                orginized_text_file_contents.append([orginized_line])
                orginized_line = ''
                char_count = 0
            orginized_text_file_contents.append([word])
            continue

        if found_title:
            titles += (word + ' ')
            continue

        char_count += len(word)
        orginized_line += (word + ' ')
        if char_count >= CHARACTERS_PER_LINE:
            orginized_text_file_contents.append([orginized_line])
            orginized_line = ''
            char_count = 0

    # Put lines in order of pages
    page_text = []
    for index, line in enumerate(orginized_text_file_contents):
        if line == ['<COL_EMPTY>']:
            for _ in range(LINES_PER_PAGE-len(page_text)):
                line_count += 1
                page_text.append(['\n'])
            page_layout_text.append(page_text)
            line_count = 0
            page_text = []
            continue
        line_count += 1
        page_text.append(line)
        if line_count >= LINES_PER_PAGE or index == len(orginized_text_file_contents)-1:
            print(index, len(orginized_text_file_contents))
            page_layout_text.append(page_text)
            page_text = []
            line_count = 0
    page_text.clear()

    # How many coloumns are there
    NUM_OF_COLS = (len(page_layout_text))
    if NUM_OF_COLS % 2 != 0:
        NUM_OF_COLS += 1

    # Figure out order of pages
    ORDER_OF_PAGES = [['BACK', 'FRONT']]
    flip_spots = True
    for i in range(NUM_OF_COLS):
        n = i + 1
        if not i >= (NUM_OF_COLS//2):
            ORDER_OF_PAGES.append(
                [n if flip_spots else NUM_OF_COLS-i, NUM_OF_COLS-i if flip_spots else n])
            flip_spots = not flip_spots

    # Create blank image
    file_names = []
    for i in ORDER_OF_PAGES:
        for j in i:
            file_names.append(j)

    for page_name in file_names:
        img = Image.new("RGB", COL_SIZE, (255, 255, 255))
        img.save(f"{IMAGES_LOCATION}{page_name}.png", "PNG")

    # Add text to image.
    all_file_names = os.listdir(IMAGES_LOCATION)
    all_file_names.sort(key=NATSORT_KEY)
    all_file_names.pop(-1)
    all_file_names.pop(-1)
    for page_number in all_file_names:
        page_number = int(page_number.replace('.png', ''))
        try:
            if page_number == 0:
                continue
            img = Image.open(f"{IMAGES_LOCATION}{page_number}.png")
            text = [i[0] for i in page_layout_text[page_number-1]]
            text = '\n'.join(text)
            text_img = ImageDraw.Draw(img)
            text_img.text((0, 0), text, fill=(0, 0, 0), font=FONT)
            img = add_margin(img, TOP_MARGIN, RIGHT_MARGIN,
                             BOTTOM_MARGIN, LEFT_MARGIN, (255, 255, 255))
            img.save(f"{IMAGES_LOCATION}{page_number}.png", quality=95)
        except IndexError:
            print(f'Page #{page_number} is empty.')
            img = Image.open(f"{IMAGES_LOCATION}{page_number}.png")
            img = add_margin(img, TOP_MARGIN, RIGHT_MARGIN,
                             BOTTOM_MARGIN, LEFT_MARGIN, (255, 255, 255))
            img.save(f"{IMAGES_LOCATION}{page_number}.png", quality=95)
    for page_name in ['BACK', 'FRONT']:
        img = Image.open(f"{IMAGES_LOCATION}{page_name}.png")
        img = add_margin(img, TOP_MARGIN, RIGHT_MARGIN,
                         BOTTOM_MARGIN, LEFT_MARGIN, (255, 255, 255))
        img.save(f"{IMAGES_LOCATION}{page_name}.png", quality=95)

    # Add page numbers in header
    if INCLUDE_PAGE_NUMBERS:
        flip_spots = True
        for page_order in ORDER_OF_PAGES:
            for page in page_order:
                img = Image.open(f"{IMAGES_LOCATION}{page}.png")
                W, H = img.size
                # w, h = page_num_img.textsize(str(page))
                w, h = FONT.getsize(str(page))
                page_num_img = ImageDraw.Draw(img)
                # Add page_numbers
                if PAGE_NUMBERS_TOP:
                    if flip_spots:
                        page_num_img.text((100, 100), str(
                            page), fill=(0, 0, 0), font=FONT)
                    else:
                        page_num_img.text((W-w-150, 100), str(page),
                                          fill=(0, 0, 0), font=FONT)
                    flip_spots = not flip_spots
                elif PAGE_NUMBERS_BOTTOM:
                    page_num_img.text(((W-w)/2, (H-h-150)),
                                      str(page), fill=(0, 0, 0), font=FONT)
                img.save(f"{IMAGES_LOCATION}{page}.png", quality=95)

    # Combine
    for page_index, page_order in enumerate(ORDER_OF_PAGES):
        img1 = cv2.imread(f"{IMAGES_LOCATION}{page_order[0]}.png")
        img2 = cv2.imread(f"{IMAGES_LOCATION}{page_order[1]}.png")
        try:
            vis = np.concatenate((img1, img2), axis=1)
        except:
            img = Image.open(f"{IMAGES_LOCATION}{page_order[1]}.png")
            img = add_margin(img, TOP_MARGIN, RIGHT_MARGIN,
                             BOTTOM_MARGIN, LEFT_MARGIN, (255, 255, 255))
            img.save(f"{IMAGES_LOCATION}{page_order[1]}.png", quality=95)
            vis = np.concatenate((img1, img), axis=1)
        # vis = cv2.hconcat([img1, img2])
        cv2.imwrite(
            f'{IMAGES_LOCATION}Page {page_index+1}; {page_order[0]} - {page_order[1]}.png', vis)
        if page_index == 0:
            img = Image.open(
                f'{IMAGES_LOCATION}Page {page_index+1}; {page_order[0]} - {page_order[1]}.png')
            draw = ImageDraw.Draw(img)
            W, H = img.size
            draw.line((W/2, 0, W/2, H), fill=(0, 0, 0), width=1)
            img.save(
                f'{IMAGES_LOCATION}Page {page_index+1}; {page_order[0]} - {page_order[1]}.png', quality=95)
        os.remove(f"{IMAGES_LOCATION}{page_order[0]}.png")
        os.remove(f"{IMAGES_LOCATION}{page_order[1]}.png")


def convert_image_to_document():
    # Compile and Save
    all_file_names = os.listdir(IMAGES_LOCATION)
    all_file_names.sort(key=NATSORT_KEY)
    document = Document()

    #changing the page margins
    sections = document.sections
    for section in sections:
        change_orientation(document, section)
        section.top_margin = Inches(0)
        section.bottom_margin = Inches(0)
        section.left_margin = Inches(0)
        section.right_margin = Inches(0)
    for _, path in enumerate(all_file_names):
        document.add_picture(IMAGES_LOCATION + path,
                             width=Inches(PAPER_SIZE[0]))
    document.save(f'{OUTPUT_LOCATION}/Compiled.docx')

def convert_image_to_pdf():
    all_file_names = os.listdir(IMAGES_LOCATION)
    all_file_names.sort(key=NATSORT_KEY)

    pdf = FPDF('L', 'in', 'A4')

    # Convert to mm
    LEFT_MARGIN, RIGHT_MARGIN = 0, 0

    for image in all_file_names:
        pdf.add_page()
        pdf.image(IMAGES_LOCATION + image, LEFT_MARGIN, RIGHT_MARGIN, PAPER_SIZE[0], PAPER_SIZE[-1])
    pdf.output(f"{OUTPUT_LOCATION}/Compiled.pdf", "F")

if __name__ == '__main__':
    clear_folders([IMAGES_LOCATION])
    convert_text_to_image()
    convert_image_to_document()
    convert_image_to_pdf()
