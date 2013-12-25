//----------------------------------------------------------------------------
// A utility class to help draw texture map based text into an XNA scene.
//
// This class reads and uses the font data format produced by the BMFontGen
// tool. See http://blogs.msdn.com/garykac/articles/732007.aspx
// 
//----------------------------------------------------------------------------

#light

module Font

// Reference dlls, you will need to change this if you have a different version
// of XNA Game Framework installed

#if XBOX360
#I @"C:\Program Files\Microsoft XNA\XNA Game Studio Express\v1.0\References\Xbox360"
#else
#I @"C:\Program Files\Microsoft XNA\XNA Game Studio Express\v1.0\References\Windows\x86"
#endif

#r "Microsoft.Xna.Framework.dll"
#r "Microsoft.Xna.Framework.Game.dll"

open Collections
open Compatibility 
open Idioms
open Microsoft.Xna.Framework
open Microsoft.Xna.Framework.Audio
open Microsoft.Xna.Framework.Content
open Microsoft.Xna.Framework.Graphics
open Microsoft.Xna.Framework.Input
open Microsoft.Xna.Framework.Storage
open System
open System.IO
open System.Text
open System.Xml


// Types that describe a bitmap font

type GlyphInfo =
    {
        bitmapID : int
        originX : int
        originY : int
        width : int
        height : int
        advanceWidth : int
        leftSideBearing : int
    }

type BitmapInfo =
    {
        filename : string
        x : int
        y : int
    }

type BitmapFont =
    {
        bitmaps : Map<int, BitmapInfo>
        textures : Map<int, Texture2D>
        glyphs : Map<char, GlyphInfo>
        base : int
        ascent : int
    }
 
//----------------------------------------------------------
// Utility functions to parse XML files

let Select (|P|_|) (x: #XmlNode) = [ for P y as n in x.ChildNodes -> y ]

let Select2 (|A|B|) (x: #XmlNode) = [ for (A y | B y) as n in x.ChildNodes -> y ]

let (|Elem|_|) name (inp: #XmlNode) = 
    if inp.Name = name then Some(inp) 
    else None

let (|Attr|_|) attr (inp: #XmlNode) = 
    match inp.Attributes.GetNamedItem(attr) with
    | null -> None
    | node -> Some(node.Value)

let (|Num|_|) attr inp = 
    match inp with 
    | Attr attr v -> Some (Int32.of_string v) 
    | _           -> None

let (|NumHex|_|) attr inp = 
    match inp with 
    | Attr attr v -> Some (Int32.Parse(v, Globalization.NumberStyles.HexNumber)) 
    | _           -> None

let (|Char|_|) attr inp = 
    match inp with 
    | Attr attr v -> Some (v.[0]) 
    | _           -> None

let parsePair (splitchars : string) (str : string) =
    let items = str.Split(splitchars.ToCharArray())
    (Int32.of_string items.(0)), (Int32.of_string items.(1))
    
let (|NumPair|_|) attr inp = 
    match inp with 
    | Attr attr v -> Some (parsePair "," v) 
    | _           -> None

let (|NumPairX|_|) attr inp = 
    match inp with 
    | Attr attr v -> Some (parsePair "x" v) 
    | _           -> None

// Specialized functions to parse font files:

let rec (|GlyphElem|_|) inp = 
    match inp with 
    | Elem "glyph" (Num "ch" ch & NumHex "code" code & Num "bm" bm & NumPair "origin" origin & NumPairX "size" size & Num "aw" aw & Num "lsb" lsb ) ->
        Some {bitmapID = bm; originX = (fst origin); originY = (snd origin); width = (fst size); height = (snd size); advanceWidth = aw; leftSideBearing = lsb} 
    | _ -> None

and (|GlyphElems|) inp = Select (|GlyphElem|_|) inp 

let rec (|BitmapElem|_|) inp = 
    match inp with 
    | Elem "bitmap" (Num "id" id & Attr "name" name & NumPairX "size" size ) ->
        Some (id , {filename = name; x = (fst size); y = (snd size)})
    | _ -> None

and (|BitmapElems|) inp = Select (|BitmapElem|_|) inp 

let parse inp = 
    match (inp :> XmlNode) with 
    | Elem "font" (Num "base" b & Num "height" h & (Elem "bitmaps" (BitmapElems bitmaps)) & (Elem "gliphs" (GlyphElems glyphs))) ->
        b, h, bitmaps, glyphs
    | _ -> failwith "not a font file"

let parseBitmapFontFile(fileName : string) =
    let xd = new XmlDocument()
    xd.Load(fileName)
    parse xd.DocumentElement

let testBitmapFont () =
    printf "results=%A\n" (parseBitmapFontFile @"C:\Users\Jack\Desktop\BMFontGen\BMFontGen\comic.xml")
    