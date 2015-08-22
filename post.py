#!/usr/bin/python
#
# Sudoku game post processing module.
#
# This module processes the JSON formatted output of the main
# sudoku game and generates js for web based rendering.
# 

import sys
import yaml
import re
import os
import tempfile
from datetime import datetime
from BeautifulSoup import BeautifulSoup as bs

def parse_output(file, html = True):
    # Extract the json data.
    fh = open(file, "r")
    data = ""
    seen = False
    for line in fh:
        if not seen:
            if line.startswith("post attack:"):
                seen = True
            continue
        data += line
        if line.startswith("}"):
            break

    # Load the json data (use yaml to rid of unicode strings).
    tree = yaml.safe_load(data)

    # Locate the snaps.
    snaps = None
    for attr in tree["attrs"]:
        if attr["hook"] == "HK.SNAP":
            snaps = attr["data"]
            break

    # Process the snaps.
    i = 0
    for snap in snaps:
        process_snap(snap, i, html)
        i += 1
        
def process_snap(snap, i, html = True):
    if html:
        start_pre()

    # Dump the snap.
    show_snap(snap)
    if not html:
        print "--------------------------------------------"
        return

    end_pre()

    # Start JS section.
    start_script()

    # Initialize board.
    sudoku = snap["snap"]
    create_board(sudoku, i)

    action = snap["action"]
    if action:
        # Strategy specific reason.
        s = snap["strategy"]
        r = snap["reason"]
        if s == "ST.NAKED-GROUP":
            naked_group(r)
        elif s == "ST.HIDDEN-GROUP":
            hidden_group(r)
        elif s == "ST.Y-WING":
            y_wing(r)
        elif s == "ST.XY-CHAIN":
            xy_chain(r)
        elif s == "ST.INTERSECTION":
            intersection(r)
        elif s == "ST.XYZ-WING":
            xyz_wing(r)
        elif s == "ST.WXYZ-WING":
            wxyz_wing(r)
        elif s == "ST.INTERSECTION":
            intersection(r)
        elif s == "ST.X-WING" or s == "ST.SWORD-FISH" or \
                s == "ST.JELLY-FISH" or s == "ST.FINNED X-WING" or \
                s == "ST.FINNED SWORD-FISH":
            fish(s, r)
        elif s == "ST.X-CYCLE" or s == "ST.GROUPED-X-CYCLE" or \
                s == "ST.AIC" or s == "ST.GROUPED-AIC":
            aic(s, r)
        elif s == "ST.DIGIT FORCING-CHAIN" or s == "ST.NISHIO FORCING-CHAIN":
            forcing_chain(s, r)
        elif s == "ST.APE":
            ape(r, action)
        elif s == "ST.SIMPLE-COLORING" or s == "ST.3D-MEDUSA":
            medusa(s, r)
        elif s == "ST.UNIQUE-RECTANGLE":
            unique_rectangle(r)
        elif s == "ST.ALS":
            als(r)

        # Action.
        show_action(action)

    end_script()  

    # Separator.
    add_separator()
    add_pagebreak()

def create_board(sudoku, i = None):
    src = [
        "var sudoku = \"{0}\"".format(sudoku),
        "var element = " + ("\"sudoku\"" if i is None else "\"step-{0}\"".format(i)),
        "board = new Board(sudoku, element)",
        "board.display()"
        ]
    print "\n".join(src)

def show_snap(snap):
    print "strategy: {0}".format(snap["strategy"])
    print "action: {0}".format(snap["action"])
    reason = snap["reason"]
    print "reason: {0}".format(dict((k, v) for k, v in reason.items()
                                    if not k.startswith("__") and not k.endswith("__"))
                               if isinstance(reason, dict) else reason)

def show_action(action):
    add_comment("action")
    for a in action:
        highlight_hints(a["node"], a["hints"], "action")

def naked_group(reason):
    add_comment("ST.NAKED-GROUP")
    hints = reason["hints"]
    nodes = reason["group"]
    for node in nodes:
        highlight_hints(node, hints, "reason")

def hidden_group(reason):
    add_comment("ST.HIDDEN-GROUP")
    hints = reason["hints"]
    nodes = reason["group"]
    for node in nodes:
        highlight_hints(node, hints, "reason")

def y_wing(reason):
    add_comment("ST.Y-WING")
    hint = reason["hint"]
    xz = reason["xz"]
    yz = reason["yz"]
    xy = reason["xy"]
    for node in [xy, xz, yz]:
        highlight_hints(node, hint, "reason")
    connect_nodes(xy, xz);
    connect_nodes(xy, yz);

def xyz_wing(reason):
    add_comment("ST.XYZ-WING")
    hint = reason["hint"]
    xz = reason["xz"]
    yz = reason["yz"]
    xyz = reason["xyz"]
    for node in [xyz, xz, yz]:
        highlight_hints(node, hint, "reason")
    connect_nodes(xyz, xz);
    connect_nodes(xyz, yz);

def wxyz_wing(reason):
    add_comment("ST.WXYZ-WING")
    hint = reason["hint"]
    hinge = reason["hinge"]
    wing = reason["wing"]
    for node in wing:
        highlight_hints(node, hint, "reason")
    for node in hinge:
        highlight_hints(node, hint, "reason_2");

def xy_chain(reason):
    add_comment("ST.XY-CHAIN")
    hint = reason["hint"]
    xz = reason["xz"]
    yz = reason["yz"]
    chain = reason["chain"]
    for node in [xz, yz]:
        highlight_hints(node, hint, "reason")
    prev = xz
    for node in chain:
        highlight_hints(node, [], "reason")
        connect_nodes(prev, node)
        prev = node
    connect_nodes(prev, yz)

def intersection(reason):
    add_comment("ST.INTERSECTION")
    hint = reason["hints"]
    lots = reason["lots"]
    nodes = reason["nodes"]
    for node in nodes:
        highlight_hints(node, hint, "reason", False)
    for lot in lots:
        lineStyle = "new LineStyle(null, null, Decorator.boundColor, null)"
        highlight_lot(lot, lineStyle)

def fish(strategy, reason):
    add_comment(strategy)
    hints = reason["hints"]
    plots = reason["plots"]
    fin = reason["fin"]
    for plot in plots:
        lineStyle = "new LineStyle(null, null, Decorator.boundColor, null)"
        highlight_group(plot["nodes"], lineStyle)
        for node in plot["nodes"]:
            highlight_hints(node, hints, "reason", False)
    if fin:
        for node in fin:
            highlight_hints(node, hints, "reason_2")

def aic(strategy, reason):
    add_comment(strategy)
    chain = reason["__chain__"]

    # Mismatching head and tail links indicates this is a contig
    # chain. Append the head to the end of the chain to close it.
    if chain[0][0] != chain[-1][0]:
        chain.append(chain[0])
    else:
        # True first link indicates this is a discontig weak chain.
        # Remove the first link and add the second link to the end.
        if chain[0][1]:
            chain = chain[1:]
            chain.append(chain[0])

    highlight_chain(chain)

def forcing_chain(strategy, reason):
    add_comment(strategy)
    chains = reason["__chain__"]
    for chain in chains:
        lineColor = None
        curve = None
        if chain != chains[0]:
            lineColor = "solidLineColor_2"
            curve = "lineCurve_2"
        highlight_chain(chain, lineColor, curve)

def ape(reason, action):
    add_comment("ST.APE")
    pair = reason["pair"]
    excl = reason["excl"]
    for x in pair:
        highlight_node(x, "reason")
    for act in action:
        i = pair.index(act["node"])
        for e in excl:
            candidate, als = e
            if candidate[i] in act["hints"]:
                for a in als:
                    highlight_hints(a, candidate, "reason_2")

def medusa(strategy, reason):
    add_comment(strategy)
    chain = reason["__chain__"]

    # First pass highlight the links.
    for linkgroup in chain:
        (node, hint), color = linkgroup[0]
        style = "reason" if color else "reason_2"
        highlight_hints(node, [hint], style)

    # Second pass connect the links.
    for linkgroup in chain:
        (node, hint), color = linkgroup[0]
        for toloc in linkgroup[1]:
            (n, h), c = toloc
            connect_groups([node], hint, [n], h, color)

def unique_rectangle(reason):
    add_comment("ST.UNIQUE-RECTANGLE")
    hints = reason["hints"]
    floor = reason["floor"]
    roof = reason["roof"]

    for node in floor:
        highlight_hints(node, hints, "reason")

    for node in roof:
        highlight_hints(node, hints, "reason_2")

def als(reason):
    add_comment("ST.ALS")
    hints = reason["rcs"]
    als1 = reason["als1"]
    als2 = reason["als2"]

    for node in als1:
        highlight_hints(node, hints, "reason")

    for node in als2:
        highlight_hints(node, hints, "reason_2")

def highlight_node(node, type):
    print "board.highlightNodeBorder({0}, Decorator.{1})".format(node_ident(node), type)

def highlight_hints(node, hints, type, hintBorder = False, nodeBorder = True):
    src = []
    id = node_ident(node)
    if nodeBorder:
        src.append("board.highlightNodeBorder({0}, Decorator.{1})".format(id, type))
    if hintBorder:
        src.append("board.highlightHintBorder({0}, {1}, Decorator.{2})".format(id, hints, type))
    src.append("board.highlightHintFill({0}, {1}, Decorator.{2})".format(id, hints, type))
    print "\n".join(src)

def highlight_group(nodes, style = None):
    print "board.groupNodes({0}{1})".format(group_ident(nodes),
                                            ", " + style if style else "")

def highlight_lot(lot, style = None):
    lineStyle = ", " + style if style else ""
    if lot in "ABCDEFGHJ":
        print "board.highlightRow({0}{1})".format("ABCDEFGHJ".index(lot), lineStyle)
    elif lot in "123456789":
        print "board.highlightCol({0}{1})".format("123456789".index(lot), lineStyle)
    elif lot in "abcdefghj":
        print "board.highlightBox({0}{1})".format("abcdefghj".index(lot), lineStyle)

def connect_nodes(node1, node2):
    print "board.connectNodes({0}, {1})".format(node_ident(node1), node_ident(node2))

def connect_groups(group1, hint1, group2, hint2, color, style = None):
    print "board.connectGroups({0}, {1}, {2}, {3}{4})".format(
        group_ident(group1), hint1, group_ident(group2), hint2,
        ", " + style if style else "")

def highlight_chain(chain, lineColor = None, curve = None):
    # First pass highlight the links.
    for loc in chain:
        (group, hint), color = loc
        borderStyle = "reason" if color else "reason_2"
        if len(group) == 1:
            highlight_hints(group[0], [hint], borderStyle, loc == chain[0])
        else:
            lineStyle = "new LineStyle(null, null, Decorator.{0}, null)".format(
                "boundColor" if color else "boundColor_2")
            highlight_group(group, lineStyle)
            for node in group:
                highlight_hints(node, [hint], borderStyle, loc == chain[0], False)

    # Second pass draw connections. For some reason, mixing group
    # highlighting (rectangle drawing on the canvas encompassing
    # the nodes) and line drawing triggers a bug in chrome that
    # ends up showing additional line segments.
    prev = None
    for loc in chain:
        (group, hint), color = loc
        if prev:
            (g, h), c = prev
            lineStyle = "new LineStyle(Decorator.{0}, {1}, {2}, {3})".format(
                "strokeSolid" if color else "strokeDouble",
                "Decorator." + curve if curve else "null",
                "Decorator." + lineColor if lineColor else "null",
                "Decorator.lineGradient")
            connect_groups(g, h, group, hint, color, lineStyle)
        prev = loc

def node_ident(node):
    match = re.match(r"([A-HJ])([1-9])", node)
    if match:
        x = "ABCDEFGHJ".index(match.group(1))
        y = int(match.group(2)) - 1
    else:
        match = re.match(r"[rR]([1-9])[cC]([1-9])", node)
        if match:
            x = int(match.group(1)) - 1
            y = int(match.group(2)) - 1
    return "{{x: {0}, y: {1}}}".format(x, y)

def group_ident(group):
    return "[{0}]".format(", ".join(node_ident(node) for node in group))

def add_comment(c):
    print "// {0}".format(c)

def add_separator():
    print "<hr/>"

def add_pagebreak():
    print "<p style=\"page-break-after:always;\"></p>"

def start_script():
    print "<script>"

def end_script():
    print "</script>"

def start_pre():
    print "<pre>"

def end_pre():
    print "</pre>"

def start_html(js, css):
    print "<html>"
    print "<link href=\"{0}\" type=\"text/css\" rel=\"stylesheet\">".format(css)
    print "<script type=\"text/javascript\" src=\"{0}\">".format(js)
    print "</script>"

def start_body():
    print "<body>"

def end_body():
    print "</body>"

def end_html():
    print "</html>"

def show_title():
    print "<h1>My Sudoku Solver</h1>"

def show_input(sudoku):
    print datetime.now().strftime("%I:%M%p on %B %d, %Y") + "<br>"
    print "You entered: " + sudoku + "<br>"
    start_script()
    create_board(sudoku)
    end_script()

def generate_html(sudoku, out):
    start_html("sudoku.js", "sudoku.css")
    start_body()
    show_title()
    show_input(sudoku)
    add_separator()
    add_pagebreak()
    parse_output(out)
    end_body()
    end_html()

def generate_plain(sudoku, out):
    parse_output(out, False)

def run(sudoku, html = True):
    # Create tenporary files.
    param = tempfile.NamedTemporaryFile()
    output = tempfile.NamedTemporaryFile()
    staging = tempfile.NamedTemporaryFile()

    # Redirect stdout to the staging file.
    saved = sys.stdout
    sys.stdout = staging

    # Put the user input into a temp file.
    param.write("Grid 00\n");
    param.write(sudoku + "\n");
    param.flush()
    
    # Invoke the sudoku game.
    os.system("game.py " + param.name + " 00 > " + output.name)
    param.close()
    
    if html:
        generate_html(sudoku, output.name)
    else:
        generate_plain(sudoku, output.name)
    output.close()

    # Reset stdout back to what it was.
    sys.stdout = saved

    # Pretty print the output.
    staging.seek(0)
    data = staging.read()[:-1]
    if html:
        soup = bs(data)
        print soup.prettify()
    else:
        print data

def main():
    html = None
    if len(sys.argv) == 2:
        sudoku = sys.argv[1]
        html = True
    elif len(sys.argv) == 3:
        sudoku = sys.argv[2]
        if sys.argv[1] == "-h":
            html = True
        elif sys.argv[1] == "-p":
            html = False

    if html is None:
        print sys.argv[0] + ": [-h|-p] <sudoku>"
        sys.exit(-1);

    run(sudoku, html)

# Take it away!
main()

