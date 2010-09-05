// Dany360.cpp : Defines the entry point for the application.
//

#include "stdafx.h"

//-------------------------------------------------------------------------------------
// Vertex shader
// We use the register semantic here to directly define the input register
// matWVP.  Conversely, we could let the HLSL compiler decide and check the
// constant table.
//-------------------------------------------------------------------------------------
const char* g_strVertexShaderProgram = 
" struct VS_IN                                 "  
" {                                            " 
"     float4 ObjPos   : POSITION;              "  // Object space position 
"     float2 uv       : TEXCOORD;              "  // Vertex color                 
" };                                           " 
"                                              " 
" struct VS_OUT                                " 
" {                                            " 
"     float4 ProjPos  : POSITION;              "  // Projected space position 
"     float2 uv       : TEXCOORD;              "  
" };                                           "  
"                                              "  
" VS_OUT main( VS_IN In )                      "  
" {                                            "  
"     VS_OUT Out;                              "  
"     Out.ProjPos = In.ObjPos;                 "  // Transform vertex into
"     Out.uv = In.uv;                          "  // Projected space and 
"     return Out;                              "  // Transfer color
" }                                            ";

//-------------------------------------------------------------------------------------
// Pixel shader
//-------------------------------------------------------------------------------------
const char* g_strPixelShaderProgram = 
" sampler2D s;                                 "
" struct PS_IN                                 "
" {                                            "
"     float2 uv : TEXCOORD;                    "  // Interpolated color from                      
" };                                           "  // the vertex shader
"                                              "  
" float4 main( PS_IN In ) : COLOR              "  
" {                                            "  
"     return tex2D(s, In.uv);                  "  // Output color
" }                                            "; 


//-------------------------------------------------------------------------------------
// Time             Since fAppTime is a float, we need to keep the quadword app time 
//                  as a LARGE_INTEGER so that we don't lose precision after running
//                  for a long time.
//-------------------------------------------------------------------------------------
struct TimeInfo
{    
    LARGE_INTEGER qwTime;    
    LARGE_INTEGER qwAppTime;   

    float fAppTime;    
    float fElapsedTime;    

    float fSecsPerTick;    
};

//-------------------------------------------------------------------------------------
// CInterfacePtr<T> Helper class to make sure we always release our interfaces.
//                  This is a simple resource management class- there are subtleties
//                  when doing assignment or copy of smart pointers, so we make sure 
//                  they aren't called by making copy and assign private.
//-------------------------------------------------------------------------------------
template <class T>
class CInterfacePtr
{
public:
     CInterfacePtr(){ m_ptr=NULL; }
     CInterfacePtr(T*p){ m_ptr=p; }
    ~CInterfacePtr(){ if(m_ptr) m_ptr->Release(); }
     CInterfacePtr &operator = (T*p) { m_ptr = p; return *this; }

    T**  operator&()  { return &m_ptr; }
    T*   operator->() { return m_ptr; }
         operator T*(){ return m_ptr; }
   	bool operator!() { return (m_ptr == NULL); }

private:
    CInterfacePtr(const CInterfacePtr &p);                  // unimplemented copy
    CInterfacePtr &operator = (const CInterfacePtr &p);     // unimplemented assign

    T *m_ptr;
};

//-------------------------------------------------------------------------------------
// Global variables
//-------------------------------------------------------------------------------------
CInterfacePtr<IDirect3DDevice9>             g_pd3dDevice;    // Our rendering device
D3DPRESENT_PARAMETERS d3dpp; 
CInterfacePtr<IDirect3DVertexBuffer9>       g_pVB;           // Buffer to hold vertices
CInterfacePtr<IDirect3DVertexDeclaration9>  g_pVertexDecl;   // Vertex format decl
CInterfacePtr<IDirect3DVertexShader9>       g_pVertexShader; // Vertex Shader
CInterfacePtr<IDirect3DPixelShader9>        g_pPixelShader;  // Pixel Shader
CInterfacePtr<IDirect3DTexture9>            g_pTexture;      // Texture

// A structure for our custom vertex type. We added texture coordinates
struct CUSTOMVERTEX
{
    float x;
    float y;
    float z;
    float    tu;
    float    tv;
};

// Our custom FVF, which describes our custom vertex structure
#define D3DFVF_CUSTOMVERTEX (D3DFVF_XYZ | D3DFVF_TEX1)


D3DXMATRIX g_matWorld;
D3DXMATRIX g_matProj;
D3DXMATRIX g_matView;

TimeInfo g_Time;

BOOL g_bWidescreen = TRUE;

// Start of game

// The game goes here

void MyDebugBreak()
{
    DebugBreak();
}

void MyAssert(bool test)
{
    if(!test)
    {
        DebugBreak();
    }
}

enum Direction
{
    kDirUp,
    kDirUpRight,
    kDirRight,
    kDirDownRight,
    kDirDown,
    kDirDownLeft,
    kDirLeft,
    kDirUpLeft,
    kDirNone = 0xff
};

bool IsDiagonal(Direction dir)
{
    return (((DWORD) dir) & 1) != 0;
}

// Angle is expressed in 1/8ths of a circle:

Direction RotateBy(Direction dir, int angle)
{
    return (Direction) (0x7 & (((int) dir) + angle));
}

enum MapData
{
    kSpace,
    kWall,
    kLock,
    kUp,
    kDown,
    kKey,
    kFood,
    kMoney,
    kBomb,
    kGhost,
    kSmiley,
    kBig,
    kHeart,
    kGen1,
    kGen2,
    kGen3,
    kArrow0, // Down-left arrow
    kArrow1,
    kArrow2,
    kArrow3,
    kArrow4,
    kArrow5,
    kArrow6,
    kArrow7,
    kPlayer0, // Actually has a "1" on his chest
    kPlayer1,
    kPlayer2,
    kPlayer3
};

bool IsSlidable(MapData d)
{
    return d == kSpace || d == kMoney || (d >= kDown && d <= kBomb);
}

class Map
{
public:
    Map()
    {
        Init();
    }

    MapData Get(DWORD x, DWORD y)
    {
        MapData b = kSpace;
        if(x >= 0 && x < Width && y >= 0 && y < Height)
        {
            b = (MapData) Cell[x + y*Width];
        }
        else
        {
            MyDebugBreak();
        }
        return b;
    }

    MapData Get(DWORD x, DWORD y, Direction dir)
    {
        MapData b = kSpace;
        if(x >= 0 && x < Width && y >= 0 && y < Height)
        {
            b = (MapData) Cell[x + y*Width];
        }
        else
        {
            MyDebugBreak();
        }
        return b;
    }

    void Set(DWORD x, DWORD y, int v)
    {
        if(x >= 0 && x < Width && y >= 0 && y < Height && v <= kPlayer3)
        {
            Cell[x + y*Width] = v;
        }
        else
        {
            MyDebugBreak();
        }
    }

    bool Find(BYTE& rx, BYTE& ry, MapData v)
    {
        for(int y = 0; y < Height; y++)
        {
            for(int x = 0; x < Width; x++)
            {
                if(Cell[x + y * Width] == v)
                {
                    rx = x;
                    ry = y;
                    return true;
                }
            }
        }
        return false;
    }

    void OpenLock(DWORD x, DWORD y)
    {
        // Flood fill from this coord
        if(Cell[x + y * Width] == kLock)
        {
            Cell[x + y * Width] = kSpace;
            for(int dy = -1;dy <= 1; dy++)
                for(int dx = -1;dx <= 1; dx++)
                    if(dx != 0 || dy != 0)
                        OpenLock(x + dx, y + dy);
        }
    }

    void Init()
    {
        for(DWORD y = 0; y < Height; y++)
        {
            for(DWORD x = 0; x < Width; x++)
            {
                BYTE b = kSpace;
                if(y == 0 || y == Height-1 || x == 0 || x == Width - 1)
                {
                    b = kWall;
                }
                else if ( x == 2 && y == 2)
                {
                    b = kUp;
                }
                else if ( x == 10 && y == 10 )
                {
                    b = kDown;
                }
                Cell[y*Width+x] = b;
            }
        }
    }

    bool LoadLevel(DWORD index)
    {
        char fileName[MAX_PATH];
        FILE* in;
        sprintf(fileName, "d:\\levels\\level.%c", index + 'a');
        in = fopen(fileName, "rb");
        bool failed = true;
        if(in)
        {
            failed = false;
            for(int y = 0; y < Height; y++)
            {
                for(int x = 0; x < Width; x += 2)
                {
                    int inb = fgetc(in);
                    if(inb < 0)
                    {
                        failed = true;
                        break;
                    }
                    Cell[y*Width+x] = (BYTE) (inb & 0xf);
                    Cell[y*Width+x+1] = (BYTE) ((inb >> 4) & 0xf);
                }
            }
            fclose(in);
        }
        if(failed)
        {
            Init();
        }
        return !failed;
    }

    void GetActive(float& x, float& y, DWORD& left, DWORD& top, DWORD& right, DWORD& bottom)
    {
        GetActive1(x, left, right, Map::Width, Map::ViewWidth);
        GetActive1(y, top, bottom, Map::Height, Map::ViewHeight);
    }

    void GetActive1(float& x, DWORD& left, DWORD& right, DWORD width, DWORD viewWidth)
    {
        x -= (viewWidth / 2.0f);
        x = max(x, 0.f);
        x = min(x, width - viewWidth);
        left = (DWORD) x;
        right = min(left + viewWidth + 1, width);
    }

    const static DWORD Width = 60;
    const static DWORD Height = 30;
    const static DWORD NumCells = Width * Height;
    BYTE Cell[NumCells];

    const static DWORD ViewWidth = 20;
    const static DWORD ViewHeight = 10;
};

class Arrow
{
public:
    Arrow()
    {
        alive = false;
        x = 0;
        y = 0;
        dir = kDirNone;
    }

    static bool CanGo(MapData d)
    {
        return d == kSpace;
    }

    static bool CanHit(MapData d)
    {
        return d >= kBomb && d <= kGen3;
    }

    BYTE alive;
    BYTE x;
    BYTE y;
    Direction dir;
};

enum PlayerState
{
    kNotInGame,
    kNormal,
    kInWarp
};

class Player
{
public:
    Player()
    {
        Init();
    }

    void Init()
    {
        x = 0;
        y = 0;
        state = kNormal;
        health = kHealthMax;
        food = 0;
        bombs = 0;
        keys = 0;
        score = 0;
        dir = kDirNone;
        lastMoveTime = 0;
    }

    bool IsInGame()
    {
        return state != kNotInGame;
    }

    bool IsAlive()
    {
        return health > 0 && state != kNotInGame;
    }

    bool IsVisible()
    {
        return health > 0 && state == kNormal;
    }

    void EatFood()
    {
        if(food > 0 && health < kHealthMax)
        {
            --food;
            health = kHealthMax;
        }
    }

    static const int kHealthMax = 10;
    BYTE x;
    BYTE y;
    BYTE health;
    BYTE food;
    BYTE keys;
    BYTE bombs;
    DWORD score;
    PlayerState state;
    DWORD lastMoveTime;
    Direction dir;
    Arrow arrow;
};

class World
{
public:
    World()
    {
    }

    void Init()
    {
        map.Init();
        numPlayers = 0;
        for(DWORD i = 0; i < PlayerCount; i++)
        {
            player[i].Init();
            player[i].state = i < numPlayers ? kNormal : kNotInGame;
        }
    }

    void Update()
    {
        time = GetTickCount();

        GetCOG(cogX, cogY);
        map.GetActive(cogX, cogY, startX, startY, endX, endY);

        for(DWORD i = 0; i < numPlayers; i++)
        {
            DoArrowMove(&player[i], false);
        }

        DoMonsters();
    }

    bool IsGameOver()
    {
        for(DWORD i = 0; i < numPlayers; i++)
        {
            if(player[i].IsAlive())
            {
                return false;
            }
        }
        return true;
    }

    void DoMonsters()
    {
        // update in a grid pattern
        int gridStep = (time / (1000 / 60)) % 9;
        int gridXOffset = gridStep % 3;
        int gridYOffset = gridStep / 3;
        for(DWORD y = startY + gridYOffset; y < endY; y += 3)
        {
            for(DWORD x = startX + gridXOffset; x < endX; x += 3)
            {
                MapData d = map.Get(x, y);
                if(d >= kGhost && d <= kBig)
                {
                    // Move towards nearest player
                    Direction dir = GetDirectionOfNearestPlayer(x, y);
                    if(dir != kDirNone)
                    {
                        BYTE mx;
                        BYTE my;
                        bool canMove = false;
                        MapData d2;
                        for(int test = 0; test < 3; test++)
                        {
                            const static int kTestDelta[3] = {0,-1,1};
                            mx = (BYTE) x;
                            my = (BYTE) y;
                            MoveCoords(mx, my, (dir + kTestDelta[test]) & 7);
                            d2 = map.Get(mx, my);
                            if(d2 == kSpace || d2 >= kPlayer0 && d2 <= kPlayer3)
                            {
                                canMove = true;
                                break;
                            }
                        }
                        if(canMove)
                        {
                            map.Set(x, y, kSpace);
                            if(d2 >= kPlayer0 && d2 <= kPlayer3)
                            {
                                Player* p = &player[d2 - kPlayer0];
                                int monsterHit = d - kGhost + 1;
                                if(p->health > monsterHit)
                                {
                                    p->health -= monsterHit;
                                }
                                else
                                {
                                    KillPlayer(d2 - kPlayer0);
                                }
                            }
                            else
                            {
                                map.Set(mx, my, d);
                            }
                        }
                    }
                }
                else if(d >= kGen1 && d <= kGen3)
                {
                    // Random generator
                    if(getRandom(10) < 3)
                    {
                        BYTE gx = (BYTE) x;
                        BYTE gy = (BYTE) y;
                        MoveCoords(gx, gy, getRandom(4) * 2);
                        if(map.Get(gx,gy) == kSpace)
                        {
                            map.Set(gx, gy, (MapData) kGhost + (d - kGen1));
                        }
                    }
                }
            }
        }
    }

    static DWORD getRandom(DWORD range)
    {
        return rand() % range;
    }

    Direction GetDirectionOfNearestPlayer(DWORD x, DWORD y)
    {
        DWORD bestX = 0;
        DWORD bestY = 0;
        DWORD bestDistance = 10000;
        for(DWORD i = 0; i < numPlayers; i++)
        {
            Player *pP = &player[i];
            if(pP->IsVisible())
            {
                DWORD distance = abs((int) (pP->x - x)) + abs((int) (pP->y - y));
                if(distance < bestDistance)
                {
                    bestDistance = distance;
                    bestX = pP->x;
                    bestY = pP->y;
                }
            }
        }
        if(bestDistance == 10000)
        {
            return kDirNone;
        }
        int dx = bestX - x;
        int dy = bestY - y;
        BYTE bitField = 0;
        if(dy > 0) bitField |= 8;
        else if(dy < 0) bitField |= 4;
        if(dx > 0) bitField |= 2;
        else if(dx < 0) bitField |= 1;

        //     7 0 1
        //     6 + 2 
        //     5 4 3 

        const static BYTE kDirTable[16] =
        {
            // YyXx
            255, // 0000
                6, // 0001
                2, // 0010
                255, // 0011
                0, // 0100
                7, // 0101
                1, // 0110
                255, // 0111
                4, // 1000
                5, // 1001
                3, // 1010
                255, // 1011
                255, // 1100
                255, // 1101
                255, // 1110
                255, // 1111
        };

        return (Direction) kDirTable[bitField];
    }

    void GetCOG(float& x, float& y)
    {
        x = 0.f;
        y = 0.f;
        int liveCount = 0;
        for(DWORD i = 0; i < numPlayers; i++)
        {
            Player *pP = &player[i];
            if(pP->IsVisible())
            {
                x += pP->x;
                y += pP->y;
                ++liveCount;
            }
        }
        if(liveCount)
        {
            x /= liveCount;
            y /= liveCount;
        }
        else
        {
            BYTE dx, dy;
            FindUp(dx, dy);
            x = dx;
            y = dy;
        }
    }

    void LoadLevel(DWORD index)
    {
        if(map.LoadLevel(index))
        {
            level = (BYTE) index;
        }
        else
        {
            level = 0;
            map.LoadLevel(0);
        }
        SetPlayerPositions();
    }

    void ChangeLevel(int delta)
    {
        DWORD newLevel = min(26, level + delta);
        LoadLevel(newLevel);
    }

    void FindUp(BYTE& x, BYTE& y)
    {
        if(!map.Find(x, y, kUp))
        {
            MyDebugBreak();
            x = 4;
            y = 4;
        }
    }

    void SetPlayerPositions()
    {
        BYTE x;
        BYTE y;
        FindUp(x, y);
        for(DWORD i = 0; i < numPlayers; i++)
        {
            Player* p = &player[i];
            if(p->IsAlive())
            {
                BYTE px = x;
                BYTE py = y;
                MoveCoords(px, py, i * 2);
                PlaceInWorld(i, px, py);
            }
        }
    }

    void AddPlayer(DWORD index)
    {
        BYTE x;
        BYTE y;
        FindUp(x,y);
        Player* p = &player[index];
        MyAssert(!p->IsAlive());
        p->Init();
        numPlayers = max(numPlayers, index + 1);
        BYTE px = x;
        BYTE py = y;
        DWORD direction = index * 2;
        MoveCoords(px, py, direction);
        PlaceInWorld(index, px, py);
    }

    void KillPlayer(DWORD index)
    {
        Player* p = &player[index];
        p->health = 0;
        MapData remains = kSpace;
        if(p->keys)
        {
            --p->keys;
            remains = kKey;
        }
        map.Set(p->x, p->y, remains);
    }

    void PlaceInWorld(DWORD index, DWORD x, DWORD y)
    {
        Player* p = &player[index];
        MyAssert(p->IsAlive());
        p->x = (BYTE) x;
        p->y = (BYTE) y;
        p->dir = (Direction) (index * 2);
        map.Set(p->x, p->y, (MapData) (kPlayer0 + index));
        p->state = kNormal;
        p->arrow.alive = false;
    }

    void Move(DWORD stick, Direction dir)
    {
        if(stick < 4 && dir < 8)
        {
            if(stick < numPlayers)
            {
                Player* p = &player[stick];
                p->dir = dir;
                if(p->IsVisible() && time - p->lastMoveTime >= kMsPerMove)
                {
                    p->lastMoveTime = time;
                    BYTE x = p->x;
                    BYTE y = p->y;
                    MoveCoords(x, y, dir);
                    MapData d = map.Get(x,y);

                    if(d == kWall)
                    {
                        // See if we can slide along the wall
                        if(IsDiagonal(dir))
                        {
                            for(int slideAngle = -1; slideAngle <= 1; slideAngle += 2)
                            {
                                BYTE x2 = p->x;
                                BYTE y2 = p->y;
                                MoveCoords(x2, y2, RotateBy(dir, slideAngle));
                                MapData d2 = map.Get(x2,y2);
                                if(IsSlidable(d2))
                                {
                                    x = x2;
                                    y = y2;
                                    d = d2;
                                    break;
                                }
                            }
                        }
                    }
                    bool bMove = false;
                    switch(d)
                    {
                    case kSpace:
                        bMove = true;
                        break;
                    case kLock:
                        if(p->keys)
                        {
                            --p->keys;
                            map.OpenLock(x, y);
                            bMove = true;
                        }
                        break;
                    case kKey:
                        ++p->keys;
                        bMove = true;
                        break;
                    case kFood:
                        ++p->food;
                        bMove = true;
                        break;
                    case kMoney:
                        p->score += 10;
                        bMove = true;
                        break;
                    case kBomb:
                        ++p->bombs;
                        bMove = true;
                        break;
                    case kDown:
                        {
                            p->state = kInWarp;
                            map.Set(p->x, p->y, kSpace);
                            if(IsPartyInWarp())
                            {
                                ChangeLevel(1);
                            }
                        }
                        break;
                    default:
                        break;
                    }
                    if(bMove)
                    {
                        map.Set(p->x, p->y, kSpace);
                        map.Set(x, y, kPlayer0 + stick);
                        p->x = x;
                        p->y = y;
                    }
                }

            }
        }
        else
        {
            MyDebugBreak();
        }
    }

    bool IsPartyInWarp()
    {
        // At least one player in warp, and no players visible
        bool atLeastOneWarp = false;
        bool atLeastOneVisible = false;
        for(DWORD i = 0; i < numPlayers;i++)
        {
            if(player[i].IsVisible())
            {
                atLeastOneVisible = true;
                break;
            }
            if(player[i].IsAlive() && player[i].state == kInWarp)
            {
                atLeastOneWarp = true;
            }
        }
        if(atLeastOneWarp && ! atLeastOneVisible)
        {
            return true;
        }
        return false;
    }

    void EatFood(DWORD index)
    {
        if(index < numPlayers)
        {
            Player* p = &player[index];
            if(p->IsVisible())
            {
                p->EatFood();
            }
        }
    }

    void Fire(DWORD index)
    {
        if(index < numPlayers)
        {
            Player* p = &player[index];
            if(!p->arrow.alive)
            {
                p->arrow.alive = true;
                p->arrow.x = p->x;
                p->arrow.y = p->y;
                p->arrow.dir = p->dir;
                DoArrowMove(p, true);
            }
        }
        else
        {
            MyDebugBreak();
        }
    }

    void DoArrowMove(Player* p, bool isFirstMove)
    {
        if(!p->arrow.alive)
        {
            return;
        }
        BYTE x = p->arrow.x;
        BYTE y = p->arrow.y;
        if(!isFirstMove)
        {
            map.Set(x, y, kSpace);
        }
        MoveCoords(x, y, p->arrow.dir);
        if( x < startX || y < startY || x >= endX || y >= endY)
        {
            p->arrow.alive = false;
        }
        else
        {
            MapData d = map.Get(x,y);
            if(Arrow::CanHit(d))
            {
                switch(d)
                {
                case kBomb:
                    DoSmartBomb();
                    map.Set(x, y, kSpace);
                    break;
                case kGhost:
                case kGen1:
                    map.Set(x, y, kSpace);
                    break;
                case kSmiley:
                case kBig:
                case kGen2:
                case kGen3:
                    map.Set(x, y, d-1);
                    break;
                case kHeart:
                    {
                        bool foundPlayer = false;
                        for(DWORD i = 0; i < numPlayers; i++)
                        {
                            Player* p = &player[i];
                            if(!p->IsAlive())
                            {
                                p->health = 9;
                                p->state = kNormal;
                                PlaceInWorld(i, x, y);
                                foundPlayer = true;
                                break;
                            }
                        }
                        if(!foundPlayer)
                        {
                            map.Set(x, y, kBig);
                        }
                    }
                    break;
                default:
                    MyDebugBreak();
                }
                p->arrow.alive = false;
            }
            else if(Arrow::CanGo(d))
            {
                p->arrow.x = x;
                p->arrow.y = y;
                int rotatedDir = ((p->arrow.dir + 3) & 7); // Because font is screwed up
                map.Set(x, y, kArrow0 + rotatedDir);
            }
            else
            {
                p->arrow.alive = false;
            }
        }
    }

    void UseSmartBomb(DWORD index)
    {
        if(index < numPlayers)
        {
            Player* p = &player[index];
            if(p->bombs)
            {
                --p->bombs;
                DoSmartBomb();
            }
        }
        else
        {
            MyDebugBreak();
        }
    }

    void DoSmartBomb()
    {
        float cogX;
        float cogY;
        DWORD startX;
        DWORD endX;
        DWORD startY;
        DWORD endY;
        GetCOG(cogX, cogY);
        map.GetActive(cogX, cogY, startX, startY, endX, endY);
        for(DWORD y = startX; y < endY; y++)
        {
            for(DWORD x = startX; x < endX; x++)
            {
                MapData d = map.Get(x, y);
                if(d >= kGhost && d <= kBig || d >= kGen1 && d <= kGen3)
                {
                    map.Set(x, y, kSpace);
                }
            }
        }
    }

    static void MoveCoords(BYTE& x, BYTE& y, DWORD direction)
    {
        if(direction < 8)
        {
            // Up is zero, clockwise
            static signed char kOffsets[8][2] =
            {
                {0,-1},{1,-1},{1,0},{1,1},{0,1},{-1,1},{-1,0},{-1,-1}
            };
            x += kOffsets[direction][0];
            y += kOffsets[direction][1];
        }
        else
        {
            MyDebugBreak();
        }
    }
    Map map;
    BYTE level;
    const static int PlayerCount = 4;
    Player player[PlayerCount];
    DWORD numPlayers;
    DWORD time;

    // This information is updated once per tick:

    float cogX; // Center of group
    float cogY;
    DWORD startX; // bounds of active (visible) map
    DWORD endX;
    DWORD startY;
    DWORD endY;

    static const DWORD kMsPerMove = (1000 / 60) * 3;
};

class GamePad
{
public:
    GamePad()
    {
        buttons = 0;
        strobe = 0;
    }

    static const int kUp = 1; // Mask for up button
    static const int kDown = 2;
    static const int kLeft = 4;
    static const int kRight = 8;
    static const int kA = 16;
    static const int kB = 32;
    static const int kX = 64;
    static const int kY = 128;
    static const int kC = 256;
    static const int kD = 512;
    WORD buttons;	// bit set if button is currently pressed down
    WORD strobe;	// bit set if button is newly pressed down
};

class Keyboard
{
public:
    Keyboard()
    {
        memset(data,0, sizeof(data));
    }
    void HandleEvent(bool down, BYTE key)
    {
        data[key] = down;
    }
    static const int KeySize = 256;
    bool data[KeySize];

};

const DWORD kNumVerts = Map::NumCells * 6;

class View
{
public:
    View()
    {
    }

    void Render(World& world)
    {

        // Clear the back buffer
        g_pd3dDevice->Clear( 0L, NULL, D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER|D3DCLEAR_STENCIL, 
            D3DCOLOR_XRGB(0,0,0), 1.0f, 0L );

        // Draw the triangles in the vertex buffer. This is broken into a few steps:

        g_pd3dDevice->SetVertexShader( g_pVertexShader );
        g_pd3dDevice->SetPixelShader( g_pPixelShader );

        g_pd3dDevice->SetStreamSource(0, NULL, 0, 0);

        // Fill the vertex buffer. We are setting the tu and tv texture
        // coordinates, which range from 0.0 to 1.0
        CUSTOMVERTEX* pVertices;
        if( FAILED( g_pVB->Lock( 0, 0, (void**)&pVertices, 0 ) ) )
            return;

        float x;
        float y;
        world.GetCOG(x, y);

        DWORD numTris = DrawToTexture(world.map, pVertices, kNumVerts, x, y);
        g_pVB->Unlock();

        g_pd3dDevice->SetTexture( 0, g_pTexture );

        // Render the vertex buffer contents
        g_pd3dDevice->SetRenderState(D3DRS_VIEWPORTENABLE, FALSE);
        g_pd3dDevice->SetRenderState( D3DRS_CULLMODE, D3DCULL_NONE );

        g_pd3dDevice->SetStreamSource( 0, g_pVB, 0, sizeof(CUSTOMVERTEX) );
        g_pd3dDevice->SetFVF( D3DFVF_CUSTOMVERTEX );
        g_pd3dDevice->DrawPrimitive( D3DPT_TRIANGLELIST, 0, numTris );
    }

    DWORD DrawToTexture(Map& map, CUSTOMVERTEX* pV, DWORD numV, float cogX, float cogY)
    {
        static const float CellSize = 32.0f;
        static const float uTexelSize = 1.0f / 256.0f;
        static const float vTexelSize = 1.0f / 32.0f;
        static const DWORD uChars = 16;
        static const DWORD vChars = 2;
        static const float uScale = 1.0f / uChars;
        static const float vScale = 1.0f / vChars;
        static const float uBase = 0.0f;
        static const float vBase = 1.0f;

        static const float viewBaseX = 0.0f;
        static const float viewBaseY = 70.0f;

        CUSTOMVERTEX* pTri = pV;

        DWORD startX;
        DWORD endX;
        DWORD startY;
        DWORD endY;
        map.GetActive(cogX, cogY, startX, startY, endX, endY);

        const float xBase = viewBaseX -cogX * CellSize - 0.5f;
        const float yBase = viewBaseY -cogY * CellSize - 0.5f;

        DWORD dwNumTris = 0;
        for(DWORD x = startX; x < endX; x++)
        {
            for(DWORD y = startY; y < endY; y ++)
            {
                BYTE b = map.Get(x, y);
                float uLow = (b % uChars) * uScale;
                float uHigh = uLow + uScale;
                float vLow = (b / uChars) * vScale;
                float vHigh = vLow + vScale;

                float xLow = xBase + x * CellSize;
                float xHigh = xLow + CellSize;
                float yLow = yBase + y * CellSize;
                float yHigh = yLow + CellSize;

                // Set the two triangles

                // First triangle
                pTri->x = xLow;
                pTri->y = yLow;
                pTri->z = 0.f;
                pTri->tu = uLow;
                pTri->tv = vLow;

                pTri++;

                pTri->x = xHigh;
                pTri->y = yLow;
                pTri->z = 0.f;
                pTri->tu = uHigh;
                pTri->tv = vLow;

                pTri++;

                pTri->x = xLow;
                pTri->y = yHigh;
                pTri->z = 0.f;
                pTri->tu = uLow;
                pTri->tv = vHigh;

                // Second triangle
                pTri++;

                pTri->x = xLow;
                pTri->y = yHigh;
                pTri->z = 0.f;
                pTri->tu = uLow;
                pTri->tv = vHigh;

                pTri++;

                pTri->x = xHigh;
                pTri->y = yLow;
                pTri->z = 0.f;
                pTri->tu = uHigh;
                pTri->tv = vLow;

                pTri++;

                pTri->x = xHigh;
                pTri->y = yHigh;
                pTri->z = 0.f;
                pTri->tu = uHigh;
                pTri->tv = vHigh;

                pTri++;

                dwNumTris += 2;
            }
        }
        return dwNumTris;
    }
};

class Game
{
public:
    Game()
    {
        Init();
    }

    void Init()
    {
        world.Init();
    }

    void Start()
    {
        Init();
        world.LoadLevel(0);
    }
    void Render()
    {
        view.Render(world);
    }

    static const SHORT INPUT_DEADZONE = (SHORT)( 0.24f * FLOAT(0x7FFF) );

    //--------------------------------------------------------------------------------------
    // Name: ConvertThumbstickValue()
    // Desc: Converts SHORT thumbstick values to FLOAT, while enforcing a deadzone
    //--------------------------------------------------------------------------------------
    inline FLOAT ConvertThumbstickValue( SHORT sThumbstickValue )
    {
        if( sThumbstickValue > +INPUT_DEADZONE )
        {
            return (sThumbstickValue-INPUT_DEADZONE) / (32767.0f-INPUT_DEADZONE);
        }
        if( sThumbstickValue < -INPUT_DEADZONE )
        {
            return (sThumbstickValue+INPUT_DEADZONE+1.0f) / (32767.0f-INPUT_DEADZONE);
        }
        return 0.0f;
    }

    void Input()
    {
        // Clear strobes

        for(DWORD i = 0; i < 4; i++)
        {
            WORD oldState = gamepad[i].buttons;
            gamepad[i].buttons = 0;
            XINPUT_STATE input;
            if( ERROR_SUCCESS == XInputGetState( i, &input ))
            {
                DWORD pad = i;
                DWORD mask = 0;
                if(!world.player[i].IsAlive() )
                {
                    world.AddPlayer(i);
                }
                if(input.Gamepad.sThumbLX > INPUT_DEADZONE)
                {
                    mask |= GamePad::kRight;
                }
                else if(input.Gamepad.sThumbLX < -INPUT_DEADZONE)
                {
                    mask |= GamePad::kLeft;
                }

                if(input.Gamepad.sThumbLY > INPUT_DEADZONE)
                {
                    mask |= GamePad::kUp;
                }
                else if(input.Gamepad.sThumbLY < -INPUT_DEADZONE)
                {
                    mask |= GamePad::kDown;
                }

                struct PadMapEntry {
                    WORD wButton;
                    WORD mask;
                };

                PadMapEntry map[] = {
                    {XINPUT_GAMEPAD_DPAD_LEFT, GamePad::kLeft},
                    {XINPUT_GAMEPAD_DPAD_DOWN, GamePad::kDown},
                    {XINPUT_GAMEPAD_DPAD_RIGHT, GamePad::kRight},
                    {XINPUT_GAMEPAD_DPAD_UP, GamePad::kUp},
                    {XINPUT_GAMEPAD_A, GamePad::kA},
                    {XINPUT_GAMEPAD_B, GamePad::kB},
                    {XINPUT_GAMEPAD_X, GamePad::kX},
                    {XINPUT_GAMEPAD_Y, GamePad::kY},

                    {XINPUT_GAMEPAD_LEFT_THUMB, GamePad::kD}, // For development go down to next level

                    {0, 0}
                };

                for(PadMapEntry* pE = map; pE->wButton != 0; pE++)
                {
                    if((pE->wButton & input.Gamepad.wButtons) != 0)
                    {
                        mask |= pE->mask;
                    }
                }

                gamepad[pad].buttons |= mask;
            }
            else {
                if(world.player[i].IsAlive() )
                {
                    world.KillPlayer(i);
                }
            }
            gamepad[i].strobe = gamepad[i].buttons & ~ oldState;
        }
    }

    void Step()
    {
        world.Update();
        MovePlayers();
        if(world.IsGameOver())
        {
            Start();
        }
    }

    void MovePlayers()
    {
        for(DWORD i = 0; i < world.numPlayers; i++)
        {
            GamePad* pPad = & gamepad[i];
            static Direction kPadToDir[] =
            {
                // Bitfield is Right Left Down Up
                // Directions are clockwise from up == 0
                kDirNone, // 0000
                kDirUp, // 0001 
                kDirDown, // 0010
                kDirNone, // 0011 
                kDirLeft, // 0100
                kDirUpLeft, // 0101
                kDirDownLeft, // 0110
                kDirLeft, // 0111
                kDirRight, // 1000
                kDirUpRight, // 1001
                kDirDownRight, // 1010
                kDirRight, // 1011
                kDirNone, // 1100
                kDirUp, // 1101 
                kDirDown, // 1110 
                kDirNone, // 1111 
            };
            Direction dir = kPadToDir[0xf & pPad->buttons];
            if(dir != kDirNone)
            {
                world.Move(i, dir);
            }

            // Handle strobes
            if(pPad->buttons & GamePad::kA)
            {
                world.Fire(i);
            }
            if(pPad->strobe & GamePad::kY)
            {
                world.EatFood(i);
            }
            if(pPad->strobe & GamePad::kB)
            {
                world.UseSmartBomb(i);
            }

            if(pPad->strobe & GamePad::kD)
            {
                if(i == 0)
                {
                    world.ChangeLevel(1); // For debugging
                }
            }
        }
    }

    World world;
    GamePad gamepad[World::PlayerCount];
    Keyboard keyboard;
    View view;
};

Game gGame;

//-----------------------------------------------------------------------------
// Name: InitGeometry()
// Desc: Create the textures and vertex buffers
//-----------------------------------------------------------------------------
HRESULT InitGeometry()
{
    // Use D3DX to create a texture from a file based image
    if( FAILED( D3DXCreateTextureFromFile( g_pd3dDevice, "d:\\Dandy.bmp", &g_pTexture ) ) )
    {
        OutputDebugString("Could not find d:\\Dandy.bmp\n");
        return E_FAIL;
    }

    // Create the vertex buffer.
    if( FAILED( g_pd3dDevice->CreateVertexBuffer( kNumVerts*sizeof(CUSTOMVERTEX),
        D3DUSAGE_WRITEONLY, D3DFVF_CUSTOMVERTEX,
        D3DPOOL_DEFAULT, &g_pVB, NULL ) ) )
    {
        return E_FAIL;
    }

    return S_OK;
}


// End of game

HRESULT InitD3D()
{
    // Create the D3D object.
    CInterfacePtr<IDirect3D9> pD3D;
    pD3D = Direct3DCreate9( D3D_SDK_VERSION );
    if( !pD3D )
        return E_FAIL;

    // Set up the structure used to create the D3DDevice.
    ZeroMemory( &d3dpp, sizeof(d3dpp) );
    XVIDEO_MODE VideoMode;
    XGetVideoMode( &VideoMode );
    g_bWidescreen = VideoMode.fIsWideScreen;
    d3dpp.BackBufferWidth        = 640; // min( VideoMode.dwDisplayWidth, 1280 );
    d3dpp.BackBufferHeight       = 480; // min( VideoMode.dwDisplayHeight, 720 );
    d3dpp.BackBufferFormat       = D3DFMT_X8R8G8B8;
    d3dpp.BackBufferCount        = 1;
    d3dpp.EnableAutoDepthStencil = TRUE;
    d3dpp.AutoDepthStencilFormat = D3DFMT_D24S8;
    d3dpp.SwapEffect             = D3DSWAPEFFECT_DISCARD;
    d3dpp.PresentationInterval   = D3DPRESENT_INTERVAL_TWO; // 30 Hz game

    // Create the Direct3D device.
    if( FAILED( pD3D->CreateDevice( 0, D3DDEVTYPE_HAL, NULL,
        D3DCREATE_HARDWARE_VERTEXPROCESSING,
        &d3dpp, &g_pd3dDevice ) ) )
        return E_FAIL;

    return S_OK;
}


//-------------------------------------------------------------------------------------
// Name: InitScene()
// Desc: Creates the scene.  First we compile our shaders. For the final version
//       of a game, you should store the shaders in binary form; don't call 
//       D3DXCompileShader at runtime. Next, we declare the format of our 
//       vertices, and then create a vertex buffer. The vertex buffer is basically
//       just a chunk of memory that holds vertices. After creating it, we must 
//       Lock()/Unlock() it to fill it. Finally, we set up our world, projection,
//       and view matrices.
//-------------------------------------------------------------------------------------
HRESULT InitScene()
{
    // Compile vertex shader.
    CInterfacePtr<ID3DXBuffer> pVertexShaderCode;
    CInterfacePtr<ID3DXBuffer> pVertexErrorMsg;
    HRESULT hr = D3DXCompileShader( g_strVertexShaderProgram, 
        (UINT)strlen( g_strVertexShaderProgram ),
        NULL, 
        NULL, 
        "main", 
        "vs_2_0", 
        0, 
        &pVertexShaderCode, 
        &pVertexErrorMsg, 
        NULL );
    if( FAILED(hr) )
    {
        if( pVertexErrorMsg )
            OutputDebugString( (char*)pVertexErrorMsg->GetBufferPointer() );
        return E_FAIL;
    }    

    // Create vertex shader.
    g_pd3dDevice->CreateVertexShader( (DWORD*)pVertexShaderCode->GetBufferPointer(), 
        &g_pVertexShader );

    // Compile pixel shader.
    CInterfacePtr<ID3DXBuffer> pPixelShaderCode;
    CInterfacePtr<ID3DXBuffer> pPixelErrorMsg;
    hr = D3DXCompileShader( g_strPixelShaderProgram, 
        (UINT)strlen( g_strPixelShaderProgram ),
        NULL, 
        NULL, 
        "main", 
        "ps_2_0", 
        0, 
        &pPixelShaderCode, 
        &pPixelErrorMsg,
        NULL );
    if( FAILED(hr) )
    {
        if( pPixelErrorMsg )
            OutputDebugString( (char*)pPixelErrorMsg->GetBufferPointer() );
        return E_FAIL;
    }

    // Create pixel shader.
    g_pd3dDevice->CreatePixelShader( (DWORD*)pPixelShaderCode->GetBufferPointer(), 
        &g_pPixelShader );

    // Define the vertex elements and
    // Create a vertex declaration from the element descriptions.
    D3DVERTEXELEMENT9 VertexElements[3] =
    {
        { 0,  0, D3DDECLTYPE_FLOAT3, D3DDECLMETHOD_DEFAULT, D3DDECLUSAGE_POSITION, 0 },
        { 0, 12, D3DDECLTYPE_FLOAT2, D3DDECLMETHOD_DEFAULT, D3DDECLUSAGE_TEXCOORD, 0 },
        D3DDECL_END()
    };
    g_pd3dDevice->CreateVertexDeclaration( VertexElements, &g_pVertexDecl );

    return S_OK;
}

// XUI stuff

//--------------------------------------------------------------------------------------
// Scene implementation class.
//--------------------------------------------------------------------------------------
class CMyMainScene : public CXuiSceneImpl
{

protected:

    // Control and Element wrapper objects.
    CXuiControl m_playButton;
    CXuiControl m_HelpButton;
    CXuiTextElement m_text1;

    // Message map.
    XUI_BEGIN_MSG_MAP()
        XUI_ON_XM_INIT( OnInit )
        // XUI_ON_XM_NOTIFY_PRESS( OnNotifyPress )
        XUI_END_MSG_MAP()

        //----------------------------------------------------------------------------------
        // Performs initialization tasks - retrieves controls.
        //----------------------------------------------------------------------------------
        HRESULT OnInit( XUIMessageInit *pInitData, BOOL& bHandled )
    {
        // Retrieve controls for later use.
        GetChildById( L"Play", &m_playButton );
        GetChildById( L"Help", &m_HelpButton );
        GetChildById( L"XuiText1", &m_text1 );
        return S_OK;
    }

#if 0
    //----------------------------------------------------------------------------------
    // Handler for the button press message.
    //----------------------------------------------------------------------------------
    HRESULT OnNotifyPress( HXUIOBJ hObjPressed, BOOL& bHandled )
    {
        // Determine which button was pressed,
        // and set the text accordingly.
        if ( hObjPressed == m_playButton )
            m_text1.SetText( L"Play" );
        else if ( hObjPressed == m_HelpButton )
            m_text1.SetText( L"Help" );
        else
            return S_OK;

        bHandled = TRUE;
        return S_OK;
    }

#endif

public:

    // Define the class. The class name must match the ClassOverride property
    // set for the scene in the UI Authoring tool.
    XUI_IMPLEMENT_CLASS(CMyMainScene, L"DandyMainScene", XUI_CLASS_SCENE)
};

class CPlayScene : public CXuiSceneImpl
{

protected:

    // Control and Element wrapper objects.
    CXuiTextElement m_playerText[4];

    // Message map.
    XUI_BEGIN_MSG_MAP()
        XUI_ON_XM_INIT( OnInit )
        XUI_ON_XM_RENDER( OnNotifyRender )
    XUI_END_MSG_MAP()

        //----------------------------------------------------------------------------------
        // Performs initialization tasks - retrieves controls.
        //----------------------------------------------------------------------------------
        HRESULT OnInit( XUIMessageInit *pInitData, BOOL& bHandled )
    {
        // Retrieve controls for later use.
        GetChildById( L"XuiText1", &m_playerText[0] );
        GetChildById( L"XuiText2", &m_playerText[1] );
        GetChildById( L"XuiText3", &m_playerText[2] );
        GetChildById( L"XuiText4", &m_playerText[3] );
        return S_OK;
    }

    HRESULT OnNotifyRender(XUIMessageRender *pRenderData, BOOL& bHandled)
    {
        for(DWORD i = 0; i < 4; i++)
        {
            WCHAR buf[100];
            Player* p = &gGame.world.player[i];
            if(p->IsInGame())
            {
                wsprintfW(buf, L"P%d $%u H %3u%% F %u B %u",
                    i+1, p->score, p->health*10, p->food, p->bombs);
            }
            else
            {
                buf[0] = 0;
            }
            m_playerText[i].SetText(buf);
        }
        return S_OK;
    }

public:

    // Define the class. The class name must match the ClassOverride property
    // set for the scene in the UI Authoring tool.
    XUI_IMPLEMENT_CLASS(CPlayScene, L"PlayScene", XUI_CLASS_SCENE)
};

//--------------------------------------------------------------------------------------
// Main XUI host class. It is responsible for registering scene classes and provide
// basic initialization, scene loading and rendering capability.
//--------------------------------------------------------------------------------------
class CMyApp : public CXuiModule
{

protected:
    // Override RegisterXuiClasses so that CMyApp can register classes.
    virtual HRESULT RegisterXuiClasses();

    // Override UnregisterXuiClasses so that CMyApp can unregister classes. 
    virtual HRESULT UnregisterXuiClasses();


};


//--------------------------------------------------------------------------------------
// Name: RegisterXuiClasses
// Desc: Registers all the scene classes.
//--------------------------------------------------------------------------------------
HRESULT CMyApp::RegisterXuiClasses()
{
    HRESULT hr = CMyMainScene::Register();
    if(FAILED(hr))
        goto exit;
    hr = CPlayScene::Register();
    if(FAILED(hr))
        goto exit;

exit:
    return hr;
}


//--------------------------------------------------------------------------------------
// Name: UnregisterXuiClasses
// Desc: Unregisters all the scene classes.
//--------------------------------------------------------------------------------------
HRESULT CMyApp::UnregisterXuiClasses()
{
    CMyMainScene::Unregister();
    CPlayScene::Unregister();
    return S_OK;
}


//--------------------------------------------------------------------------------------
// Name: RegisterXuiClasses
// Desc: Application entry point.
//--------------------------------------------------------------------------------------
VOID __cdecl main()
{

    // Initialize Direct3D
    if( FAILED( InitD3D() ) )
        return;

    if( FAILED( InitScene() ) )
        return;

    gGame.Start();

    InitGeometry();

    // Declare an instance of the XUI framework application.
    CMyApp app;

    // Initialize the application.    
    HRESULT hr = app.InitShared(g_pd3dDevice, &d3dpp, XuiD3DXTextureLoader);
    if ( FAILED(hr) )
    {
        OutputDebugString( "Failed initializing application.\n" );
        return;
    }

    // Register a default typeface
    hr = app.RegisterDefaultTypeface(L"Arial Unicode MS", L"file://game:/xarialuni.ttf");
    if( FAILED(hr) ) 
    {
        OutputDebugString( "Failed to register default typeface.\n" );
        return;
    }

    // Load the skin file used for the scene.
    app.LoadSkin( L"file://game:/xui/dandy.xzp#xui/skin_dandy.xur" );

    // Load the scene.
    app.LoadFirstScene( L"file://game:/xui/dandy.xzp#", L"xui/main.xur", NULL );

    for(;;) // loop forever
    {
        hr = XuiTimersRun();
        app.RunFrame();
        gGame.Input();

        gGame.Step();

        // Render the scene
        gGame.Render();
        hr = app.Render();

        // Present the backbuffer contents to the display
        g_pd3dDevice->Present( NULL, NULL, NULL, NULL );
    }

    // Free resources, unregister custom classes, and exit.
    app.Uninit();
}
