// The width and height of a tile in pixels (in the strike image)
var tileWidth = 16;
var tileHeight = 16;

var strike = new Image();
strike.src = "data:image/png;base64,"+
"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"+
"lFTkSuQmCC";