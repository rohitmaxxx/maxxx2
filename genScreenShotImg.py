from PIL import Image, ImageDraw, ImageFont
from pyvips import Image as pyImage
import textwrap, cgi, glob, os
import csv


IMG_COUNTER = None
def getCurrentImgFilename(same_file=False, path="imgs"):
    global IMG_COUNTER
    path = "output/" + path
    if not os.path.exists(path):
        os.mkdir(path)
    if IMG_COUNTER is None:
        IMG_COUNTER = len(glob.glob("%s*.png" % path))
    IMG_COUNTER += 1
    return "%s/screen_%s.png" % (path, IMG_COUNTER)

def getFontSizeByLanguage(string, font, renderer_lib, remove_height_offset=False):
    # get fontsize according to language
    string = cgi.escape(string)                   # Here preparing string to render if any special symbol found then convert into html code for render like(& to &amp;)
    if int(renderer_lib) == 1:
        size = font.getsize(string)
        if remove_height_offset:
            size[1] -= font.getoffset(string)[1]
    else:
        size = pyImage.text(string, dpi=font['normal_font_size'], fontfile=font['normal_font_file']).width, pyImage.text(string, dpi=font['normal_font_size'], fontfile=font['normal_font_file']).height
        x = pyImage.text(string, dpi=font['normal_font_size'], fontfile=font['normal_font_file'])
    return size


def textWrapper(text, font, writing_space_width, renderer_lib, first_line_offset_width=0):
    """
    Break given text into lines when the width of text in given font on that line gets bigger than the allowed max-width
    """
    words = text.split()                                 # Split the words by spaces
    lines = ['']                                         # Start forming lines of these words based on the allowed max-width
    for idx, word in enumerate(words):
        line_empty = not lines[-1]                       # Prepare a variable that indicates whether the current line is empty or not
        # Calculate "current_line_width"
        current_line_width = getFontSizeByLanguage(lines[-1] + word, font, renderer_lib)[0]
        if len(lines) == 1:
            current_line_width += first_line_offset_width

            # Append lines DS based on "current_line_width"
        if current_line_width < writing_space_width:
            # If line wasn't empty, make sure there is a space before the word
            space = "" if line_empty else " "
            lines[-1] += space + word
        else:
            if line_empty: lines[-1] = word          # if the word was already empty, update it (happens when the word itself is larger than allowed width)
            else:          lines.append(word)        # else append
    return lines


def getWrappedTextMaxHeightWidth(text, font, writing_space_width, renderer_lib):
    text_max_width, text_total_height = 0, 0
    wrapped_text_array = textWrapper(text, font, writing_space_width, renderer_lib)
    for line in wrapped_text_array:
        text_total_height += getFontSizeByLanguage(line, font, renderer_lib)[1]
        text_width_check = getFontSizeByLanguage(line, font, renderer_lib)[0]
        if text_width_check > text_max_width:
            text_max_width = text_width_check
    return wrapped_text_array, text_max_width, text_total_height


def renderTextOnImage(text, abs_x, abs_y, background_image, font_file, text_color, font_size, max_width, renderer_lib=1, manage_abs_y=None, manage_abs_x=None, max_height=None, text_resizable=False, hide_extra_text=False, font_family=None, get_details=False, custom_offset=2):
    """
    draw text on image on the basis of height width of a particular box and also make resizable to make best fit to the box
    The variables are used in method:
    text:                      your input text
    abs_x:                     absolute value of axis x to render text from
    abs_y:                     ablsolute value of axis y to render text from
    background_image:          background or base image to render text on it
    font_file:                 font_file to render text with this font
    text_color:                give your custom color for text
    font_size:                 give your own font size
    font_family:               this is font family name of the given font(like "Arial Bold" for Arial_Bold font)
    max_width:                 maximum width for given aria(box width where text is to render)
    renderer_lib:              this is text renderer library if value is "1" then it will use "pillow" lib and if vlaue is "2" then it will use pyvips to render the text
    manage_abs_x and y:        these variables are to manage axis x and y in the given box(hieght, width) on image if vlaue is "center" then text will be in center(with respect y) bellow:
    
    by default manage x and y   manage_x= default and y="center"  manage_x= default and y="down"  manage_x= "center" and y=default     manage_x= "right" and y=default    manage_x= "center" and y="center"
    __________________              ______________________          _____________________            ______________________                 ______________________          ______________________
    |text            |             |                     |         |                     |           |        text         |                |                 text|         |                     |
    |                |             |text                 |         |                     |           |                     |                |                     |         |        text         |
    |________________|             |_____________________|         |text ________________|           |_____________________|                |_____________________|         |_____________________|

    max_height:                 maximun height of the given box
    text_resizable:             It enamble the text resize to fit in the box according to height anbd width
    hide_extra_text:            removes extra text wich is overlapping the given box(in this situation text will not resize automatic)
    get_details:                return only details like(font, text_width, text_total_hieght)
    custom offset:              custom offset between two lines
    """
    
    if font_size is None:
        # There are situation when "font_size" is not known but the maximum height that a text will occupy is known. So with "text_resizable" set to true by default
        # the correct "font_size" will automatically be obtained. And so we make the task easy for the user by ignoring passing an explicit value for it.
        if max_height is None:
            raise Exception("Both 'font_size' and 'max_height' cannot be None")
        if int(renderer_lib) == 1:
            font_size = max_height
        else:
            font_size = max_height*7

    if int(renderer_lib) == 1:
        custom_offset = 0
        # background_image = Image.open(background_image)
        draw = ImageDraw.Draw(background_image)
        font = ImageFont.truetype(font_file, size=font_size)
    else:
        # background_image = pyImage.new_from_file(background_image)
        font = {'normal_font_file': font_file, 'normal_font_size': font_size}
    wrapped_text_array, text_width, text_total_height = getWrappedTextMaxHeightWidth(text, font, max_width, renderer_lib)

    if text_resizable:
        while (text_width > max_width or text_total_height>max_height) and font_size>0:                   # Limiting lines count by decreasing font_size and text_writing_space_width_in_pixel
            if int(renderer_lib) == 1:
                font_size -= 1
                font = ImageFont.truetype(font_file, size=font_size)
            else:
                font_size -= 1
                font.update({'normal_font_size': font_size})
            wrapped_text_array, text_width, text_total_height = getWrappedTextMaxHeightWidth(text, font, max_width, renderer_lib)
            text_total_height = text_total_height + (custom_offset*(len(wrapped_text_array)-1))
    
    if hide_extra_text:
        copy_text = "".join(wrapped_text_array)
        while (text_width > max_width or text_total_height>max_height) and font_size>0:                   # Limiting lines count by decreasing font_size and text_writing_space_width_in_pixel
            text = text[:-1]
            wrapped_text_array, text_width, text_total_height = getWrappedTextMaxHeightWidth(text, font, max_width, renderer_lib)
            text_total_height = text_total_height + (custom_offset*(len(wrapped_text_array)-1))
        if len("".join(wrapped_text_array)) != len(copy_text):
            wrapped_text_array[-1] = wrapped_text_array[-1][:-3] + "..."


    if get_details:
        return font, text_width, text_total_height
    if manage_abs_y and max_height:
        if manage_abs_y=="center" and (max_height-text_total_height)>0:
            abs_y = abs_y + (max_height-text_total_height)/2
        if manage_abs_y=="down" and (max_height-text_total_height)>0:
            abs_y = abs_y + (max_height-text_total_height)
    reset_abs_x = abs_x
    for line in wrapped_text_array:
        if manage_abs_x:
            text_line_width = getFontSizeByLanguage(line, font, renderer_lib)[0]
            if manage_abs_x=="center" and (max_width-text_line_width)>0:
                abs_x = reset_abs_x + (max_width-text_line_width)/2
            if manage_abs_x=="right" and (max_width-text_line_width)>0:
                abs_x = reset_abs_x + (max_width-text_line_width)
        if int(renderer_lib) == 1:
            text_height = font.getsize(line)[1]
            abs_y -= font.getoffset(line)[1]                                                # remove top y_offset value from abs_y to draw text from exact axis(x, y)
            draw.text((abs_x, abs_y), line, fill=text_color, font=font)
            abs_y += text_height + font.getoffset(line)[1]
        else:
            text_height = getFontSizeByLanguage(line, font, renderer_lib)[1]

            line = cgi.escape(line)                                                         # Here preparing string to render if any special symbol found then convert into html code for render like(& to &amp;)
            text = pyImage.text(line, dpi=font['normal_font_size'], font=font_family, fontfile=font_file, align = "centre") 
            # print(font_file, line, font['normal_font_size'])
            # we'll use that as the alpha scale down to make it transparent
            alpha = (text).cast("uchar")
            # make a blue rectangle the same size and tag as srgb
            overlay = text.new_from_image(list(text_color)).copy(interpretation="srgb")
            # attach the alpha
            overlay = overlay.bandjoin(alpha)
            # load an image and composite on the overlay
            background_image = background_image.composite2(overlay, 'over', x = abs_x, y = abs_y)
            abs_y += text_height + custom_offset
    return font, background_image

def genBannerImgs(text, input_img_folder_path, output_img_folder_path):    
    banner_absolute_values = {
        "text_1_ds": {
            "hide_extra_text": True,
            "manage_abs_x": None,
            "manage_abs_y": None,
            "font_family": "Poppins Regular",
            "font_size": 129,
            "font_file": "fonts/Poppins-Regular.ttf",
            "text_color": (0,0,0),
            "text": text[0],
            "abs_x": 402,
            "abs_y": 74,
            "max_width": 580,
            "max_height": 27
        },
        "text_2_ds": {
            "hide_extra_text": True,
            "manage_abs_x": None,
            "manage_abs_y": None,
            "font_family": "Poppins SemiBold",
            "font_size": 118,
            "font_file": "fonts/Poppins-SemiBold.ttf",
            "text_color": (0,0,0),
            "text": text[1],
            "abs_x": 402,
            "abs_y": 103,
            "max_width": 580,
            "max_height": 58
        },
        "text_3_ds": {
            "hide_extra_text": True,
            "manage_abs_x": None,
            "manage_abs_y": None,
            "font_family": "Poppins SemiBold",
            "font_size": 124,
            "font_file": "fonts/Poppins-SemiBold.ttf",
            "text_color": (0,0,0),
            "text": text[2],
            "abs_x": 402,
            "abs_y": 257,
            "max_width": 580,
            "max_height": 22
        }
    }

    banner_empty_imgs = ["1.jpg", "2.jpg", "3.jpg"]
    renderer_lib = 2
    img_file = "%s%s" % (input_img_folder_path, banner_empty_imgs[0])
    if int(renderer_lib) == 1:
        background_image = Image.open(img_file)
    else:
        background_image = pyImage.new_from_file(img_file)
    output_file = getCurrentImgFilename(path=output_img_folder_path)
    if os.path.exists(output_file):
        return
    for text_values in banner_absolute_values.values():
        args = [text_values["text"], text_values["abs_x"], text_values["abs_y"], background_image, text_values["font_file"], text_values["text_color"], text_values["font_size"], text_values["max_width"]]
        background_image = renderTextOnImage(*args, hide_extra_text=text_values["hide_extra_text"], manage_abs_y="down", renderer_lib=renderer_lib, max_height=text_values["max_height"], font_family=text_values["font_family"])[1]
    if int(renderer_lib) == 1:
        background_image.save(output_file)
    else:
        background_image.write_to_file(output_file)
    
    print("banner screentshot generated at: ", output_file)


def genMobileScreenShot(s_1_text, s_2_text, s_3_text, s_4_text, s_7_text, input_img_folder_path, output_img_folder_path):
    if not isinstance(s_1_text, list):
        s_1_text = [s_1_text]
    if not isinstance(s_2_text, list):
        s_2_text = [s_2_text]
    if not isinstance(s_3_text, list):
        s_3_text = [s_3_text]
    if not isinstance(s_4_text, list):
        s_4_text = [s_4_text]
    if not isinstance(s_7_text, list):
        s_7_text = [s_7_text]

    mobile_screen_ds = {
        "screen_1": {
            "text_1_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_1_text[0],
                "abs_x": 127,
                "abs_y": 760,
                "max_width": 235,
                "max_height": 38
            }
        },
        "screen_2": {
            "text_1_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": None,
                "font_family": "Arial Regular",
                "font_size": 70,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (255,255,255),
                "text": s_2_text[0],
                "abs_x": 115,
                "abs_y": 316,
                "max_width": 221,
                "max_height": 12
            }
        },
        "screen_3": {
            "text_1_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": None,
                "font_family": "Arial Regular",
                "font_size": 78,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_3_text[0],
                "abs_x": 150,
                "abs_y": 315,
                "max_width": 300,
                "max_height": 14
            }
        },
        "screen_4": {
            "text_1_ds": {
                "hide_extra_text": False,
                "manage_abs_x": "center",
                "manage_abs_y": "center",
                "font_family": "Arial Regular",
                "font_size": 84,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (255,255,255),
                "text": s_4_text[0],
                "abs_x": 127,
                "abs_y": 350,
                "max_width": 330,
                "max_height": 30
            },
            "text_2_ds": {
                "hide_extra_text": True,
                "manage_abs_x": "center",
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 75,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (255,255,255),
                "text": s_4_text[1],
                "abs_x": 126,
                "abs_y": 385,
                "max_width": 75,
                "max_height": 11
            },
            "text_3_ds": {
                "hide_extra_text": True,
                "manage_abs_x": "center",
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 75,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (255,255,255),
                "text": s_4_text[2],
                "abs_x": 247,
                "abs_y": 385,
                "max_width": 75,
                "max_height": 11
            },
            "text_4_ds": {
                "hide_extra_text": True,
                "manage_abs_x": "center",
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 75,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (255,255,255),
                "text": s_4_text[3],
                "abs_x": 370,
                "abs_y": 385,
                "max_width": 75,
                "max_height": 11
            },
            "text_5_ds": {
                "hide_extra_text": True,
                "manage_abs_x": "center",
                "manage_abs_y": "center",
                "font_family": "Arial Regular",
                "font_size": 54,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_4_text[4],
                "abs_x": 118,
                "abs_y": 488,
                "max_width": 118,
                "max_height": 8
            },
            "text_6_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color":  (0,0,0),
                "text": s_4_text[5],
                "abs_x": 125,
                "abs_y": 625,
                "max_width": 235,
                "max_height": 38
            },
            "text_7_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_4_text[6],
                "abs_x": 125,
                "abs_y": 713,
                "max_width": 235,
                "max_height": 38
            },
            "text_8_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_4_text[7],
                "abs_x": 125,
                "abs_y": 803,
                "max_width": 235,
                "max_height": 38
            }
        },
        "screen_7": {
            "text_1_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_7_text[0],
                "abs_x": 124,
                "abs_y": 367,
                "max_width": 235,
                "max_height": 38
            },
            "text_2_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_7_text[1],
                "abs_x": 124,
                "abs_y": 485,
                "max_width": 235,
                "max_height": 38
            },
            "text_3_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_7_text[2],
                "abs_x": 124,
                "abs_y": 605,
                "max_width": 235,
                "max_height": 38
            },
            "text_4_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_7_text[3],
                "abs_x": 124,
                "abs_y": 726,
                "max_width": 235,
                "max_height": 38
            },
            "text_5_ds": {
                "hide_extra_text": True,
                "manage_abs_x": None,
                "manage_abs_y": "down",
                "font_family": "Arial Regular",
                "font_size": 77,
                "font_file": "fonts/Arial-regular.ttf",
                "text_color": (0,0,0),
                "text": s_7_text[4],
                "abs_x": 124,
                "abs_y": 844,
                "max_width": 235,
                "max_height": 38
            }
        }
    }

    img_list = ["1", "2", "3", "4", "7"]
    renderer_lib = 2
    for idx in img_list:
        output_file = getCurrentImgFilename(path=output_img_folder_path)
        if os.path.exists(output_file):
            continue
        img_base_file = "%s%s.jpg" % (input_img_folder_path, idx)
        if int(renderer_lib) == 1:
            background_image = Image.open(img_base_file)
        else:
            background_image = pyImage.new_from_file(img_base_file)
        for text_values in mobile_screen_ds["screen_%s" % idx].values():
            args = [text_values["text"], text_values["abs_x"], text_values["abs_y"], background_image, text_values["font_file"], text_values["text_color"], text_values["font_size"], text_values["max_width"]]
            background_image = renderTextOnImage(*args, manage_abs_y=text_values["manage_abs_y"], manage_abs_x=text_values["manage_abs_x"], renderer_lib=renderer_lib, max_height=text_values["max_height"], hide_extra_text=text_values["max_height"], font_family=text_values["font_family"])[1]
        if int(renderer_lib) == 1:
            background_image.save(output_file)
        else:
            background_image.write_to_file(output_file)

        background_image.clear
        print("mobile screentshot generated at: ", output_file)


if __name__ == "__main__":
    if False:
        text = ["EduGorilla's IBPS RRB SO Marketing Test Series App", "Our IBPS RRB SO Marketing Test Series", "Features of our EduGorilla's IBPS Test Series App"]
        with open("./input_data/featured_graphics.csv", "r", newline='') as featured_graphics:
            text_data = list(csv.reader(featured_graphics, delimiter=','))
        print("len ::", len(text_data))
        z = ["com.edugorilla.upscmt", "com.edugorilla.multimedia_designing_mocktest", "com.edugorilla.mbatsicet", "com.edugorilla.dsgnata", "com.edugorilla.under_graduate_aptitude_test_ugat_mock_test", "com.edugorilla.gujarat_common_entrance_test_gcet_mock_tes"]
        t2 = text_data
        x = 0
        for data in text_data:
            
            IMG_COUNTER = 0
            output = data[1]
            # if d[1] == data[1]:
            #     if x>0 and (d[1] not in z):
            #         print("matrched===========", data[1], x)
            #         z.append(data[1])
                # x += 1
            if output in z:
                output += "_" + str(x)
                x += 1

            text = [data[2], data[3], data[4]]
            genBannerImgs(text, "./screens/banner/", output)
    if True:
        s_1_text = ["IBPS RRB Treasury Manager - Quiz 09th July"]
        s_2_text = ["IBPS RRB Treasury Manager Mock Test -1"]
        s_3_text = ["IBPS RRB Treasury Manager Mock Test -1"]
        s_4_text = ["IBPS RRB Treasury Manager", "746344", "2772", "98151+", "IBPS RRB Treasury Manager Mock Test -2", "IBPS RRB Treasury Manager Mock Test -2", "IBPS RRB Treasury Manager Mock Test -3", "IBPS RRB Treasury Manager Mock Test -4"]
        s_7_text = ["IBPS RRB Treasury Manager - Quiz 09th July"]
        
        with open("./input_data/Screen_shot_screen_1.csv", "r", newline='') as Screen_shot_screen_1:
            s1 = list(csv.reader(Screen_shot_screen_1, delimiter=','))
        with open("./input_data/Screen_shot_screen_2_3.csv", "r", newline='') as Screen_shot_screen_2:
            s2_3 = list(csv.reader(Screen_shot_screen_2, delimiter=','))
        with open("./input_data/Screen_shot_screen_4.csv", "r", newline='') as Screen_shot_screen_3:
            s4 = list(csv.reader(Screen_shot_screen_3, delimiter=','))
        with open("./input_data/Screen_shot_screen_7.csv", "r", newline='') as Screen_shot_screen_4:
            s7 = list(csv.reader(Screen_shot_screen_4, delimiter=','))
        Screen_shot_screen_1.close()
        Screen_shot_screen_2.close()
        Screen_shot_screen_3.close()
        Screen_shot_screen_4.close()
        for idx, data in enumerate(s7):
            IMG_COUNTER = 0
            s7[idx].append(s7[idx][-1].replace("11", "10"))
            print(s7[idx])
            output = s1[idx][1]
            if output == "None":
                output += "_" + str(s1[idx][0])
            s_1_text = s1[idx][-1]
            s_2_3_text = s2_3[idx][-1]
            s_4_text =s4[idx][2:]
            s_7_text = s7[idx][2:]        
        
            genMobileScreenShot(s_1_text, s_2_3_text, s_2_3_text, s_4_text, s_7_text, "./screens/hindi/", output)
