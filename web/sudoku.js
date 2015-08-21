// Constants.
var Decorator = {
                                      // CSS selectors
    action: "action",                 // action based highlight
    reason: "reason",                 // reason based highlight
    reason_2: "reason_2",             // alternative reason based highlight
                                      // Canvas style
    boundWidth: 2,                    // bounding box line width
    boundColor: "#ffff00",            // bounding box line color
    boundColor_2: "#448800",          // alternative bounding box line color
    strokeSolid: "solid",             // connection line solid style
    strokeDouble: "double",           // connection line double style
    solidLineColor: "#228822",        // connection line color
    solidLineColor_2: "#882222",      // alternative connection line color
    solidLineWidth: 3,                // solid line width
    lineCurve: -20,                   // line curvature
    lineCurve_2: 20,                  // alternative line curvature
    lineGradient: 100,                // line gradient
    doubleLineOutsideWidth: 5,        // double line width
    doubleLineInsideWidth: 3,         // double line hollow width
    doubleLineInsideColor: "#ffffff"  // double line hollow color
};

// LineStyle constructor (for canvas graphics).
function LineStyle(stroke, curve, color, gradient) {
    if (!stroke) {
        stroke = Decorator.strokeSolid;
    }

    if (!color) {
        color = Decorator.solidLineColor;
    }

    if (!curve) {
        curve = Decorator.lineCurve;
    }

    this.stroke = stroke;
    this.curve = curve;
    this.color = color;
    this.gradient = gradient;
}

LineStyle.prototype.getStrokeStyle = function(ctx, loc1, loc2) {
    if (!this.gradient) {
        return this.color;
    }

    // Linear gradient from start to end of line.
    var grad= ctx.createLinearGradient(loc1.x, loc1.y, loc2.x, loc2.y);
    grad.addColorStop(0, this.shadeColor(this.color, this.gradient));
    grad.addColorStop(1, this.color);

    return grad;
}

LineStyle.prototype.shadeColor = function(color, percent) {
    var r = parseInt(color.substring(1, 3), 16);
    var g = parseInt(color.substring(3, 5), 16);
    var b = parseInt(color.substring(5, 7), 16);

    r = parseInt(r * (100 + percent) / 100);
    g = parseInt(g * (100 + percent) / 100);
    b = parseInt(b * (100 + percent) / 100);

    r = Math.min(r, 255);
    g = Math.min(g, 255);
    b = Math.min(b, 255);

    var rr = r.toString(16);
    var gg = g.toString(16);
    var bb = b.toString(16);

    rr = rr.length == 1 ? "0" + rr : rr;
    gg = gg.length == 1 ? "0" + gg : gg;
    bb = bb.length == 1 ? "0" + bb : bb;

    return "#" + rr + gg + bb;
}

// Sudoku Node constructor
function Node(index, value) {
    this.index = index;

    if (!value) {
        this.value = 0;
    } else {
        this.value = value;
    }
}

// Sudoku Board constructor
function Board(sudoku, div) {
    this.sudoku = sudoku;
    this.div = div;
    this.nodes = [];
    this.board = null;
    this.bounds = null;
}

Board.prototype.getElement = function() {
    var elem = document.getElementById(this.div);
    if (!elem) {
        elem = document.createElement('div');
	elem.id = div;
	elem.setAttribute('class', 'frame table');
        document.body.appendChild(elem);
    }
    return elem;
}

Board.prototype.display = function() {
    this.loadGame();
    this.initializeUI();
    this.createBoard();
}

Board.prototype.initializeUI = function() {
    var container = document.getElementById(this.div);
    if (!container) {
        container = document.createElement('div');
        container.setAttribute('class', 'sudoku');
        container.id = this.div;
        document.body.appendChild(container);
    }

    var table = document.createElement('div');
    table.setAttribute('class', 'frame table');
    table.id = this.div + '-table';
    container.appendChild(table);

    var canvas = document.createElement('canvas');
    canvas.setAttribute('class', 'frame canvas');
    canvas.id = this.div + '-canvas';
    canvas.width = container.offsetWidth;
    canvas.height = container.offsetHeight;
    container.appendChild(canvas);

    // Get the offsets of the canvas
    this.bounds = canvas.getBoundingClientRect()
}

Board.prototype.createBoard = function() {
    // Create outer table for the sudoku board.
    this.board = document.createElement('table');
    this.board.setAttribute('class', 'board');

    // Create inner table for each sudoku box.
    var x, y;
    for (x = 0; x < 3; x++) {
        var row = this.board.insertRow(x);
        for (y = 0; y < 3; y++) {
            var cell = row.insertCell(y);
            cell.setAttribute('class', 'outer');
            var box = this.createBox(x, y);
            cell.appendChild(box);
        }
    }

    // Append Table into div.
    var elem = document.getElementById(this.div + '-table');
    elem.appendChild(this.board);
};

Board.prototype.createBox = function(bx, by) {
    var box = document.createElement('table');
    box.setAttribute('class', 'box');

    // Create table for each sudoku cell.
    var x, y;
    for (x = 0; x < 3; x++) {
        var row = box.insertRow(x);
        for (y = 0; y < 3; y++) {
            var cell = row.insertCell(y);
	    cell.setAttribute('class', 'inner');
	    this.createNode(cell, bx * 3 + x, by * 3 + y);
        }
    }

    return box;
}

Board.prototype.createNode = function(cell, x, y) {
    var node = this.nodes[x * 9 + y];

    if (node.value) {
        cell.innerHTML = node.value.toString();
    } else if (node.hints) {
        var hints = this.addHints(node.hints);
        cell.appendChild(hints);
    }
}

Board.prototype.addHints = function(hints) {
    var node = document.createElement('table');
    node.setAttribute('class', 'hints');

    var x, y;
    for (x = 0; x < 3; x++) {
        // Insert New Row for table at index 'x'.
        var row = node.insertRow(x);
        for (y = 0; y < 3; y++) {
            // Insert New Column for Row 'x' at index 'y'.
            var cell = row.insertCell(y);
	    cell.setAttribute('class', 'hint');
            var hint = x * 3 + y + 1
            if (hints.indexOf(hint) != -1) {
                cell.innerHTML = hint.toString();
            }
        }
    }

    return node;
}

Board.prototype.loadGame = function() {
    var vpatt = /\d|\[[1-9](\s*,\s*[1-9]){1,8}\]/g;
    var hpatt = /\d/g;
    var match, value, node, hint;
    var index = 0, hints = [];
    
    while (match = vpatt.exec(this.sudoku)) {
        value = match[0];

        if (!value.startsWith('[')) {
            node = new Node(index, parseInt(value));
        } else {
            node = new Node(index);
            while (match = hpatt.exec(value)) {
                hint = match[0];
                hints.push(parseInt(hint));
            }
            node.hints = hints.slice();
            hints = []
        }

        index++;
        this.nodes.push(node);
    }
}

Board.prototype.getNodeCell = function(node) {
    var bx = Math.trunc(node.x / 3), by = Math.trunc(node.y / 3);
    var nx = node.x % 3, ny = node.y % 3;
    var box = this.board.rows[bx].cells[by];
    return box.firstChild.rows[nx].cells[ny];
}

Board.prototype.getHintCell = function(node, hint) {
    var cell = this.getNodeCell(node);
    var x = Math.trunc((hint - 1) / 3), y = (hint - 1) % 3;
    return cell.firstChild.rows[x].cells[y];
}

Board.prototype.hasHints = function(node) {
    var cell = this.getNodeCell(node);
    if (cell.firstChild == null) {
        return false;
    }
    return cell.firstChild.nodeName.toLowerCase() === "table";
}

Board.prototype.decorate = function(elem, addent, base) {
    if (!base) {
        base = elem.getAttribute('class');
    }
    elem.setAttribute('class', base + ' ' + addent);
}

Board.prototype.getStyleClass = function(base, type) {
    return base + '_' + type;
}

Board.prototype.highlightNodeBorder = function(node, type) {
    var cell = this.getNodeCell(node);
    var cls = this.getStyleClass('node_border_high', type);
    this.decorate(cell, cls, 'inner');
}

Board.prototype.highlightNodeFill = function(node, type) {
    var cell = this.getNodeCell(node);
    var cls = this.getStyleClass('node_fill_high', type);
    this.decorate(cell, cls, 'inner');
}

Board.prototype.highlightHintBorder = function(node, hints, type) {
    if (!this.hasHints(node)) {
        return;
    }
    var hint;
    var h;
    var cls = this.getStyleClass('hint_border_high', type);
    for (h = 0; h < hints.length; h++) {
        cell = this.getHintCell(node, hints[h]);
        if (cell.innerHTML.length > 0) {
            // Make the style change addititve.
            this.decorate(cell, cls);
        }
    }
}

Board.prototype.highlightHintFill = function(node, hints, type) {
    if (!this.hasHints(node)) {
        return;
    }
    var hint;
    var h;
    var cls = this.getStyleClass('hint_fill_high', type);
    for (h = 0; h < hints.length; h++) {
        cell = this.getHintCell(node, hints[h]);
        if (cell.innerHTML.length > 0) {
            // Make the style change addititve.
            this.decorate(cell, cls);
        }
    }
}

Board.prototype.locateElement = function(elem) {
    var rect = elem.getBoundingClientRect();
    x = rect.left - this.bounds.left;
    y = rect.top - this.bounds.top;
    w = rect.right - rect.left;
    h = rect.bottom - rect.top;

    return {x: x + w / 2, y: y + h / 2};
}

Board.prototype.findMinRect = function(nodes) {
    var i, cell, r, b;
    for (i = 0; i < nodes.length; i++) {
        cell = this.getNodeCell(nodes[i]);
        if (!b) {
            r = cell.getBoundingClientRect();
            // Make a copy of r since it seems to be immutable.
            b = {left: r.left, top: r.top, right: r.right, bottom: r.bottom}
            continue;
        }
        r = cell.getBoundingClientRect()
        b.left = Math.min(r.left, b.left);
        b.top = Math.min(r.top, b.top);
	b.right = Math.max(r.right, b.right);
        b.bottom = Math.max(r.bottom, b.bottom);
    }

    // Adjust the bounding rect found to be relative to the canvas.
    b.left -= this.bounds.left;
    b.top -= this.bounds.top;
    b.right -= this.bounds.left;
    b.bottom -= this.bounds.top;

    return {x: b.left, y: b.top, width: b.right - b.left, height: b.bottom - b.top};
}

Board.prototype.groupNodes = function(nodes, style) {
    var rect = this.findMinRect(nodes);

    if (!style) {
        style = new LineStyle();
    }

    // Set up the canvas.
    var canvas = document.getElementById(this.div + '-canvas');
    var ctx = canvas.getContext('2d');

    ctx.strokeStyle = style.color;
    ctx.lineWidth = Decorator.boundWidth;
    ctx.rect(rect.x, rect.y, rect.width, rect.height);

    ctx.stroke();
}

Board.prototype.groupRow = function(node, style) {
    left = {x: node.x, y: 0};
    right = {x: node.x, y: 8};
    this.groupNodes([left, right], style);
}

Board.prototype.groupCol = function(node, style) {
    left = {x: 0, y: node.y};
    right = {x: 8, y: node.y};
    this.groupNodes([left, right], style);
}

Board.prototype.groupBox = function(node, style) {
    topLeft = {x: Math.trunc(node.x / 3) * 3, y: Math.trunc(node.y / 3) * 3};
    topRight = {x: topLeft.x, y: topLeft.y + 2};
    bottomLeft = {x: topLeft.x + 2, y: topLeft.y};
    bottomRight = {x: topLeft.x + 2, y: topLeft.y + 2};
    this.groupNodes([topLeft, topRight, bottomLeft, bottomRight], style);
}

Board.prototype.highlightRow = function(row, style) {
    this.groupRow({x: row, y: 0}, style)
}

Board.prototype.highlightCol = function(col, style) {
    this.groupCol({x: 0, y: col}, style)
}

Board.prototype.highlightBox = function(box, style) {
    this.groupBox({x: Math.trunc(box / 3) * 3, y: (box % 3) * 3}, style)
}

Board.prototype.connectGroups = function(group1, hint1, group2, hint2, style) {
    this.connectHints(group1[Math.trunc(group1.length / 2)], hint1,
        group2[Math.trunc(group2.length / 2)], hint2, style)
}

Board.prototype.connectHints = function(node1, hint1, node2, hint2, style) {
    var cell1, cell2;

    if (this.hasHints(node1)) {
        cell1 = this.getHintCell(node1, hint1);
    } else {
        cell1 = this.getNodeCell(node1);
    }
    if (this.hasHints(node2)) {
        cell2 = this.getHintCell(node2, hint2);
    } else {
        cell2 = this.getNodeCell(node2);
    }

    this.connectCells(cell1, cell2, style);
}

Board.prototype.connectNodes = function(node1, node2, style) {
    var cell1 = this.getNodeCell(node1);
    var cell2 = this.getNodeCell(node2);
    this.connectCells(cell1, cell2, style);
}

Board.prototype.connectCells = function(cell1, cell2, style) {
    // Locate the cells.
    var loc1 = board.locateElement(cell1);
    var loc2 = board.locateElement(cell2);

    if (!style) {
        style = new LineStyle();
    }

    // Set up the canvas.
    var canvas = document.getElementById(this.div + '-canvas');
    var ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(loc1.x, loc1.y);
    dx = loc2.x - loc1.x;
    dy = loc2.y - loc1.y;
    xy = Math.sqrt(dx * dx + dy * dy);
    cx = style.curve * dy / xy
    cy = style.curve * dx / xy;
    ctx.bezierCurveTo(loc1.x + cx, loc1.y + cy, loc2.x + cx, loc2.y + cy, loc2.x, loc2.y);

    // Stroke.
    if (style.stroke === Decorator.strokeSolid) {
        this.solidStroke(ctx, style, loc1, loc2);
    } else if (style.stroke === Decorator.strokeDouble) {
        this.doubleStroke(ctx, style, loc1, loc2);
    }
}

Board.prototype.solidStroke = function(ctx, style, loc1, loc2) {
    ctx.strokeStyle = style.getStrokeStyle(ctx, loc1, loc2);
    ctx.lineWidth = Decorator.solidLineWidth;
    ctx.stroke();
}

Board.prototype.doubleStroke = function(ctx, style, loc1, loc2) {
    ctx.strokeStyle = style.getStrokeStyle(ctx, loc1, loc2);
    ctx.lineWidth = Decorator.doubleLineOutsideWidth;
    ctx.stroke();
    ctx.strokeStyle = Decorator.doubleLineInsideColor;
    ctx.lineWidth = Decorator.doubleLineInsideWidth;
    ctx.stroke();
}
