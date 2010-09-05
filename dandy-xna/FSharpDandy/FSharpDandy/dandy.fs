//----------------------------------------------------------------------------
// Dandy Dungeon, a 2D 4-player action-adventure game in FSharp
// (Originally written in 6502 assembly language for the Atari 800 in 1983.)
//----------------------------------------------------------------------------

#light

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

// Configuration:

// Directory to look for game media files. This is relative to the game executable path.

let gameMediaPath = @"\Media\"

let tileSizeX = 32.0
let tileSizeY = 32.0
let scoreBoxSizeX = 640.0 / 4.0
let scoreBoxSizeY = 480.0 - (tileSizeY * 10.0)
let mapBaseY = scoreBoxSizeY

//---------------------------------------------------------------
// The game model

type piece = 
    Space |
    Wall |
    Lock |
    Up |
    Down |
    Key |
    Food |
    Money |
    Bomb |
    Ghost of int |
    Heart |
    Generator of int |
    Arrow of int |
    Player of int

let piece_of_int i =
    match i with
          0 -> Space
        | 1 -> Wall
        | 2 -> Lock
        | 3 -> Up
        | 4 -> Down
        | 5 -> Key
        | 6 -> Food
        | 7 -> Money
        | 8 -> Bomb
        | 9 | 10 | 11 -> Ghost (i - 9)
        | 12 -> Heart
        | 13 | 14 | 15 -> Generator (i - 13)
        | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 -> Arrow (i - 16)
        | 24 | 25 | 26 | 27 -> Player (i-24)
        | _ -> Space

let int_of_piece p =
    match p with
        | Space         -> 0
        | Wall          -> 1
        | Lock          -> 2
        | Up            -> 3 
        | Down          -> 4 
        | Key           -> 5 
        | Food          -> 6 
        | Money         -> 7 
        | Bomb          -> 8 
        | Heart         -> 12 
        | Ghost i       -> 9 + i
        | Generator i   -> 13 + i
        | Arrow i       -> 16 + i
        | Player i      -> 24 + i

let float_of_piece p = float (int_of_piece p)

let mapChars = " *LUDKF$BabcHABC<<<<<<<<1234"

type point = { x: int; y: int }
    with
        static member make(x, y) = {x = x; y = y}
        static member (+) (a, b) = {x = a.x + b.x; y = a.y + b.y}
        static member (-) (a, b) = {x = a.x - b.x; y = a.y - b.y}
    end

let offsets = [|
    point.make(0,-1); point.make(1,-1); point.make(1,0);
    point.make(1,1); point.make(0,1); point.make(-1,1);
    point.make(-1,0); point.make(-1,-1)
|]

let offset dir = offsets.(dir)

let moveDir (p : point) dir = p + offset dir

let kDirNone = 8

let kPadToDir =
    [|
        // Bitfield is Right Left Down Up
        // Directions are clockwise from up == 0 . 8 == undefined
        8; // 0000
        0; // 0001 
        4; // 0010
        8; // 0011 
        6; // 0100
        7; // 0101
        5; // 0110
        6; // 0111
        2; // 1000
        1; // 1001
        3; // 1010
        2; // 1011
        8; // 1100
        0; // 1101 
        4; // 1110 
        8  // 1111 
    |]

let kTestDirDelta = [| 1; -1; 0|]

let adjustHeading dir delta = (dir + delta) &&& 7

let random = new Random()
let getRandom range = random.Next(range)

type map =
  class
    val width: int
    val height: int
    val arr: piece [,]
    new(x, y) = {width = x; height = y; arr = Array2.create x y Space}
    member m.get(x, y) =  m.arr.[x,y]
    member m.get(p) =  m.arr.[p.x,p.y]
    member m.set(x, y, v) = m.arr.[x,y] <- v
    member m.set(p, v) = m.arr.[p.x,p.y] <- v
    /// Search for the first piece that matches the function f.
    // returns the tuple (found (x, y))
    member m.find(f: piece -> bool) = 
      let w = m.width
      let h = m.height
      let mutable res = false
      let mutable y = 0
      let mutable x = 0
      while not res && y < h do
        while not res && x < w do
          if f (m.get(x, y)) then res <- true
          if not res then x <- x + 1
        done
        if not res then
            x <- 0
            y <- y + 1
      done
      (res, point.make(x,y))
    member m.fold(f, acc) =
      let mutable acc2 = acc
      for y = 0 to m.height-1 do
        for x = 0 to m.width-1 do
          acc2 <- f x y (m.get(x,y)) acc2
        done
      done
      acc2
    member m.iter(f) =
      for y = 0 to m.height-1 do
        for x = 0 to m.width-1 do
          f x y (m.get(x,y))
        done
      done
    override m.ToString() =
      let w = m.width
      let h = m.height
      let sb = new System.Text.StringBuilder((w+1)*h)
      let oc (c : char) = ignore(sb.Append(c))
      let w2 = w - 1
      let f x y p =
        oc(mapChars.Chars(int_of_piece p))
        if x = w2 then oc '\n'
      m.iter f
      sb.ToString()
    member m.getActive (cog : float * float) =
      let getActiveAxis x width viewWidth =
        let fwidth, fviewWidth = (float width), (float viewWidth)
        let x2 = Math.Min(fwidth - fviewWidth, Math.Max(0.0, x - fviewWidth / 2.0))
        // let left = truncate x2 // Doesn't work on Xbox 360 in F# 1.9.1.1, System.Math.Truncate(double) not supported
        let left = Int32.of_float x2
        let right = Math.Min(left + viewWidth + 1, width)
        x2, left, right
      let cogx, cogy = cog in
      let x2, left, right = getActiveAxis cogx m.width 20 in
      let y2, top, bottom = getActiveAxis cogy m.height 10 in
      x2, y2, left, top, right, bottom
  end

type arrow =
  class
    val mutable pos : point
    val mutable dir : int
    new(pos, dir) = {pos = pos; dir = dir}
    static member CanGo p = p = Space
  end

type playerState = Inactive | Playing | InWarp | Dead

type player =
  class
    val mutable pos : point
    val mutable dir : int
    val mutable health : int
    val mutable score : int
    val mutable arrow : arrow option
    val mutable state : playerState
    val mutable keys : int
    val mutable bombs : int
    val index : int
    new(x,y,d, index) = {pos = point.make(x, y); dir = d; health = 0; score = 0; arrow = None;
      state = Inactive; keys = 0; bombs = 0; index = index}
    member p.IsAlive() = match p.state with Playing | InWarp -> true | _ -> false
    member p.IsVisible() = p.state = Playing
  end

type GameKeys = class
    static member Up = 1
    static member Down = 2
    static member Left = 4
    static member Right = 8
    static member A = 16
    static member B = 32
    static member C = 64 // "X" on Xbox 360 controller
    static member D = 128 // "Y" on Xbox 360 controller
    static member Start = 256
    static member Back = 512
end

type gamepad =
  class
    val mutable buttons : int
    val mutable strobes : int (* down at least once since last time strobes were cleared *)
    new() = { buttons = 0;  strobes = 0}
    member g.set down mask =
      if down then
        g.buttons <- g.buttons ||| mask
        g.strobes <- g.strobes ||| mask
      else
        g.buttons <- g.buttons &&&  ~~~ mask
  end;;

let numPlayers = 4

type input =
    class
        val mutable escStrobe : bool
        val pads : gamepad []
        val map : (Keys * int * int) list
        new() =
            {
                pads = Array.init numPlayers (fun _ -> new gamepad());
                map = [
      
                    // Player 1 - wasd
                    
                        (Keys.A, 0, GameKeys.Left);
                        (Keys.S, 0, GameKeys.Down);
                        (Keys.D, 0, GameKeys.Right);
                        (Keys.W, 0, GameKeys.Up);
                        (Keys.Q, 0, GameKeys.A);
                        (Keys.E, 0, GameKeys.B);

                        // (Keys.F11, 0, GameKeys.C);
                        (Keys.F12, 0, GameKeys.D); // For development go down to next level

                        // Player 2 - IJKL

                        (Keys.J, 1, GameKeys.Left);
                        (Keys.K, 1, GameKeys.Down);
                        (Keys.L, 1, GameKeys.Right);
                        (Keys.I, 1, GameKeys.Up);
                        (Keys.U, 1, GameKeys.A);
                        (Keys.O, 1, GameKeys.B);

                        // Player 3 - ins/del pad
                        
                        (Keys.Delete, 2, GameKeys.Left);
                        (Keys.End, 2, GameKeys.Down);
                        (Keys.PageDown, 2, GameKeys.Right);
                        (Keys.Home, 2, GameKeys.Up);
                        (Keys.Insert, 2, GameKeys.A);
                        (Keys.PageUp, 2, GameKeys.B);
                        
                        // Player 4 - number pad

                        (Keys.NumPad4, 3, GameKeys.Left);
                        (Keys.NumPad5, 3, GameKeys.Down);
                        (Keys.NumPad2, 3, GameKeys.Down); // Alternate down, since it has a down arrow
                        (Keys.NumPad6, 3, GameKeys.Right);
                        (Keys.NumPad8, 3, GameKeys.Up);
                        (Keys.NumPad7, 3, GameKeys.A);
                        (Keys.NumPad9, 3, GameKeys.B);
                    ];
            escStrobe = false
        }
        member this.HandleEvent(down, (key : Keys)) =
            match List.tryfind (fun (a, b, c) -> a = key) this.map with
            | Some (a, b, c) ->
                if b < numPlayers then this.pads.(b).set down c
            | _ ->
                if down then
                    if key = Keys.Escape then this.escStrobe <- true
                    
        member this.ClearStrobes() =
          for i = 0 to numPlayers - 1 do
            this.pads.(i).strobes <- 0
          done
          this.escStrobe <- false
        
        member this.UpdatePadState(pad, key, down) =
            this.pads.(pad).set down key

    end

/// Used to convert integer to "PlayerIndex" enum

let g_players = [|PlayerIndex.One;PlayerIndex.Two;PlayerIndex.Three;PlayerIndex.Four|]

/// Implement very simple vibration effect

type tapperEffect = int * float32 * float32

let g_nullEffect = (0, 0.0f, 0.0f)

type tapper =
    class
        val fx : tapperEffect []
        new(numPlayers) =
            {
                fx = Array.create numPlayers g_nullEffect
            }
        member this.Tap(player , duration, lowFreq, highFreq) =
            this.fx.[player] <- (duration, lowFreq, highFreq)
            
        member this.Update() =
            let fx = this.fx
            for i = 0 to fx.Length-1 do
                let c, low, high = fx.[i]
                ignore (GamePad.SetVibration(g_players.[i], low, high))
                if c > 1 then
                    fx.[i] <- (c - 1, low, high)
                elif c = 1 then
                    fx.[i] <- g_nullEffect
            done
        end

// Compute remainder and modulus - a very common operation for 2D games

let remmod v stride =
    let y = v / stride
    let x = v - y * stride
    (x, y)
  
let kDirTable =
    [|
             // YyXx
        255; // 0000
        6;   // 0001
        2;   // 0010
        255; // 0011
        0;   // 0100
        7;   // 0101
        1;   // 0110
        255; // 0111
        4;   // 1000
        5;   // 1001
        3;   // 1010
        255; // 1011
        255; // 1100
        255; // 1101
        255; // 1110
        255  // 1111
    |]

type game = class
    val m : map
    val p : player[]
    val mutable level : int
    val input : input
    val mutable gridStep : int
    val mutable soundBank : SoundBank
    val tapper : tapper
    new () =
        {
            m = new map(60,30)
            p = Array.zero_create numPlayers
            level = 0
            input = new input()
            gridStep = 0
            soundBank = null
            tapper = new tapper(numPlayers)
        }
            
    member g.init() =
        for i = 0 to numPlayers-1 do
            g.p.(i) <- new player(0, 0, 0, i)
            g.p.(i).health <- 10
        done
        g.load(0)
        g.gridStep <- 0
    
    member g.PlayCue(s) =
        g.soundBank.PlayCue(s)
    
    member g.levelName(level) =
        let levelChar = Char.chr (97 + level)
        let sb = new System.Text.StringBuilder(300)
        sb.Append(StorageContainer.TitleLocation).Append(gameMediaPath).Append(@"levels\level.").Append(levelChar).ToString()
    
    member g.placePlayer(i, pos, dir) =
        let p = g.p.(i)
        p.pos <- pos
        p.dir <- dir
        if p.IsVisible() then g.m.set(p.pos, Player p.index)
    
    member g.showPlayer(p) =
        g.setPlayerState(p, Playing)
    
    member g.setPlayerState((p : player), state) =
        p.state <- state
        let newCell =
            match state with
            | Playing -> Player p.index
            | Dead ->
                if p.keys > 0 then
                    p.keys <- p.keys - 1
                    Key
                else
                    Space
            | _ -> Space
        g.m.set(p.pos, newCell)
    
    member g.load(level) =
        g.level <- level
        let m = g.m
        let levelName = g.levelName level
        let fs = File.OpenRead(levelName)
        for y = 0 to m.height-1 do
            for x = 0 to ((m.width-1) / 2) do
                let x2 = x * 2
                let c = fs.ReadByte()
                m.set(x2, y, piece_of_int (c &&& 0xf))
                m.set(x2 + 1, y, piece_of_int (c >>> 4))
            done
        done
        let _, pt = m.find((=) Up)
        for i = 0 to numPlayers-1 do
            let dir = 2 * i
            g.placePlayer(i, pt + offset dir, dir)
        done
    member g.cog() =
        let cog, n =
            Array.fold_left
                (fun (cog, n) (p : player) -> if p.IsVisible() then (cog + p.pos, n + 1) else (cog, n))
                (point.make(0,0), 0) g.p in
            let div = (float (if n = 0 then 1 else n))
            ((float cog.x) / div, (float cog.y) / div)
    member g.HandleEvent(down, (key : Keys)) =
        g.input.HandleEvent(down, key)
        
    member g.Step() =
        g.MoveArrows()
        g.MoveMonsters()
        g.MovePlayers()
        if not (g.PartyAlive()) then
            g.init()
        elif g.PartyInWarp() then
            g.ChangeLevel()
            for i = 0 to numPlayers - 1 do
                let p = g.p.(i)
                if p.state = InWarp then g.showPlayer(p)
            done
        g.input.ClearStrobes()
        g.tapper.Update()
    
    member g.MoveArrows() =
        for i = 0 to numPlayers - 1 do
            let p = g.p.(i)
            match p.arrow with
            | Some arrow -> g.DoArrowMove p false
            | _ -> ()
        done
    
    member g.MoveMonsters() =
       let m = g.m
       let cogx, cogy, l,t,r,b = m.getActive(g.cog())
       let gridSize = 3
       let gx, gy = remmod g.gridStep 3
       let mutable y = t + gy
       while y < b do
         let mutable x = l + gx
         while x < r do
           g.MoveMonster x y
           x <- x + gridSize
         done
         y <- y + gridSize
       done
       g.gridStep <- g.gridStep + 1
       if g.gridStep >= gridSize * gridSize then g.gridStep <- 0
    
    member g.MoveMonster x y =
       let m = g.m
       match m.get(x,y) with
           | Ghost gtype ->
             g.MoveGhost x y gtype
           | Generator gtype ->
             if (getRandom 10) < 3 then
               let gpos = point.make(x, y)
               let mpos = moveDir gpos ((getRandom 4) * 2)
               if m.get(mpos) = Space then
                 m.set(mpos, Ghost gtype)
           | _ -> ()
    
    member g.MoveGhost x y gtype =
       let dir = g.GetDirectionOfNearestPlayer x y
       if dir <> kDirNone then
         let m = g.m in
         let mpos = point.make(x,y) in
         let mutable mpos' = None in
         let mutable freeze = false in
         for test = 0 to 2 do
           let mpos'' = moveDir mpos (adjustHeading dir kTestDirDelta.(test)) in
           if 
             match m.get(mpos'') with
             | Space -> true
             | Player _ -> true
             | Arrow _ -> freeze <- true; false
             | _ -> false
           then
             mpos' <- Some mpos''
         done;
         if not freeze then (
             match mpos' with
             | Some mpos'' ->
               m.set(x, y, Space);
               ( match m.get(mpos'') with
               | Player i ->
                 let p = g.p.(i) in
                 let monsterHit = gtype + 1 in
                 if p.health > monsterHit then
                   p.health <- p.health - monsterHit
                   g.PlayCue("ouch")
                   g.tapper.Tap(i, 1 + gtype, 0.0f, 1.0f )
                 else (
                   p.health <- 0;
                   p.pos <- mpos'';
                   g.setPlayerState(p, Dead)
                 )
               | _ -> m.set(mpos'', Ghost gtype)
               )
             | _ -> ()
           )
           
    member g.GetDirectionOfNearestPlayer x y =
       let bestPos,bestDistance = 
         g.p |> Array.fold_left (fun ((bestPos,bestDistance) as acc) p -> 
           if p.IsVisible() then
             let distance = Math.Abs(p.pos.x - x) + Math.Abs(p.pos.y - y) in
             if distance < bestDistance then (p.pos, distance) else acc
           else acc)
           (point.make(0,0), 10000) in
       if bestDistance = 10000 then
         kDirNone
       else
         let dx, dy = bestPos.x - x, bestPos.y - y in
         let test v neg pos = if v > 0 then pos else (if v < 0 then neg else 0) in
         let dirBits = (test dy 4 8) ||| (test dx 1 2) in
         kDirTable.(dirBits)
         
    member g.MovePlayers() =
        if g.input.escStrobe then
            (); // Application.Exit()
        for i = 0 to numPlayers - 1 do
            let p = g.p.(i) in
            let pad = g.input.pads.(i) in
            let buttons = pad.buttons in
            let strobes = pad.strobes in
            let check data mask = data &&& mask <> 0 in
            match p.state with
            | Inactive ->
                if check strobes GameKeys.A then g.showPlayer(p)
            | Playing ->
                let dir = kPadToDir.(15 &&& buttons)
                let firing = check buttons GameKeys.A
                if dir <> kDirNone then g.Move i dir firing
                if firing then g.Fire i
                if check strobes GameKeys.B then g.UseSmartBomb i
                if check strobes GameKeys.D then g.ChangeLevel()
            | _ -> ()
        done
        
    member g.Move i dir firing =
        let p = g.p.(i)
        if p.IsVisible() then
            p.dir <- dir;
            let pos' = moveDir p.pos dir
            let doMove =
                if firing then
                    false  // Don't actually move if we're firing
                else
                    match g.m.get(pos') with
                    | Space ->
                        true
                    | Lock ->
                        if p.keys > 0 then
                            p.keys <- p.keys - 1
                            g.PlayCue("doorOpen")
                            g.OpenLock pos'
                            true
                        else
                            g.PlayCue("needkey")
                            false
                    | Key ->
                        p.keys <- p.keys + 1
                        g.PlayCue("key")
                        true
                    | Food ->
                        p.health <- p.health + 10
                        g.PlayCue("yum")
                        true
                    | Money ->
                        p.score <- p.score + 10
                        g.PlayCue("kaching")
                        true
                    | Bomb ->
                        p.bombs <- p.bombs + 1
                        g.PlayCue("bomb")
                        true
                    | Down ->
                        g.PlayCue("goingDown")
                        g.setPlayerState(p, InWarp)
                        false
                    | Player i2 ->
                        // See if we can push the other player
                        let p2 = g.p.(i2)
                        let pos2' = moveDir p2.pos dir
                        let moveEm = g.m.get(pos2') = Space
                        if moveEm then
                            g.MoveImpl(i2, pos2')
                            g.tapper.Tap(i2, 1, 0.0f, 0.2f)
                        moveEm
                    | _ -> false
            if doMove then
                g.MoveImpl(i, pos')
                
    member g.MoveImpl(i, pos') =
        let p = g.p.(i)
        g.m.set(p.pos, Space)
        g.m.set(pos', Player i)
        p.pos <- pos'
        
    member g.OpenLock pos =
        (* Flood fill *)
        let m = g.m
        let x,y = pos.x, pos.y
        let rec flood x y =
            if m.get(x, y) = Lock then
                m.set(x, y, Space)
                for dx = -1 to 1 do
                    for dy = -1 to 1 do
                        flood (x + dx) (y + dy)
                    done
                done
        flood x y
    member g.PartyAlive () =
        Array.exists (fun (p : player) -> p.IsAlive()) g.p 
    member g.PartyInWarp () =
        Array.for_all (fun (p : player) -> p.state <> Playing) g.p &&
        Array.exists (fun (p : player) -> p.state = InWarp) g.p
    member g.Fire i =
        let p = g.p.(i)
        if Option.is_none p.arrow then
            p.arrow <- Some (new arrow(p.pos, p.dir))
            g.PlayCue("bang")
            g.DoArrowMove p true
    member g.DoArrowMove (p : player) isFirstMove =
       match p.arrow with
       | Some arrow ->
         let pos = arrow.pos in
         let m = g.m in
         let dir = arrow.dir in
         if not isFirstMove then
           m.set(pos, Space);
         let pos' = moveDir pos dir in
         let die () = p.arrow <- None in
         let draw piece = m.set(pos', piece); die() in
         let erase () = draw Space in
         let arrowDir = (dir + 3) &&& 7 in (* Arrow graphics don't match direction numbering *)
         match g.m.get(pos') with
          | Space -> arrow.pos <- pos' ; m.set(pos', Arrow arrowDir)
          | Bomb -> g.DoSmartBomb(); erase()
          | Ghost size ->
            g.PlayCue("monsterpain")
            if size > 0 then draw (Ghost (size - 1)) else erase()
          | Heart ->
            g.PlayCue("heart")
            g.DoHeart pos'
            die()
          | Generator size ->
            g.PlayCue("monsterpain")
            if size > 0 then draw (Generator (size - 1)) else erase()
          | _ -> die()
       | _ -> ()
    member g.DoHeart pos =
        let heartFn (p : player) =
            if p.state = Dead then
                p.health <- 9;
                p.pos <- pos;
                g.showPlayer(p);
                true
            else false
        if not (Array.exists heartFn g.p) then
            // No dead players, so generate a monster
            g.m.set(pos, Ghost 2)
    member g.UseSmartBomb i =
        let p = g.p.(i)
        if p.bombs > 0 then
            p.bombs <- p.bombs - 1;
            g.DoSmartBomb()
    member g.DoSmartBomb() =
       g.PlayCue("kaboom")
       let m = g.m in
       let _, _, l,t,r,b = m.getActive(g.cog()) in
       for y = t to b-1 do
         for x = l to r-1 do
           let erase() = m.set(x,y,Space) in
           match m.get(x,y) with
           | Ghost _ -> erase()
           | Generator _ -> erase()
           | _ -> ()
         done
       done
    member g.ChangeLevel () =
       g.level <- min (g.level + 1) 25;
       g.load(g.level)
end

type TileTexture = class
    val SpriteScale : int
    val SpriteWidth : int
    val SpriteHeight : int 
    val mutable MyTexture : Texture2D
    val mutable SpriteStride : int
    
    new(spriteWidth, spriteHeight, spriteScale) =
        {
            SpriteScale = spriteScale
            SpriteWidth = spriteWidth
            SpriteHeight = spriteHeight
            MyTexture = null
            SpriteStride = 0
        }
        
    member this.SetTexture(tex) =
        this.MyTexture <- tex
        this.SpriteStride <- this.MyTexture.Width / this.SpriteWidth
    
    member this.Dispose() =
        this.MyTexture.Dispose()
        this.MyTexture <- null
        
    member this.DrawSprite ((batch : SpriteBatch), spriteIndex, (screenpos : Vector2)) =
        let (sx, sy) = remmod spriteIndex this.SpriteStride
        let sourcerect = new Rectangle(sx * this.SpriteWidth , sy * this.SpriteHeight, this.SpriteWidth, this.SpriteHeight)
        let nsourcerect = new Nullable<Rectangle>(sourcerect)
        let destRect = new Rectangle(Float32.to_int screenpos.X, Float32.to_int screenpos.Y, this.SpriteWidth * this.SpriteScale, this.SpriteHeight * this.SpriteScale)
        batch.Draw( this.MyTexture, destRect, nsourcerect, Color.White )
end

type DandyGame = class
    inherit Game as base
    
    val mutable graphics : GraphicsDeviceManager
    val mutable content : ContentManager
    val model : game
    
    // Graphics resources
    val tex : TileTexture
    val mutable batch : SpriteBatch
    val mutable scoreFont : SpriteFont

    // Input
    val mutable downKeys : Set<Keys>
    val oldGamePadState : GamePadState array
    
    // Audio
    val mutable audioEngine : AudioEngine
    val mutable waveBank : WaveBank
    val mutable soundBank : SoundBank
    
    new() as this =
        {
            model = new game()
            tex = new TileTexture(16, 16, 2)
            batch = null
            downKeys = Set.Empty()
            graphics = null
            content = null
            oldGamePadState = Array.zero_create 4
            audioEngine = null
            waveBank = null
            soundBank = null
            scoreFont = null
        }
        then
            this.graphics <- new GraphicsDeviceManager(this)
            this.content <- new ContentManager(this.Services)
            this.audioEngine <- new AudioEngine(this.audioEnginePath("DandySounds.xgs"))
            this.waveBank <- new WaveBank(this.audioEngine, this.audioEnginePath("Wave Bank.xwb"))
            this.soundBank <- new SoundBank(this.audioEngine, this.audioEnginePath("Sound Bank.xsb"))
            this.TargetElapsedTime <- new TimeSpan(500000L) // 20 Hz 333333L) // 30 Hz
            this.model.soundBank <- this.soundBank
            this.model.init()
            
    member this.audioEnginePath(suffix : string) =
        let sb = new System.Text.StringBuilder(300)
        sb.Append(StorageContainer.TitleLocation).Append(gameMediaPath).Append(@"Sounds\").Append(suffix).ToString()

    override this.LoadGraphicsContent(loadAllContent) =
        if loadAllContent then
            let device = this.graphics.GraphicsDevice
            this.tex.SetTexture(this.content.Load(@"Media\dandy"))
            this.batch <- new SpriteBatch(device)
            this.scoreFont <- this.content.Load(@"Media\Fonts\ui")
        
    override this.UnloadGraphicsContent(unloadAllContent) =
        if unloadAllContent then
            this.content.Unload()
            this.tex.Dispose()
            this.batch.Dispose()
            this.batch <- null
            // this.scoreFont.Dispose()
            this.scoreFont <- null
    
    member this.DoInput() =
        this.DoKeysInput()
        this.DoGamePadInput()
        
    member this.DoKeysInput() =
        let keyState = Keyboard.GetState()
        let pressedKeys = keyState.GetPressedKeys()
        let newKeys = Set.Create(pressedKeys)
        let newDown = newKeys - this.downKeys
        let newUp = this.downKeys - newKeys
        newDown.Iterate (fun key -> this.model.HandleEvent(true, key))
        newUp.Iterate (fun key -> this.model.HandleEvent(false, key))
        this.downKeys <- newKeys
    
    member this.DoGamePadInput() =
        for i = 0 to 3 do
            let gps = GamePad.GetState(g_players.[i])
            if gps.IsConnected then
                let ogps = this.oldGamePadState.(i)
                
                let report key newButtonState oldButtonState =
                    if newButtonState <> oldButtonState then
                        this.model.input.UpdatePadState(i, key, (newButtonState = ButtonState.Pressed))
                        
                report GameKeys.A gps.Buttons.A ogps.Buttons.A
                report GameKeys.B gps.Buttons.B ogps.Buttons.B
                report GameKeys.Left gps.DPad.Left ogps.DPad.Left
                report GameKeys.Down gps.DPad.Down ogps.DPad.Down
                report GameKeys.Right gps.DPad.Right ogps.DPad.Right
                report GameKeys.Up gps.DPad.Up ogps.DPad.Up
                report GameKeys.Start gps.Buttons.Start ogps.Buttons.Start
                report GameKeys.Back gps.Buttons.Back ogps.Buttons.Back
                
                let reportStick key newStickState oldStickState lowActive highActive =
                    let inRange state low high = low <= state && state <= high
                    let oldActive = inRange oldStickState lowActive highActive
                    let newActive = inRange newStickState lowActive highActive
                    if oldActive <> newActive then
                        this.model.input.UpdatePadState(i, key, newActive)
                        
                let lowLow, lowHigh, highLow, highHigh = -1.0f, -0.25f, 0.25f, 1.0f
                reportStick GameKeys.Left gps.ThumbSticks.Left.X ogps.ThumbSticks.Left.X lowLow lowHigh
                reportStick GameKeys.Right gps.ThumbSticks.Left.X ogps.ThumbSticks.Left.X highLow highHigh
                reportStick GameKeys.Up gps.ThumbSticks.Left.Y ogps.ThumbSticks.Left.Y highLow highHigh
                reportStick GameKeys.Down gps.ThumbSticks.Left.Y ogps.ThumbSticks.Left.Y lowLow lowHigh
                this.oldGamePadState.(i) <- gps
        done

    override this.Update(gameTime) =
        this.DoInput()
        this.model.Step()
        this.audioEngine.Update()
        base.Update(gameTime)
    
    override this.Draw(gameTime) =
        let gd = this.graphics.GraphicsDevice
        gd.Clear(Color.Black)
        let map = this.model.m
        let xoff, yoff, left, top, right, bottom = map.getActive(this.model.cog())
        let w, h = right - left, bottom - top
        let viewport = gd.Viewport
        let vpx, vpy, vpw, vph = float viewport.X, float viewport.Y, float viewport.Width, float viewport.Height
        let mapw, maph = tileSizeX * (float w), tileSizeY * (float h)
        let xbase, ybase = vpx + (vpw - mapw) / 2.0, vpy + (vph - maph) / 2.0
        this.batch.Begin()
        for y = top to bottom-1 do
            for x = left to right-1 do
                let tile = int_of_piece (map.get (x, y))
                let px = Float32.of_float (xbase + tileSizeX * (float (x - left)))
                let py = Float32.of_float (ybase + tileSizeY * (float (y - top)))
                this.tex.DrawSprite(this.batch, tile, new Vector2(px, py))
        this.batch.DrawString(this.scoreFont, "howdy!", new Vector2(10.0f, 10.0f), Color.White)
        this.batch.End()
        base.Draw(gameTime)
end

(* This code is now in the C# "WindowsDandy" and "XboxDandy" projects, along with all the content pipeline content.
let main() =
    let game = new DandyGame()
    game.Run()

[<STAThread>]
do main()
*)