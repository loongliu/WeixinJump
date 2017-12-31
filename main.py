import subprocess
from PIL import Image, ImageDraw
import io
import math
import time

# params
people_ymin, people_ymax = 1000, 1400
people_radius = (15, 17)

left_x_y = 1.82
right_x_y = 1.75

r_time_distance = 1.35


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
    for y in range(people_ymax, people_ymin, -iter_step):
        find = False
        for x in range(1, image.width, iter_step):
            if same_color(pixels[x, y], (55, 55, 95), color_diff=10):
                x_people, y_people = x+people_radius[0], y-people_radius[1]
                find = True
                break
        if find:
            break
    # print('people position:', x_people, y_people)

    for x in range(1, x_people, iter_step):
        y = int(y_people - (x_people - x) / left_x_y)
        if not_common(pixels, x, y, background, shadow_color):
            left_x, left_y = x+2*people_radius[0], y+people_radius[1]
            break

    for x in range(image.width-5, x_people+2, -iter_step):
        y = int(y_people - (x-x_people)/right_x_y)
        if not_common(pixels, x, y, background, shadow_color):
            if x < image.width-10:
                ri_x, ri_y = x-2*people_radius[0], y+people_radius[1]
            else:
                ri_x, ri_y = x+2*people_radius[0], y-people_radius[1]
            break
    if x_people - left_x > ri_x -x_people:
        x_target, y_target = left_x, left_y
    else:
        x_target, y_target = ri_x, ri_y

    x_min, x_max = x_target, x_target
    while x_min > 10 and not_common(pixels, x_min, y_target, background, shadow_color):
        x_min -= 5
    while x_max < image.width-10 and not_common(pixels, x_max, y_target, background, shadow_color):
        x_max += 5
    x_target = (x_max + x_min) / 2

    distance = math.sqrt((x_people - x_target)**2+(y_people-y_target)**2)

    press_time = r_time_distance * distance
    if not debug:
        d = ImageDraw.Draw(image)
        r = 5
        d.ellipse((x_people-r,y_people-r,x_people+r, y_people+r), fill=(255,0,0))
        d.ellipse((x_target-r,y_target-r,x_target+r, y_target+r), fill=(255,0,0))
        screen_path = 'data/screen{}.png'.format(int(time.time()))
        image.save(screen_path, 'png')

    text_str = 'distance, time: {} {} '.format( distance, press_time)
    print(text_str)

    press_command = 'adb shell input touchscreen swipe 170 187 170 187 {}'.format(int(press_time))

    process = subprocess.Popen(press_command.split(), stdout=subprocess.PIPE)
    process.communicate()
    # print(res, error)


if __name__ == '__main__':
    while True:
        try:
            one_jump()
        except Exception:
            pass
        time.sleep(1.5)