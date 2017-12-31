import subprocess
from PIL import Image, ImageDraw, ImageFont
import io
import math
import time


screen_command = 'adb exec-out screencap -p'


iter_step = 5


def same_color(color1, color2, color_diff=30):
    if color1[0] > 240 and color1[1]>240 and color1[2]>240: return False
    return sum(abs(color1[index] - color2[index]) for index in range(3)) < color_diff


def get_image(debug_file=None):
    if debug_file:
        image = Image.open(debug_file)
    else:
        process = subprocess.Popen(screen_command.split(), stdout=subprocess.PIPE)
        image_data, error = process.communicate()
        image = Image.open(io.BytesIO(image_data))
    return image


def not_common(pixels, x, y, background, shadow_color):
    color = pixels[x,y]
    return not same_color(color, background,color_diff=40) and not same_color(color, shadow_color, color_diff=15)


def one_jump(debug=None):
    image = get_image(debug)
    pixels = image.load()

    background = pixels[540, 300]
    # print('background', background)
    shadow_color = (134, 138, 167)

    # get the people position
    x_people = 0
    y_people = 0
    for y in range(1400, 1000, -iter_step):
        find = False
        for x in range(1, image.width, iter_step):
            if same_color(pixels[x, y], (55, 55, 95), color_diff=10):
                x_people, y_people = x+15, y-17
                find = True
                break
        if find:
            break
    # print('people position:', x_people, y_people)

    for x in range(1, x_people, iter_step):
        if x <= x_people:
            y = int(y_people - (x_people - x) / 1.82)
        else:
            y = int(y_people - (x-x_people)/1.77)
        if not_common(pixels, x, y, background, shadow_color):
            # print(color)
            left_x, left_y = x+28, y+10
            break

    for x in range(image.width-5, x_people+2, -iter_step):
        y = int(y_people - (x-x_people)/1.75)
        if not_common(pixels, x, y, background, shadow_color):
            # print(color)
            if x < image.width-10:
                ri_x, ri_y = x-28, y+10
            else:
                ri_x, ri_y = x+28, y-10
            break
    if x_people - left_x > ri_x -x_people:
        x_target, y_target = left_x, left_y
        is_left = True
    else:
        x_target, y_target = ri_x, ri_y
        is_left = False

    x_min, x_max = x_target, x_target
    while x_min > 10 and not_common(pixels, x_min, y_target, background, shadow_color):
        x_min -= 5
    while x_max < image.width-10 and not_common(pixels, x_max, y_target, background, shadow_color):
        x_max += 5
    x_target = (x_max + x_min) / 2

    # y_min, y_max = y_target, y_target
    # while not_common(pixels, x_target, y_min, background, shadow_color):
    #     y_min -=5
    # while y_max < image.height - 10 and not_common(pixels, x_target, y_max, background, shadow_color):
    #     y_max +=5
    # # print('target position:', x_target, y_target)
    # y_target = (y_min + y_max) / 2
    distance = math.sqrt((x_people - x_target)**2+(y_people-y_target)**2)

    # if distance < 400:
    #     if is_left:
    #         press_time = 1.15*distance
    #     else:
    #         press_time = 1.1*distance
    # elif distance < 600:
    #     press_time = 1.2*distance
    # else:
    #     press_time = 1.2*distance
    if distance < 350:
        press_time = 1.37 * distance
    elif distance < 500:
        press_time = 1.35*distance
    else:
        press_time = 1.33*distance

    if not debug:
        d = ImageDraw.Draw(image)
        r = 5
        d.ellipse((x_people-r,y_people-r,x_people+r, y_people+r), fill=(255,0,0))
        d.ellipse((x_target-r,y_target-r,x_target+r, y_target+r), fill=(255,0,0))
        text_str = 'distance, time: {} {} '.format( distance, press_time)
        fnt = ImageFont.truetype("arial.ttf", 40)
        d.text((100, 100), text_str, font=fnt, fill=(0, 0, 0, 255))
        screen_path = 'data/screen{}.png'.format(int(time.time()))
        image.save(screen_path, 'png')

    print(text_str)

    press_command = 'adb shell input touchscreen swipe 170 187 170 187 {}'.format(int(press_time))

    process = subprocess.Popen(press_command.split(), stdout=subprocess.PIPE)
    res, error = process.communicate()
    # print(res, error)
    return x_people, y_people, press_time, distance


if __name__ == '__main__':
    old_x = None
    old_y = None
    old_time = None
    while True:
        try:
            x, y, t, d = one_jump()
        except Exception:
            pass
        # if old_x is not None:
        #     true_distance = math.sqrt((x - old_x)**2+(y-old_y)**2)
        #     f = open('time_distance.csv', 'a')
        #     f.write('{},{},\n'.format(old_time, true_distance))
        #     f.close()
        # old_x, old_y, old_time = x, y, t
        time.sleep(1.5)