#include <Windows.h>
#include <mmsystem.h>
#include <d3dx9.h>
#include <stdio.h>

//-----------------------------------------------------------------------------
// Global variables
//-----------------------------------------------------------------------------
LPDIRECT3D9             g_pD3D       = NULL; // Used to create the D3DDevice
LPDIRECT3DDEVICE9       g_pd3dDevice = NULL; // Our rendering device
LPDIRECT3DVERTEXBUFFER9 g_pVB        = NULL; // Buffer to hold vertices
LPDIRECT3DTEXTURE9      g_pTexture   = NULL; // Our texture

// A structure for our custom vertex type. We added texture coordinates
struct CUSTOMVERTEX
{
    float x;
    float y;
    float z;
    float rhw;
	float    tu;
	float    tv;
};

// Our custom FVF, which describes our custom vertex structure
#define D3DFVF_CUSTOMVERTEX (D3DFVF_XYZRHW | D3DFVF_TEX1)


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
	kPlayer0, // Actually has a "1" on his cheast
	kPlayer1,
	kPlayer2,
	kPlayer3
};

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
		sprintf(fileName, "levels\\level.%c", index + 'a');
		if((in = fopen(fileName, "rb")) == NULL)
		{
			sprintf(fileName, "..\\levels\\level.%c", index + 'a');
			in = fopen(fileName, "rb");
		}
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

	bool alive;
	BYTE x;
	BYTE y;
	Direction dir;
};

enum PlayerState
{
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

	bool IsAlive()
	{
		return health > 0;
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

	static const int kHealthMax = 9;
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
		numPlayers = 2;
		for(DWORD i = 0; i < numPlayers; i++)
		{
			player[i].Init();
		}
	}

	void Update()
	{
		time = GetTickCount();

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
		float cogX;
		float cogY;
		DWORD startX;
		DWORD endX;
		DWORD startY;
		DWORD endY;
		GetCOG(cogX, cogY);
		map.GetActive(cogX, cogY, startX, startY, endX, endY);

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
									p->health = 0;
									MapData remains = kSpace;
									if(p->keys)
									{
										--p->keys;
										remains = kKey;
									}
									map.Set(p->x, p->y, remains);
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

	void SetPlayerPositions()
	{
		BYTE x;
		BYTE y;
		if(!map.Find(x, y, kUp))
		{
			MyDebugBreak();
			x = 4;
			y = 4;
		}
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
			case kSmiley:
			case kBig:
			case kGen1:
			case kGen2:
			case kGen3:
				map.Set(x, y, kSpace);
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
	static const int kC = 64;
	static const int kD = 128;
	BYTE buttons;	// bit set if button is currently pressed down
	BYTE strobe;	// bit set if button is newly pressed down
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

		// Setup our texture. Using textures introduces the texture stage states,
		// which govern how textures get blended together (in the case of multiple
		// textures) and lighting information. In this case, we are modulating
		// (blending) our texture with the diffuse color of the vertices.
		static bool firstTime = true;
		if(firstTime)
		{
			firstTime = false;
			g_pd3dDevice->SetTexture( 0, g_pTexture );
			g_pd3dDevice->SetTextureStageState( 0, D3DTSS_COLOROP,   D3DTOP_SELECTARG1 );
			g_pd3dDevice->SetTextureStageState( 0, D3DTSS_COLORARG1, D3DTA_TEXTURE );
			g_pd3dDevice->SetTextureStageState( 0, D3DTSS_COLORARG2, D3DTA_DIFFUSE );
			g_pd3dDevice->SetTextureStageState( 0, D3DTSS_ALPHAOP,   D3DTOP_DISABLE );
		}

		// Render the vertex buffer contents
		g_pd3dDevice->SetStreamSource( 0, g_pVB, 0, sizeof(CUSTOMVERTEX) );
		g_pd3dDevice->SetFVF( D3DFVF_CUSTOMVERTEX );
		g_pd3dDevice->DrawPrimitive( D3DPT_TRIANGLELIST, 0, numTris );
	}

	DWORD DrawToTexture(Map& map, CUSTOMVERTEX* pV, DWORD numV, float cogX, float cogY)
	{
		const float CellSize = 16.0f;
		const float uTexelSize = 1.0f / 256.0f;
		const float vTexelSize = 1.0f / 32.0f;
		const DWORD uChars = 16;
		const DWORD vChars = 2;
		const float uScale = 1.0f / uChars;
		const float vScale = 1.0f / vChars;
		const float uBase = 0.0f;
		const float vBase = 1.0f;

		CUSTOMVERTEX* pTri = pV;

		DWORD startX;
		DWORD endX;
		DWORD startY;
		DWORD endY;
		map.GetActive(cogX, cogY, startX, startY, endX, endY);

		const float xBase = -cogX * 16.f - 0.5f;
		const float yBase = -cogY * 16.f - 0.5f;

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
				pTri->rhw = 1.0f;
				pTri->tu = uLow;
				pTri->tv = vLow;

				pTri++;

				pTri->x = xHigh;
				pTri->y = yLow;
				pTri->z = 0.f;
				pTri->rhw = 1.0f;
				pTri->tu = uHigh;
				pTri->tv = vLow;

				pTri++;

				pTri->x = xLow;
				pTri->y = yHigh;
				pTri->z = 0.f;
				pTri->rhw = 1.0f;
				pTri->tu = uLow;
				pTri->tv = vHigh;

				// Second triangle
				pTri++;

				pTri->x = xLow;
				pTri->y = yHigh;
				pTri->z = 0.f;
				pTri->rhw = 1.0f;
				pTri->tu = uLow;
				pTri->tv = vHigh;

				pTri++;

				pTri->x = xHigh;
				pTri->y = yLow;
				pTri->z = 0.f;
				pTri->rhw = 1.0f;
				pTri->tu = uHigh;
				pTri->tv = vLow;

				pTri++;

				pTri->x = xHigh;
				pTri->y = yHigh;
				pTri->z = 0.f;
				pTri->rhw = 1.0f;
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

	void HandleEvent(bool down, UCHAR key)
	{
		keyboard.HandleEvent(down, key);
	}

	void TranslateKeysToPads()
	{
		struct PadMapEntry {
			UCHAR vkcode;
			BYTE pad;
			BYTE mask;
		};
		PadMapEntry map[] = {
			// ASDW
			{'A', 0, GamePad::kLeft},
			{'S', 0, GamePad::kDown},
			{'D', 0, GamePad::kRight},
			{'W', 0, GamePad::kUp},
			{VK_SPACE, 0, GamePad::kA},
			{'1', 0, GamePad::kB},
			{VK_F1, 0, GamePad::kC},

			{VK_F11, 0, GamePad::kD}, // For development go down to next level

			// Number pad
			{VK_NUMPAD4, 1, GamePad::kLeft},
			{VK_NUMPAD5, 1, GamePad::kDown},
			{VK_NUMPAD6, 1, GamePad::kRight},
			{VK_NUMPAD8, 1, GamePad::kUp},
			{VK_NUMPAD0, 1, GamePad::kA},
			{'2', 1, GamePad::kB},
			{VK_F2, 1, GamePad::kC},
			{0, 0, 0}
		};

		// Reset all pads
		for(int i = 0; i < World::PlayerCount; i++)
		{
			gamepad[i].strobe = gamepad[i].buttons; // Remember old state
			gamepad[i].buttons = 0;
		}
		for(PadMapEntry* pE = map; pE->vkcode != 0; pE++)
		{
			if(keyboard.data[pE->vkcode])
			{
				gamepad[pE->pad].buttons |= pE->mask;
			}
		}
		// calculate strobe
		for(int i = 0; i < World::PlayerCount; i++)
		{
			gamepad[i].strobe = gamepad[i].buttons & ~ gamepad[i].strobe;
		}
	}

	void Step()
	{
		world.Update();
		TranslateKeysToPads();
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
			if(pPad->strobe & GamePad::kB)
			{
				world.EatFood(i);
			}
			if(pPad->strobe & GamePad::kC)
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
// Name: InitD3D()
// Desc: Initializes Direct3D
//-----------------------------------------------------------------------------
HRESULT InitD3D( HWND hWnd )
{
    // Create the D3D object.
    if( NULL == ( g_pD3D = Direct3DCreate9( D3D_SDK_VERSION ) ) )
        return E_FAIL;

    // Set up the structure used to create the D3DDevice. Since we are now
    // using more complex geometry, we will create a device with a zbuffer.
    D3DPRESENT_PARAMETERS d3dpp;
    ZeroMemory( &d3dpp, sizeof(d3dpp) );
    d3dpp.Windowed = TRUE;
    d3dpp.SwapEffect = D3DSWAPEFFECT_DISCARD;
    d3dpp.BackBufferFormat = D3DFMT_UNKNOWN;
    d3dpp.EnableAutoDepthStencil = TRUE;
    d3dpp.AutoDepthStencilFormat = D3DFMT_D16;

    // Create the D3DDevice
    if( FAILED( g_pD3D->CreateDevice( D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, hWnd,
                                      D3DCREATE_SOFTWARE_VERTEXPROCESSING,
                                      &d3dpp, &g_pd3dDevice ) ) )
    {
        return E_FAIL;
    }

    // Turn off culling
    g_pd3dDevice->SetRenderState( D3DRS_CULLMODE, D3DCULL_NONE );

    // Turn off D3D lighting
    g_pd3dDevice->SetRenderState( D3DRS_LIGHTING, FALSE );

    // Turn on the zbuffer
    g_pd3dDevice->SetRenderState( D3DRS_ZENABLE, TRUE );

    return S_OK;
}

//-----------------------------------------------------------------------------
// Name: InitGeometry()
// Desc: Create the textures and vertex buffers
//-----------------------------------------------------------------------------
HRESULT InitGeometry()
{
    // Use D3DX to create a texture from a file based image
    if( FAILED( D3DXCreateTextureFromFile( g_pd3dDevice, "Dandy.bmp", &g_pTexture ) ) )
    {
        // If texture is not in current folder, try parent folder
        if( FAILED( D3DXCreateTextureFromFile( g_pd3dDevice, "..\\Dandy.bmp", &g_pTexture ) ) )
        {
            MessageBox(NULL, "Could not find Dandy.bmp", "Dandy.exe", MB_OK);
            return E_FAIL;
        }
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


//-----------------------------------------------------------------------------
// Name: Cleanup()
// Desc: Releases all previously initialized objects
//-----------------------------------------------------------------------------
VOID Cleanup()
{
    if( g_pTexture != NULL )
        g_pTexture->Release();

    if( g_pVB != NULL )
        g_pVB->Release();

    if( g_pd3dDevice != NULL )
        g_pd3dDevice->Release();

    if( g_pD3D != NULL )
        g_pD3D->Release();
}


//-----------------------------------------------------------------------------
// Name: Render()
// Desc: Draws the scene
//-----------------------------------------------------------------------------
VOID Render()
{
    // Clear the backbuffer and the zbuffer
    g_pd3dDevice->Clear( 0, NULL, D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,
                         D3DCOLOR_XRGB(0,0,255), 1.0f, 0 );

    // Begin the scene
    if( SUCCEEDED( g_pd3dDevice->BeginScene() ) )
    {
		gGame.Render();
        // End the scene
        g_pd3dDevice->EndScene();
    }

    // Present the backbuffer contents to the display
    g_pd3dDevice->Present( NULL, NULL, NULL, NULL );
}




//-----------------------------------------------------------------------------
// Name: MsgProc()
// Desc: The window's message handler
//-----------------------------------------------------------------------------
LRESULT WINAPI MsgProc( HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam )
{
    switch( msg )
    {
	case WM_KEYDOWN:
		gGame.HandleEvent(true, (BYTE) wParam);
		return 0;
	case WM_KEYUP:
		gGame.HandleEvent(false, (BYTE) wParam);
		return 0;
    case WM_DESTROY:
        Cleanup();
        PostQuitMessage( 0 );
        return 0;
    }

    return DefWindowProc( hWnd, msg, wParam, lParam );
}


//-----------------------------------------------------------------------------
// Name: WinMain()
// Desc: The application's entry point
//-----------------------------------------------------------------------------
INT WINAPI WinMain( HINSTANCE hInst, HINSTANCE, LPSTR, INT )
{
    // Register the window class
    WNDCLASSEX wc = { sizeof(WNDCLASSEX), CS_CLASSDC, MsgProc, 0L, 0L,
                      GetModuleHandle(NULL), NULL, NULL, NULL, NULL,
                      "Dandy", NULL };
    RegisterClassEx( &wc );

    // Create the application's window
    HWND hWnd = CreateWindow( "Dandy", "Dandy Dungeon",
		WS_OVERLAPPEDWINDOW, 100, 100, 16*20 + 6, 16*10 + 34,
                              GetDesktopWindow(), NULL, wc.hInstance, NULL );

    // Initialize Direct3D
    if( SUCCEEDED( InitD3D( hWnd ) ) )
    {
		gGame.Start();
        // Create the scene geometry
        if( SUCCEEDED( InitGeometry() ) )
        {
            // Show the window
            ShowWindow( hWnd, SW_SHOWDEFAULT );
            UpdateWindow( hWnd );

            // Enter the message loop
            MSG msg;
            ZeroMemory( &msg, sizeof(msg) );
            while( msg.message!=WM_QUIT )
            {
                if( PeekMessage( &msg, NULL, 0U, 0U, PM_REMOVE ) )
                {
                    TranslateMessage( &msg );
                    DispatchMessage( &msg );
                }
                else
				{
					gGame.Step();
                    Render();
				}
            }
        }
    }

    UnregisterClass( "Dandy", wc.hInstance );
    return 0;
}