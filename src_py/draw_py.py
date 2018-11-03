'''Pygame Drawing algorithms written in Python. (Work in Progress)

Implement Pygame's Drawing Algorithms in a Python version for testing
and debugging.
'''
# FIXME : the import of the builtin math module is broken, even with :
# from __future__ import relative_imports
# from math import floor, ceil, trunc

def ceil(x):
    int_x = int(x)
    return int_x if (int_x == x) else int_x + 1


#   H E L P E R   F U N C T I O N S    #

# fractional part of x

def frac(x):
    '''return fractional part of x'''
    return x - int(x)

def inv_frac(x):
    '''return inverse fractional part of x'''
    return 1 - (x - int(x)) # eg, 1 - frac(x)


#   L O W   L E V E L   D R A W   F U N C T I O N S   #
# (They are too low-level to be translated into python, right?)

def set_at(surf, x, y, color):
    surf.set_at((x, y), color)


def draw_pixel(surf, x, y, color, bright, blend=True):
    other_col = surf.get_at((x, y)) if blend else (0, 0, 0, 0)
    new_color = tuple((bright * col + (1 - bright) * pix)
                      for col, pix in zip(color, other_col))
    # FIXME what should happen if either color or surf_col has some alpha ?
    surf.set_at((x, y), new_color)


def _drawhorzline(surf, color, x_from, y, x_to):
    if x_from == x_to:
        surf.set_at((x_from, y), color)
        return

    start, end = (x_from, x_to) if x_from <= x_to else (x_to, x_from)
    for x in range(start, end + 1):
        surf.set_at((x, y), color)


def _drawvertline(surf, color, x, y_from, y_to):
    if y_from == y_to:
        surf.set_at((x, y_from), color)
        return

    start, end = (y_from, y_to) if y_from <= y_to else (y_to, y_from)
    for y in range(start, end + 1):
        surf.set_at((x, y), color)


#    I N T E R N A L   D R A W   L I N E   F U N C T I O N S    #

def _clip_and_draw_horzline(surf, color, x_from, y, x_to):
    '''draw clipped horizontal line.'''
    # check Y inside surf
    clip = surf.get_clip()
    if y < clip.y or y >= clip.y + clip.h:
        return

    x_from = max(x_from, clip.x)
    x_to = min(x_to, clip.x + clip.w - 1)

    # check any x inside surf
    if x_to < clip.x or x_from >= clip.x + clip.w:
        return

    _drawhorzline(surf, color, x_from, y, x_to)


def _clip_and_draw_vertline(surf, color, x, y_from, y_to):
    '''draw clipped vertical line.'''
    # check X inside surf
    clip = surf.get_clip()

    if x < clip.x or x >= clip.x + clip.w:
        return

    y_from = max(y_from, clip.y)
    y_to = min(y_to, clip.y + clip.h - 1)

    # check any y inside surf
    if y_to < clip.y or y_from >= clip.y + clip.h:
        return

    _drawvertline(surf, color, x, y_from, y_to)

# These constans xxx_EDGE are "outside-the-bounding-box"-flags
LEFT_EDGE = 0x1
RIGHT_EDGE = 0x2
BOTTOM_EDGE = 0x4
TOP_EDGE = 0x8

def encode(x, y, left, top, right, bottom):
    '''returns a code that defines position with respect to a bounding box'''
    # we use the fact that python interprets booleans (the inqualities)
    # as 0/1, and then multiply them with the xxx_EDGE flags
    return ((x < left) *  LEFT_EDGE +
            (x > right) * RIGHT_EDGE +
            (y < top) * TOP_EDGE +
            (y > bottom) * BOTTOM_EDGE)


INSIDE = lambda a: not a
ACCEPT = lambda a, b: not (a or b)
REJECT = lambda a, b: a and b


def clip_line(line, left, top, right, bottom, use_float=False):
    '''Algorithm to calculate the clipped line.

    We calculate the coordinates of the part of the line segment within the
    bounding box (defined by left, top, right, bottom). The we write
    the coordinates of the line segment into "line", much like the C-algorithm.
    With `use_float` True, clip_line is usable for float-clipping.

    Returns: true if the line segment cuts the bounding box (false otherwise)
    '''
    assert isinstance(line, list)
    x1, y1, x2, y2 = line
    dtype = float if use_float else int

    while True:
        # the coordinates are progressively modified with the codes,
        # until they are either rejected or correspond to the final result.
        code1 = encode(x1, y1, left, top, right, bottom)
        code2 = encode(x2, y2, left, top, right, bottom)

        if ACCEPT(code1, code2):
            # write coordinates into "line" !
            line[:] = x1, y1, x2, y2
            return True
        if REJECT(code1, code2):
            return False

        # We operate on the (x1, y1) point, and swap if it is inside the bbox:
        if INSIDE(code1):
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            code1, code2 = code2, code1
        if (x2 != x1):
            m = (y2 - y1) / float(x2 - x1)
        else:
            m = 1.0
        # Each case, if true, means that we are outside the border:
        # calculate x1 and y1 to be the "first point" inside the bbox...
        if code1 & LEFT_EDGE:
            y1 += dtype((left - x1) * m)
            x1 = left
        elif code1 & RIGHT_EDGE:
            y1 += dtype((right - x1) * m)
            x1 = right
        elif code1 & BOTTOM_EDGE:
            if x2 != x1:
                x1 += dtype((bottom - y1) / m)
            y1 = bottom
        elif code1 & TOP_EDGE:
            if x2 != x1:
                x1 += dtype((top - y1) / m)
            y1 = top


def _clip_and_draw_line(surf, rect, color, pts):
    '''clip the line into the rectangle and draw if needed.

    Returns true if anything has been drawn, else false.'''
    # "pts" is a list with the four coordinates of the two endpoints
    # of the line to be drawn : pts = x1, y1, x2, y2.
    # The data format is like that to stay closer to the C-algorithm.
    if not clip_line(pts, rect.x, rect.y, rect.x + rect.w - 1,
                    rect.y + rect.h - 1):
        # The line segment defined by "pts" is not crossing the rectangle
        return 0
    if pts[1] == pts[3]:  #  eg y1 == y2
        _drawhorzline(surf, color, pts[0], pts[1], pts[2])
    elif pts[0] == pts[2]: #  eg x1 == x2
        _drawvertline(surf, color, pts[0], pts[1], pts[3])
    else:
        _draw_line(surf, color, pts[0], pts[1], pts[2], pts[3])
    return 1


def _draw_line(surf, color, x1, y1, x2, y2):
    '''draw a non-horizontal line (without anti-aliasing).'''
    # Variant of https://en.wikipedia.org/wiki/Bresenham's_line_algorithm
    #
    # This strongly differs from craw.c implementation, because we use a
    # "slope" variable (instead of delta_x and delta_y) and a "error" variable.
    # And we can not do pointer-arithmetic with "BytesPerPixel", like in
    # the C-algorithm.
    if x1 == x2:
        # This case should not happen...
        raise ValueError

    slope = abs((y2 - y1) / (x2 - x1))
    error = 0.0

    if slope < 1:
        # Here, it's a rather horizontal line

        # 1. check in which octants we are & set init values
        if x2 < x1:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        y = y1
        dy_sign = 1 if (y1 < y2) else -1

        # 2. step along x coordinate
        for x in range(x1, x2 + 1):
            set_at(surf, x, y, color)
            error += slope
            if error >= 0.5:
                y += dy_sign
                error -= 1
    else:
        # Case of a rather vertical line

        # 1. check in which octants we are & set init values
        if y1 > y2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        x = x1
        slope = 1 / slope
        dx_sign = 1 if (x1 < x2) else -1

        # 2. step along y coordinate
        for y in range(y1, y2 + 1):
            set_at(surf, x, y, color)
            error += slope
            if error >= 0.5:
                x += dx_sign
                error -= 1


def _draw_aaline(surf, color, from_x, from_y, to_x, to_y, blend):
    '''draw a non-horizontal anti-aliased line.'''
    dx = to_x - from_x
    dy = to_y - from_y

    if dx == 0 and dy == 0:
        set_at(surf, from_x, to_x, color)
        return

    if abs(dx) >= abs(dy):
        if from_x > to_x:
            from_x, to_x = to_x, from_x
            from_y, to_y = to_y, from_y
            dx = -dx
            dy = -dy

        slope = dy / dx
        def draw_two_pixel(x, float_y, factor):
            y = int(float_y)
            draw_pixel(surf, x, y, color, factor * inv_frac(float_y), blend)
            draw_pixel(surf, x, y + 1, color, factor * frac(float_y), blend)

        # A and G are respectively left and right to the "from" point, but
        # with integer-x-coordinate, (and only if from_x is not integer).
        # Hence they appear in following order on the line in general case:
        #  A   from-pt    G    .  .  .        to-pt    S
        #  |------*-------|--- .  .  . ---|-----*------|-
        G_x = ceil(from_x)
        G_y = from_y +  (from_x - G_x) * slope
        A_x, A_y = int(from_x), G_y - slope

        # 0. Special case : both from_x and to_x are in the same pixel
        if to_x < G_x:
            draw_two_pixel(A_x, A_y, dx)
            return

        # 1. Draw start of the segment
        if G_x != from_x:
            # we draw only if we have a non-integer-part at start of the line
            draw_two_pixel(A_x, A_y, inv_frac(from_x))

        # 2. Draw end of the segment: we add one pixel for homogenity reasons
        rest = frac(to_x)
        S_x, S_y = int(to_x) + 1, from_y + slope * (dx + 1 - rest)
        if S_x != to_x + 1:
            # Again we draw only if we have a non-integer-part
            draw_two_pixel(S_x, S_y, rest)

        # 3. loop for other points
        for x in range(G_x, S_x):
            print('  + Loop case', x)
            y = G_y + slope * (x - G_x)
            draw_two_pixel(x, y, 1)

    else:
        if from_y > to_y:
            from_x, to_x = to_x, from_x
            from_y, to_y = to_y, from_y
            dx = -dx
            dy = -dy

        slope = dx / dy

        def draw_two_pixel(float_x, y, factor):
            x = int(float_x)
            draw_pixel(surf, x, y, color, factor * inv_frac(float_x), blend)
            draw_pixel(surf, x + 1, y, color, factor * frac(float_x), blend)

        G_y = ceil(from_y)
        G_x = from_x + slope * (G_y - from_y)
        A_x, A_y = G_x - slope, int(from_y)

        # 0. Special case : both from_x and to_x are in the same pixel
        if to_y < G_y:
            draw_two_pixel(A_x, A_y, dy)
            return

        # 1. Draw start of the segment
        if G_y != from_y:
            draw_two_pixel(A_x, A_y, inv_frac(from_y))

        # 2. Draw end of the segment
        rest = frac(to_y)
        S_x, S_y = from_x + slope * (dy + 1 - rest), int(to_y) + 1
        if S_x != to_y + 1:
            draw_two_pixel(S_x, S_y, rest)

        # 3. loop for other points
        for y in range(G_y, S_y):
            x = G_x + slope * (y - G_y)
            draw_two_pixel(x, y, 1)


def _clip_and_draw_line_width(surf, rect, color, width, line):
    yinc = xinc = 0
    if abs(line[0] - line[2]) > abs(line[1] - line[3]):
        yinc = 1
    else:
        xinc = 1
    newpts = line[:]
    if _clip_and_draw_line(surf, rect, color, newpts):
        anydrawn = 1
        frame = newpts[:]
    else:
        anydrawn = 0
        frame = [10000, 10000, -10000, -10000]

    for loop in range(1, width // 2 + 1):
        newpts[0] = line[0] + xinc * loop
        newpts[1] = line[1] + yinc * loop
        newpts[2] = line[2] + xinc * loop
        newpts[3] = line[3] + yinc * loop
        if _clip_and_draw_line(surf, rect, color, newpts):
            anydrawn = 1
            frame[0] = min(newpts[0], frame[0])
            frame[1] = min(newpts[1], frame[1])
            frame[2] = max(newpts[2], frame[2])
            frame[3] = max(newpts[3], frame[3])

        if loop * 2 < width:
            newpts[0] = line[0] - xinc * loop
            newpts[1] = line[1] - yinc * loop
            newpts[2] = line[2] - xinc * loop
            newpts[3] = line[3] - yinc * loop
            if _clip_and_draw_line(surf, rect, color, newpts):
                anydrawn = 1
                frame[0] = min(newpts[0], frame[0])
                frame[1] = min(newpts[1], frame[1])
                frame[2] = max(newpts[2], frame[2])
                frame[3] = max(newpts[3], frame[3])

    return anydrawn


#    D R A W   L I N E   F U N C T I O N S    #

def draw_aaline(surf, color, from_point, to_point, blend):
    '''draw anti-aliased line between two endpoints.'''
    line = [from_point[0], from_point[1], to_point[0], to_point[1]]
    rect = surf.get_clip()
    if not clip_line(line, rect.x, rect.y, rect.x + rect.w - 1,
                     rect.y + rect.h - 1, use_float=True):
        return # TODO Rect(rect.x, rect.y, 0, 0)
    _draw_aaline(surf, color, line[0], line[1], line[2], line[3], blend)
    return # TODO Rect(-- affected area --)


#   M U L T I L I N E   F U N C T I O N S   #

def draw_lines(surf, color, closed, points, width):

    length = len(points)
    if length <= 2:
        raise TypeError
    line = [0] * 4  # store x1, y1 & x2, y2 of the lines to be drawn

    x, y = points[0]
    left = right = line[0] = x
    top = bottom = line[1] = y

    for loop in range(1, length):
        line[0] = x
        line[1] = y
        x, y = points[loop]
        line[2] = x
        line[3] = y
        if _clip_and_draw_line_width(surf, surf.get_clip(), color, width, line):
            left = min(line[2], left)
            top = min(line[3], top)
            right = max(line[2], right)
            bottom = max(line[3], bottom)

    if closed:
        line[0] = x
        line[1] = y
        x, y = points[0]
        line[2] = x
        line[3] = y
        _clip_and_draw_line_width(surf, surf.get_clip(), color, width, line)

    return  # TODO Rect(...)


def draw_polygon(surface, color, points, width):
    if width:
        draw_lines(surface, color, 1, points, width)
        return  # TODO Rect(...)
    num_points = len(points)
    point_x = [x for x, y in points]
    point_y = [y for x, y in points]

    miny = min(point_y)
    maxy = max(point_y)

    if miny == maxy:
        minx = min(point_x)
        maxx = max(point_x)
        _clip_and_draw_horzline(surface, color, minx, miny, maxx)
        return  # TODO Rect(...)

    for y in range(miny, maxy + 1):
        x_intersect = []
        for i in range(num_points):
            i_prev = i - 1 if i else num_points - 1

            y1 = point_y[i_prev]
            y2 = point_y[i]

            if y1 < y2:
                x1 = point_x[i_prev]
                x2 = point_x[i]
            elif y1 > y2:
                y2 = point_y[i_prev]
                y1 = point_y[i]
                x2 = point_x[i_prev]
                x1 = point_x[i]
            else:  # special case handled below
                continue

            if ( ((y >= y1) and (y < y2))  or ((y == maxy) and (y <= y2))) :
                x_sect = (y - y1) * (x2 - x1) // (y2 - y1) + x1
                x_intersect.append(x_sect)

        x_intersect.sort()
        for i in range(0, len(x_intersect), 2):
            _clip_and_draw_horzline(surface, color, x_intersect[i], y,
                             x_intersect[i + 1])

    # special case : horizontal border lines
    for i in range(num_points):
        i_prev = i - 1 if i else num_points - 1
        y = point_y[i]
        if miny < y == point_y[i_prev] < maxy:
            _clip_and_draw_horzline(surface, color, point_x[i], y, point_x[i_prev])

    return  # TODO Rect(...)
