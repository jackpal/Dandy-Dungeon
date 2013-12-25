//-----------------------------------------------------------------------------
// File: Dandy.cs
using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using Microsoft.DirectX;
using Microsoft.DirectX.Direct3D;
using Direct3D=Microsoft.DirectX.Direct3D;

namespace Dandy
{
// The game goes here

	class Debug
	{
		public static 
			void MyDebugBreak()
		{
			// DebugBreak();
		}

		public static void MyAssert(bool test)
		{
			if(!test)
			{
				MyDebugBreak();
			}
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
	public Map()
		{
			Init();
		}

	public MapData Get(uint x, uint y)
		{
			MapData b = MapData.kSpace;
			if(x >= 0 && x < Width && y >= 0 && y < Height)
			{
				b = (MapData) Cell[x + y*Width];
			}
			else
			{
				Debug.MyDebugBreak();
			}
			return b;
		}

	public MapData Get(uint x, uint y, Direction dir)
		{
			MapData b = MapData.kSpace;
			if(x >= 0 && x < Width && y >= 0 && y < Height)
			{
				b = (MapData) Cell[x + y*Width];
			}
			else
			{
				Debug.MyDebugBreak();
			}
			return b;
		}

	public void Set(uint x, uint y, MapData v)
		{
			if(x >= 0 && x < Width && y >= 0 && y < Height && v <= MapData.kPlayer3)
			{
				Cell[x + y*Width] = v;
			}
			else
			{
				Debug.MyDebugBreak();
			}
		}

	public bool Find(ref byte rx, ref byte ry, MapData v)
		{
			for(int y = 0; y < Height; y++)
			{
				for(int x = 0; x < Width; x++)
				{
					if(Cell[x + y * Width] == v)
					{
						rx = (byte) x;
						ry = (byte) y;
						return true;
					}
				}
			}
			return false;
		}

	public void OpenLock(uint x, uint y)
		{
			// Flood fill from this coord
			if(Cell[x + y * Width] == MapData.kLock)
			{
				Cell[x + y * Width] = MapData.kSpace;
				for(int dy = -1;dy <= 1; dy++)
					for(int dx = -1;dx <= 1; dx++)
						if(dx != 0 || dy != 0)
							OpenLock((uint) (x + dx), (uint) (y + dy));
			}
		}

	public void Init()
		{
			for(uint y = 0; y < Height; y++)
			{
				for(uint x = 0; x < Width; x++)
				{
					MapData b = MapData.kSpace;
					if(y == 0 || y == Height-1 || x == 0 || x == Width - 1)
					{
						b = MapData.kWall;
					}
					else if ( x == 2 && y == 2)
					{
						b = MapData.kUp;
					}
					else if ( x == 10 && y == 10 )
					{
						b = MapData.kDown;
					}
					Cell[y*Width+x] = b;
				}
			}
		}

		public bool LoadLevel(uint index)
		{
			String fileName = "levels\\level." + (char) (index + 'a');
			try 
			{
				LoadLevel2(fileName);
			}
			catch
			{
				fileName = "..\\..\\levels\\level." + (char) (index + 'a');
				try 
				{
					LoadLevel2(fileName);
				}
				catch
				{
					return false;
				}
			}
			return true;
		}

		private void LoadLevel2(string fileName)
		{
			using(FileStream s = new FileStream(fileName, FileMode.Open))
			{
				for(int y = 0; y < Height; y++)
				{
					for(int x = 0; x < Width; x += 2)
					{
						int inb = s.ReadByte();
						if(inb < 0)
						{
							throw new System.Exception("Unexpected EOF");
						}
						Cell[y*Width+x] = (MapData) (inb & 0xf);
						Cell[y*Width+x+1] = (MapData) ((inb >> 4) & 0xf);
					}
				}
			}
		}

		public void GetActive(ref float x, ref float y, ref uint left, ref uint top, ref uint right, ref uint bottom)
		{
			GetActive1(ref x, ref left, ref right, Map.Width, Map.ViewWidth);
			GetActive1(ref y, ref top, ref bottom, Map.Height, Map.ViewHeight);
		}

		private void GetActive1(ref float x, ref uint left, ref uint right, uint width, uint viewWidth)
		{
			x -= (viewWidth / 2.0f);
			x = Math.Max(x, 0.0f);
			x = Math.Min(x, width - viewWidth);
			left = (uint) x;
			right = Math.Min(left + viewWidth + 1, width);
		}

		public const uint Width = 60;
		public const uint Height = 30;
		public const uint NumCells = Width * Height;
		private MapData[] Cell = new MapData[NumCells];

		public const uint ViewWidth = 20;
		public const uint ViewHeight = 10;
	}

class Arrow
{
public Arrow()
	{
		alive = false;
		x = 0;
		y = 0;
		dir = Direction.kDirNone;
	}

	public static bool CanGo(MapData d)
	{
		return d == MapData.kSpace;
	}

	public static bool CanHit(MapData d)
	{
		return d >= MapData.kBomb && d <= MapData.kGen3;
	}

	public bool alive;
	public byte x;
	public byte y;
	public Direction dir;
}

enum PlayerState
{
	kNormal,
	kInWarp
}

class Player
{
	public Player()
	{
		Init();
	}

	public void Init()
	{
		x = 0;
		y = 0;
		state = PlayerState.kNormal;
		health = kHealthMax;
		food = 0;
		bombs = 0;
		keys = 0;
		score = 0;
		dir = Direction.kDirNone;
		lastMoveTime = DateTime.Now;
	}

	public bool IsAlive()
	{
		return health > 0;
	}

	public bool IsVisible()
	{
		return health > 0 && state == PlayerState.kNormal;
	}

	public void EatFood()
	{
		if(food > 0 && health < kHealthMax)
		{
			--food;
			health = kHealthMax;
		}
	}

	public const int kHealthMax = 9;
	public byte x;
	public byte y;
	public byte health;
	public byte food;
	public byte keys;
	public byte bombs;
	public uint score;
	public PlayerState state;
	public DateTime lastMoveTime;
	public Direction dir;
	public Arrow arrow = new Arrow();
};

class World
{
	public World()
	{
		for(uint i = 0; i < player.Length; i++)
		{
			player[i] = new Player();
		}
	}

	public void Init()
	{
		map.Init();
		numPlayers = 2;
		for(uint i = 0; i < numPlayers; i++)
		{
			player[i].Init();
		}
		gridStep = 0;
	}

	static readonly DateTime dtStart = DateTime.Now;

	public void Update()
	{
		time = DateTime.Now;

		for(uint i = 0; i < numPlayers; i++)
		{
			DoArrowMove(player[i], false);
		}

		DoMonsters();
	}

	public bool IsGameOver()
	{
		for(uint i = 0; i < numPlayers; i++)
		{
			if(player[i].IsAlive())
			{
				return false;
			}
		}
		return true;
	}

	public void DoMonsters()
	{
		float cogX = 0.0f;
		float cogY = 0.0f;
		uint startX = 0;
		uint endX = 0;
		uint startY = 0;
		uint endY = 0;
		GetCOG(ref cogX, ref cogY);
		map.GetActive(ref cogX, ref cogY, ref startX, ref startY, ref endX, ref endY);

		// update in a grid pattern
		++gridStep;
		uint gridXOffset = gridStep % 3;
		uint gridYOffset = (gridStep / 3) % 3;
		for(uint y = startY + gridYOffset; y < endY; y += 3)
		{
			for(uint x = startX + gridXOffset; x < endX; x += 3)
			{
				MapData d = map.Get(x, y);
				if(d >= MapData.kGhost && d <= MapData.kBig)
				{
					// Move towards nearest player
					Direction dir = GetDirectionOfNearestPlayer(x, y);
					if(dir != Direction.kDirNone)
					{
						byte mx = 0;
						byte my = 0;
						bool canMove = false;
						MapData d2 = MapData.kSpace;
						for(int test = 0; test < 3; test++)
						{
							mx = (byte) x;
							my = (byte) y;
							MoveCoords(ref mx, ref my, (Direction) (((int) dir + kTestDelta[test]) & 7));
							d2 = map.Get(mx, my);
							if(d2 == MapData.kSpace || d2 >= MapData.kPlayer0 && d2 <= MapData.kPlayer3)
							{
								canMove = true;
								break;
							}
						}
						if(canMove)
						{
							map.Set(x, y, MapData.kSpace);
							if(d2 >= MapData.kPlayer0 && d2 <= MapData.kPlayer3)
							{
								Player p = player[d2 - MapData.kPlayer0];
								int monsterHit = d - MapData.kGhost + 1;
								if(p.health > monsterHit)
								{
									p.health = (byte) (p.health - monsterHit);
								}
								else
								{
									p.health = 0;
									MapData remains = MapData.kSpace;
									if(p.keys > 0)
									{
										--p.keys;
										remains = MapData.kKey;
									}
									map.Set(p.x, p.y, remains);
								}
							}
							else
							{
								map.Set(mx, my, d);
							}
						}
					}
				}
				else if(d >= MapData.kGen1 && d <= MapData.kGen3)
				{
					// Random generator
					if(getRandom(10) < 3)
					{
						byte gx = (byte) x;
						byte gy = (byte) y;
						MoveCoords(ref gx, ref gy, (Direction)( getRandom(4) * 2));
						if(map.Get(gx,gy) == MapData.kSpace)
						{
							map.Set(gx, gy, (MapData) MapData.kGhost + (d - MapData.kGen1));
						}
					}
				}
			}
		}
	}
	
	private static uint gridStep;

	private static readonly int[] kTestDelta = new int[]{0,-1,1};

	private Random random = new Random();

	public uint getRandom(uint range)
	{
		return (uint) random.Next((int) range);
	}

	public Direction GetDirectionOfNearestPlayer(uint x, uint y)
	{
		uint bestX = 0;
		uint bestY = 0;
		uint bestDistance = 10000;
		for(uint i = 0; i < numPlayers; i++)
		{
			Player pP = player[i];
			if(pP.IsVisible())
			{
				uint distance = (uint) (Math.Abs((int) pP.x - (int) x) + Math.Abs((int) pP.y - (int) y));
				if(distance < bestDistance)
				{
					bestDistance = distance;
					bestX = pP.x;
					bestY = pP.y;
				}
			}
		}
		if(bestDistance == 10000)
		{
			return Direction.kDirNone;
		}
		int dx = (int) (bestX - x);
		int dy = (int) (bestY - y);
		byte bitField = 0;
		if(dy > 0) bitField |= 8;
		else if(dy < 0) bitField |= 4;
		if(dx > 0) bitField |= 2;
		else if(dx < 0) bitField |= 1;

		//     7 0 1
		//     6 + 2 
		//     5 4 3 


		return (Direction) kDirTable[bitField];
	}

	private static readonly byte[] kDirTable =
		new byte[]{
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

	public void GetCOG(ref float x, ref float y)
	{
		x = 0.0f;
		y = 0.0f;
		int liveCount = 0;
		for(uint i = 0; i < numPlayers; i++)
		{
			Player pP = player[i];
			if(pP.IsVisible())
			{
				x += pP.x;
				y += pP.y;
				++liveCount;
			}
		}
		if(liveCount > 0)
		{
			x /= liveCount;
			y /= liveCount;
		}
	}

	public void LoadLevel(uint index)
	{
		if(map.LoadLevel(index))
		{
			level = (byte) index;
		}
		else
		{
			level = 0;
			map.LoadLevel(0);
		}
		SetPlayerPositions();
	}

	public void ChangeLevel(int delta)
	{
		uint newLevel = (uint) Math.Min(26, level + delta);
		LoadLevel(newLevel);
	}

	public void SetPlayerPositions()
	{
		byte x = 0;
		byte y = 0;
		if(!map.Find(ref x, ref y, MapData.kUp))
		{
			Debug.MyDebugBreak();
			x = 4;
			y = 4;
		}
		for(uint i = 0; i < numPlayers; i++)
		{
			Player p = player[i];
			if(p.IsAlive())
			{
				byte px = x;
				byte py = y;
				MoveCoords(ref px, ref py, (Direction)(i * 2));
				PlaceInWorld(i, px, py);
			}
		}
	}

	public void PlaceInWorld(uint index, uint x, uint y)
	{
		Player p = player[index];
		Debug.MyAssert(p.IsAlive());
		p.x = (byte) x;
		p.y = (byte) y;
		p.dir = (Direction) (index * 2);
		map.Set(p.x, p.y, (MapData) ((int) MapData.kPlayer0 + index));
		p.state = PlayerState.kNormal;
		p.arrow.alive = false;
	}

	public void Move(uint stick, Direction dir)
	{
		if(stick < 4 && dir < (Direction) 8)
		{
			if(stick < numPlayers)
			{
				Player p = player[stick];
				p.dir = dir;
				TimeSpan delta = time - p.lastMoveTime;
				if(p.IsVisible() && delta.Milliseconds >= kMsPerMove)
				{
					p.lastMoveTime = time;
					byte x = p.x;
					byte y = p.y;
					MoveCoords(ref x, ref y, dir);
					MapData d = map.Get(x,y);
					bool bMove = false;
					switch(d)
					{
					case MapData.kSpace:
						bMove = true;
						break;
					case MapData.kLock:
						if(p.keys > 0)
						{
							--p.keys;
							map.OpenLock(x, y);
							bMove = true;
						}
						break;
					case MapData.kKey:
						++p.keys;
						bMove = true;
						break;
					case MapData.kFood:
						++p.food;
						bMove = true;
						break;
					case MapData.kMoney:
						p.score += 10;
						bMove = true;
						break;
					case MapData.kBomb:
						++p.bombs;
						bMove = true;
						break;
					case MapData.kDown:
						{
							p.state = PlayerState.kInWarp;
							map.Set(p.x, p.y, MapData.kSpace);
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
						map.Set(p.x, p.y, MapData.kSpace);
						map.Set(x, y, (MapData) ((int) MapData.kPlayer0 + stick));
						p.x = x;
						p.y = y;
					}
				}

			}
		}
		else
		{
			Debug.MyDebugBreak();
		}
	}

	public bool IsPartyInWarp()
	{
		// At least one player in warp, and no players visible
		bool atLeastOneWarp = false;
		bool atLeastOneVisible = false;
		for(uint i = 0; i < numPlayers;i++)
		{
			if(player[i].IsVisible())
			{
				atLeastOneVisible = true;
				break;
			}
			if(player[i].IsAlive() && player[i].state == PlayerState.kInWarp)
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

	public void EatFood(uint index)
	{
		if(index < numPlayers)
		{
			Player p = player[index];
			if(p.IsVisible())
			{
				p.EatFood();
			}
		}
	}

	public void Fire(uint index)
	{
		if(index < numPlayers)
		{
			Player p = player[index];
			if(!p.arrow.alive)
			{
				p.arrow.alive = true;
				p.arrow.x = p.x;
				p.arrow.y = p.y;
				p.arrow.dir = p.dir;
				DoArrowMove(p, true);
			}
		}
		else
		{
			Debug.MyDebugBreak();
		}
	}

	public void DoArrowMove(Player p, bool isFirstMove)
	{
		if(!p.arrow.alive)
		{
			return;
		}
		byte x = p.arrow.x;
		byte y = p.arrow.y;
		if(!isFirstMove)
		{
			map.Set(x, y, MapData.kSpace);
		}
		MoveCoords(ref x, ref y, p.arrow.dir);
		MapData d = map.Get(x,y);
		if(Arrow.CanHit(d))
		{
			switch(d)
			{
			case MapData.kBomb:
				DoSmartBomb();
				map.Set(x, y, MapData.kSpace);
				break;
			case MapData.kGhost: goto common;
			case MapData.kSmiley: goto common;
			case MapData.kBig: goto common;
			case MapData.kGen1: goto common;
			case MapData.kGen2: goto common;
			case MapData.kGen3:
					common:
				map.Set(x, y, MapData.kSpace);
				break;
			case MapData.kHeart:
				{
					bool foundPlayer = false;
					for(uint i = 0; i < numPlayers; i++)
					{
						Player p2 = player[i];
						if(!p2.IsAlive())
						{
							p2.health = 9;
							p2.state = PlayerState.kNormal;
							PlaceInWorld(i, x, y);
							foundPlayer = true;
							break;
						}
					}
					if(!foundPlayer)
					{
						map.Set(x, y, MapData.kBig);
					}
				}
				break;
			default:
				Debug.MyDebugBreak();
				break;
			}
			p.arrow.alive = false;
		}
		else if(Arrow.CanGo(d))
		{
			p.arrow.x = x;
			p.arrow.y = y;
			int rotatedDir = ((int)(p.arrow.dir + 3) & 7); // Because font is screwed up
			map.Set(x, y, (MapData) (MapData.kArrow0 + rotatedDir));
		}
		else
		{
			p.arrow.alive = false;
		}
	}

	public void UseSmartBomb(uint index)
	{
		if(index < numPlayers)
		{
			Player p = player[index];
			if(p.bombs > 0)
			{
				--p.bombs;
				DoSmartBomb();
			}
		}
		else
		{
			Debug.MyDebugBreak();
		}
	}

	public void DoSmartBomb()
	{
		float cogX = 0.0f;
		float cogY = 0.0f;
		uint startX = 0;
		uint endX = 0;
		uint startY = 0;
		uint endY = 0;
		GetCOG(ref cogX, ref cogY);
		map.GetActive(ref cogX, ref cogY, ref startX, ref startY, ref endX, ref endY);
		for(uint y = startX; y < endY; y++)
		{
			for(uint x = startX; x < endX; x++)
			{
				MapData d = map.Get(x, y);
				if(d >= MapData.kGhost && d <= MapData.kBig || d >= MapData.kGen1 && d <= MapData.kGen3)
				{
					map.Set(x, y, MapData.kSpace);
				}
			}
		}
	}

	public static void MoveCoords(ref byte x, ref byte y, Direction direction)
	{
		if((int) direction < 8)
		{
			// Up is zero, clockwise
			x = (byte) (x + kOffsets[(int) direction][0]);
			y = (byte) (y + kOffsets[(int) direction][1]);
		}
		else
		{
			Debug.MyDebugBreak();
		}
	}

	private static readonly sbyte[][] kOffsets = new sbyte[][]
	{
		new sbyte[]{0,-1},new sbyte[]{1,-1},new sbyte[]{1,0},new sbyte[]{1,1},new sbyte[]{0,1},new sbyte[]{-1,1},new sbyte[]{-1,0},new sbyte[]{-1,-1}
	};

	public Map map = new Map();
	public byte level;
	public const int PlayerCount = 4;
	public Player[] player = new Player[PlayerCount];
	public uint numPlayers;
	public DateTime time;

	public const uint kMsPerMove = (1000 / 60) * 3;
};

class GamePad
{
	public GamePad()
	{
		buttons = 0;
		strobe = 0;
	}

	public const int kUp = 1; // Mask for up button
	public const int kDown = 2;
	public const int kLeft = 4;
	public const int kRight = 8;
	public const int kA = 16;
	public const int kB = 32;
	public const int kC = 64;
	public const int kD = 128;
	public byte buttons;	// bit set if button is currently pressed down
	public byte strobe;	// bit set if button is newly pressed down
};

class Keyboard
{
	public Keyboard()
	{
	}
	public void HandleEvent(bool down, Keys key)
	{
		data[(int) key] = down;
	}
	public const int KeySize = 256;
	public bool[] data = new bool[KeySize];
};

class View
{
public View()
	{
	}

	public void Render(World world, Device device, // Our rendering device
		VertexBuffer vb,
		Texture texture)
	{
		// Fill the vertex buffer. We are setting the tu and tv texture
		// coordinates, which range from 0.0 to 1.0
		CustomVertex.TransformedTextured[] verts = (CustomVertex.TransformedTextured[])vb.Lock(0,0); // Lock the buffer (which will return our structs)

		float x = 0;
		float y = 0;
		world.GetCOG(ref x, ref y);

		uint numTris = DrawToTexture(world.map, verts, x, y);
		vb.Unlock();

		// Setup our texture. Using textures introduces the texture stage states,
		// which govern how textures get blended together (in the case of multiple
		// textures) and lighting information. In this case, we are modulating
		// (blending) our texture with the diffuse color of the vertices.
		if(firstTime)
		{
			firstTime = false;

			// Setup our texture. Using textures introduces the texture stage states,
			// which govern how textures get blended together (in the case of multiple
			// textures) and lighting information. In this case, we are modulating
			// (blending) our texture with the diffuse color of the vertices.
			device.SetTexture(0,texture);
			device.TextureState[0].ColorOperation = TextureOperation.SelectArg1;
			device.TextureState[0].ColorArgument1 = TextureArgument.TextureColor;
			device.TextureState[0].ColorArgument2 = TextureArgument.Diffuse;
			device.TextureState[0].AlphaOperation = TextureOperation.Disable;
	
			device.SetStreamSource(0, vb, 0);
			device.VertexFormat = CustomVertex.TransformedTextured.Format;
		}

		// Render the vertex buffer contents
		device.DrawPrimitives(PrimitiveType.TriangleList, 0, (int) numTris);
	}

	public uint DrawToTexture(Map map, CustomVertex.TransformedTextured[] pV, float cogX, float cogY)
	{
		const float CellSize = 16.0f;
		const uint uChars = 16;
		const uint vChars = 2;
		const float uScale = 1.0f / uChars;
		const float vScale = 1.0f / vChars;

		uint startX = 0;
		uint endX = 0;
		uint startY = 0;
		uint endY = 0;
		map.GetActive(ref cogX, ref cogY, ref startX, ref startY, ref endX, ref endY);

		float xBase = -cogX * 16.0f - 0.5f;
		float yBase = -cogY * 16.0f - 0.5f;

		uint dwNumTris = 0;
		uint index = 0;
		for(uint x = startX; x < endX; x++)
		{
			for(uint y = startY; y < endY; y ++)
			{
				byte b = (byte) map.Get(x, y);
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
				pV[index].X = xLow;
				pV[index].Y = yLow;
				pV[index].Z = 0.0f;
				pV[index].Rhw = 1.0f;
				pV[index].Tu = uLow;
				pV[index].Tv = vLow;

				index++;

				pV[index].X = xHigh;
				pV[index].Y = yLow;
				pV[index].Z = 0.0f;
				pV[index].Rhw = 1.0f;
				pV[index].Tu = uHigh;
				pV[index].Tv = vLow;

				index++;

				pV[index].X = xLow;
				pV[index].Y = yHigh;
				pV[index].Z = 0.0f;
				pV[index].Rhw = 1.0f;
				pV[index].Tu = uLow;
				pV[index].Tv = vHigh;

				// Second triangle
				index++;

				pV[index].X = xLow;
				pV[index].Y = yHigh;
				pV[index].Z = 0.0f;
				pV[index].Rhw = 1.0f;
				pV[index].Tu = uLow;
				pV[index].Tv = vHigh;

				index++;

				pV[index].X = xHigh;
				pV[index].Y = yLow;
				pV[index].Z = 0.0f;
				pV[index].Rhw = 1.0f;
				pV[index].Tu = uHigh;
				pV[index].Tv = vLow;

				index++;

				pV[index].X = xHigh;
				pV[index].Y = yHigh;
				pV[index].Z = 0.0f;
				pV[index].Rhw = 1.0f;
				pV[index].Tu = uHigh;
				pV[index].Tv = vHigh;

				index++;

				dwNumTris += 2;
			}
		}
		return dwNumTris;
	}
	private static bool firstTime = true;
	public const uint kNumVerts = Map.NumCells * 6;
};

class Game
{
	public Game()
	{
		for(int i = 0; i < gamepad.Length; ++i)
		{
			gamepad[i] = new GamePad();
		}
		Init();
	}

	public void Init()
	{
		world.Init();
	}

	public void Start()
	{
		Init();
		world.LoadLevel(0);
	}
	public void Render(Device device, VertexBuffer vertexBuffer, Texture texture)
	{
		view.Render(world, device, vertexBuffer, texture);
	}

	public void HandleEvent(bool down, Keys key)
	{
		keyboard.HandleEvent(down, key);
	}

	struct PadMapEntry 
	{
		public PadMapEntry(Keys vkcode, byte pad, byte mask)
		{
			this.vkcode = vkcode;
			this.pad = pad;
			this.mask = mask;
		}
		public Keys vkcode;
		public byte pad;
		public byte mask;
	};

	static readonly PadMapEntry[] map = 
		new PadMapEntry[]{
			// ASDW
			new PadMapEntry(Keys.A, 0, GamePad.kLeft),
			new PadMapEntry(Keys.S, 0, GamePad.kDown),
			new PadMapEntry(Keys.D, 0, GamePad.kRight),
			new PadMapEntry(Keys.W, 0, GamePad.kUp),
			new PadMapEntry(Keys.Space, 0, GamePad.kA),
			new PadMapEntry(Keys.D1, 0, GamePad.kB),
			new PadMapEntry(Keys.F1, 0, GamePad.kC),

			new PadMapEntry(Keys.F11, 0, GamePad.kD), // For development go down to next level

				// Number pad
			new PadMapEntry(Keys.NumPad4, 1, GamePad.kLeft),
			new PadMapEntry(Keys.NumPad5, 1, GamePad.kDown),
			new PadMapEntry(Keys.NumPad6, 1, GamePad.kRight),
			new PadMapEntry(Keys.NumPad8, 1, GamePad.kUp),
			new PadMapEntry(Keys.NumPad0, 1, GamePad.kA),
			new PadMapEntry(Keys.D2, 1, GamePad.kB),
			new PadMapEntry(Keys.F2, 1, GamePad.kC),
			new PadMapEntry(0, 0, 0)
		};
	public void TranslateKeysToPads()
	{
		// Reset all pads
		for(int i = 0; i < World.PlayerCount; i++)
		{
			gamepad[i].strobe = gamepad[i].buttons; // Remember old state
			gamepad[i].buttons = 0;
		}
		foreach(PadMapEntry pE in map)
		{
			if(keyboard.data[(int) pE.vkcode])
			{
				gamepad[pE.pad].buttons |= pE.mask;
			}
		}
		// calculate strobe
		for(int i = 0; i < World.PlayerCount; i++)
		{
			gamepad[i].strobe = (byte) (gamepad[i].buttons & ~ gamepad[i].strobe);
		}
	}

	public void Step()
	{
		world.Update();
		TranslateKeysToPads();
		MovePlayers();
		if(world.IsGameOver())
		{
			Start();
		}
	}

	static readonly Direction[] kPadToDir =
	new Direction[]{
		// Bitfield is Right Left Down Up
		// Directions are clockwise from up == 0
		Direction.kDirNone, // 0000
		Direction.kDirUp, // 0001 
		Direction.kDirDown, // 0010
		Direction.kDirNone, // 0011 
		Direction.kDirLeft, // 0100
		Direction.kDirUpLeft, // 0101
		Direction.kDirDownLeft, // 0110
		Direction.kDirLeft, // 0111
		Direction.kDirRight, // 1000
		Direction.kDirUpRight, // 1001
		Direction.kDirDownRight, // 1010
		Direction.kDirRight, // 1011
		Direction.kDirNone, // 1100
		Direction.kDirUp, // 1101 
		Direction.kDirDown, // 1110 
		Direction.kDirNone, // 1111 
	};

	void MovePlayers()
	{
		for(uint i = 0; i < world.numPlayers; i++)
		{
			GamePad pPad = gamepad[i];
			Direction dir = kPadToDir[0xf & pPad.buttons];
			if(dir != Direction.kDirNone)
			{
				world.Move(i, dir);
			}

			// Handle strobes
			if((pPad.buttons & GamePad.kA) != 0)
			{
				world.Fire(i);
			}
			if((pPad.strobe & GamePad.kB) != 0)
			{
				world.EatFood(i);
			}
			if((pPad.strobe & GamePad.kC) != 0)
			{
				world.UseSmartBomb(i);
			}

			if((pPad.strobe & GamePad.kD) != 0)
			{
				if(i == 0)
				{
					world.ChangeLevel(1); // For debugging
				}
			}
		}
	}

	World world = new World();
	GamePad[] gamepad = new GamePad[World.PlayerCount];
	Keyboard keyboard = new Keyboard();
	View view = new View();
};

	public class Dandy : Form
	{
		// Our global variables for this project
		Device device = null; // Our rendering device
		VertexBuffer vertexBuffer = null;
		Texture texture = null;
		PresentParameters presentParams = new PresentParameters();
		bool pause = false;


		public Dandy()
		{
			// Set the initial size of our form
			this.ClientSize = new System.Drawing.Size(16*20, 16*10);
			// And its caption
			this.Text = "Dandy Dungeon C#";

			this.KeyDown += new KeyEventHandler(Dandy_KeyDown);
			this.KeyUp += new KeyEventHandler(Dandy_KeyUp);

			game.Start();
		}

		public bool InitializeGraphics()
		{
			try
			{
				presentParams.Windowed=true; // We don't want to run fullscreen
				presentParams.SwapEffect = SwapEffect.Discard; // Discard the frames 
				device = new Device(0, DeviceType.Hardware, this, CreateFlags.SoftwareVertexProcessing, presentParams); //Create a device
				device.DeviceReset += new System.EventHandler(this.OnResetDevice);
				this.OnCreateDevice(device, null);
				this.OnResetDevice(device, null);
				pause = false;

				return true;
			}
			catch (DirectXException)
			{
				// Catch any errors and return a failure
				return false;
			}
		}

		public void OnCreateDevice(object sender, EventArgs e)
		{
			Device dev = (Device)sender;
			// Now Create the VB
			vertexBuffer = new VertexBuffer(typeof(CustomVertex.TransformedTextured), (int) View.kNumVerts, dev, Usage.WriteOnly, CustomVertex.TransformedTextured.Format, Pool.Default);
			vertexBuffer.Created += new System.EventHandler(this.OnCreateVertexBuffer);
			this.OnCreateVertexBuffer(vertexBuffer, null);
		}

		public void OnResetDevice(object sender, EventArgs e)
		{
			Device dev = (Device)sender;
			// Turn off culling, so we see the front and back of the triangle
			dev.RenderState.CullMode = Cull.None;
			// Turn off D3D lighting
			dev.RenderState.Lighting = false;
			// Turn on the ZBuffer
			dev.RenderState.ZBufferEnable = true;
			// Now create our texture
			texture = TextureLoader.FromFile(dev, Application.StartupPath + @"\..\..\dandy.bmp");
		}
		public void OnCreateVertexBuffer(object sender, EventArgs e)
		{
		}

		private void Render()
		{
			if (pause)
				return;

			game.Step();
 
			//Clear the backbuffer to a blue color 
			device.Clear(ClearFlags.Target, System.Drawing.Color.Blue, 0.0f, 0);
			//Begin the scene
			device.BeginScene();
			game.Render(device, vertexBuffer, texture);
			//End the scene
			device.EndScene();
			// Update the screen
			device.Present();
		}

		protected override void OnPaint(System.Windows.Forms.PaintEventArgs e)
		{
			this.Render(); // Render on painting
		}
		protected override void OnKeyPress(System.Windows.Forms.KeyPressEventArgs e)
		{
			if ((int)(byte)e.KeyChar == (int)System.Windows.Forms.Keys.Escape)
				this.Dispose(); // Esc was pressed
		}
        protected override void OnResize(System.EventArgs e)
        {
            pause = ((this.WindowState == FormWindowState.Minimized) || !this.Visible);
        }
        
        /// <summary>
		/// The main entry point for the application.
		/// </summary>
		static void Main() 
		{
			CSScheme.Scheme.main(new String[0]);
            using (Dandy frm = new Dandy())
            {
                if (!frm.InitializeGraphics()) // Initialize Direct3D
                {
                    MessageBox.Show("Could not initialize Direct3D.  This application will exit.");
                    return;
                }
                frm.Show();

                // While the form is still valid, render and process messages
                while(frm.Created)
                {
                    frm.Render();
                    Application.DoEvents();
               }
            }
		}

		private Game game = new Game();

		private void Dandy_KeyDown(object sender, KeyEventArgs e)
		{
			game.HandleEvent(true, e.KeyCode);
		}

		private void Dandy_KeyUp(object sender, KeyEventArgs e)
		{
			game.HandleEvent(false, e.KeyCode);
		}
	}
}
