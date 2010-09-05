// BitmapFont.cs
// Bitmap Font class for XNA
// Copyright 2006 Microsoft Corp.
// Revision: 2006-Aug-30

using System;
using System.Collections.Generic;
using System.Text;
using System.Xml;

using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;

namespace XNAExtras
{
	/// <summary>
	/// Info for each glyph in the font - where to find the glyph image and 
	/// other properties
	/// </summary>
	struct GlyphInfo
	{
		public int nBitmapID;
		public int nOriginX;
		public int nOriginY;
		public int nWidth;
		public int nHeight;
		public int nAdvanceWidth;
		public int nLeftSideBearing;
	}

	/// <summary>
	/// Info for each font bitmap
	/// </summary>
	struct BitmapInfo
	{
		public string strFilename;
		public int nX, nY;
	}

	/// <summary>
	/// Bitmap font class for XNA
	/// </summary>
	public class BitmapFont
	{
		private SpriteBatch m_sb;
		private Dictionary<int, BitmapInfo> m_dictBitmapID2BitmapInfo;
		private Dictionary<int, Texture2D> m_dictBitmapID2Texture;
		private Dictionary<char, GlyphInfo> m_dictUnicode2GlyphInfo;
		private Dictionary<char, Dictionary<char, int>> m_dictKern;
		private int m_nBase = 0;
		private int m_nHeight = 0;

		/// <summary>
		/// Create a new font from the info in the specified font descriptor (XML) file
		/// </summary>
		/// <param name="strFontFilename">font file (.xml)</param>
		public BitmapFont(string strFontFilename)
		{
			m_dictBitmapID2BitmapInfo = new Dictionary<int, BitmapInfo>();
			m_dictBitmapID2Texture = new Dictionary<int, Texture2D>();

			m_dictUnicode2GlyphInfo = new Dictionary<char, GlyphInfo>();
			m_dictKern = new Dictionary<char, Dictionary<char, int>>();

			XmlDocument xd = new XmlDocument();
			xd.Load(strFontFilename);
			LoadFontXML(xd.ChildNodes);
		}
		
		/// <summary>
		/// Reset the font when the device has changed
		/// </summary>
		/// <param name="device">The new device</param>
		public void Reset(GraphicsDevice device)
		{
			m_sb = new SpriteBatch(device);
			foreach (KeyValuePair<int, BitmapInfo> kv in m_dictBitmapID2BitmapInfo)
				m_dictBitmapID2Texture[kv.Key] = Texture2D.FromFile(device, kv.Value.strFilename, kv.Value.nX, kv.Value.nY);
		}

		/// <summary>
		/// Should we kern adjacent characters?
		/// </summary>
		private bool m_fKern = true;

		/// <summary>
		/// Enable/disable kerning
		/// </summary>
		public bool KernEnable
		{
			get { return m_fKern; }
			set { m_fKern = value; }
		}

		/// <summary>
		/// Distance from top of font to the baseline
		/// </summary>
		public int Baseline
		{
			get { return m_nBase; }
		}

		/// <summary>
		/// Distance from top to bottom of the font
		/// </summary>
		public int LineHeight
		{
			get { return m_nHeight; }
		}

		/// <summary>
		/// Calculate the width of the given string.
		/// </summary>
		/// <param name="format">String format</param>
		/// <param name="args">String format arguments</param>
		/// <returns>Width (in pixels) of the string</returns>
		public int MeasureString(string format, params object[] args)
		{
			string str = string.Format(format, args);
			int nWidth = 0;
			char cLast = '\0';

			foreach (char c in str)
			{
				if (!m_dictUnicode2GlyphInfo.ContainsKey(c))
				{
					//TODO: print out undefined char glyph
					continue;
				}

				GlyphInfo ginfo = m_dictUnicode2GlyphInfo[c];

				// if kerning is enabled, get the kern adjustment for this char pair
				if (m_fKern)
				{
					nWidth += CalcKern(cLast, c);
					cLast = c;
				}

				// update the string width
				nWidth += ginfo.nAdvanceWidth;
			}

			return nWidth;
		}

		/// <summary>
		/// Current pen position
		/// </summary>
		private Vector2 m_vPen = new Vector2(0, 0);

		/// <summary>
		/// Current pen position
		/// </summary>
		public Vector2 Pen
		{
			get { return m_vPen; }
			set { m_vPen = value; }
		}

		/// <summary>
		/// Set the current pen position
		/// </summary>
		/// <param name="x">X-coord</param>
		/// <param name="y">Y-coord</param>
		public void SetPen(int x, int y)
		{
			m_vPen = new Vector2(x, y);
		}


		/// <summary>
		/// Current color used for drawing text
		/// </summary>
		Color m_color = Color.White;

		/// <summary>
		/// Current color used for drawing text
		/// </summary>
		public Color TextColor
		{
			get { return m_color; }
			set { m_color = value; }
		}


		/// <summary>
		/// Draw the given string at (x,y).
		/// The text color is inherited from the last draw command (default=White).
		/// </summary>
		/// <param name="x">X-coord</param>
		/// <param name="y">Y-coord</param>
		/// <param name="format">String format</param>
		/// <param name="args">String format args</param>
		/// <returns>Width of string (in pixels)</returns>
		public int DrawString(int x, int y, string format, params object[] args)
		{
			Vector2 v = new Vector2(x, y);
			return DrawString(v, m_color, format, args);
		}

		/// <summary>
		/// Draw the given string at (x,y) using the specified color
		/// </summary>
		/// <param name="x">X-coord</param>
		/// <param name="y">Y-coord</param>
		/// <param name="color">Text color</param>
		/// <param name="format">String format</param>
		/// <param name="args">String format args</param>
		/// <returns>Width of string (in pixels)</returns>
		public int DrawString(int x, int y, Color color, string format, params object[] args)
		{
			Vector2 v = new Vector2(x, y);
			return DrawString(v, color, format, args);
		}

		/// <summary>
		/// Draw the given string using the specified color.
		/// The text drawing location is immediately after the last drawn text (default=0,0).
		/// </summary>
		/// <param name="color">Text color</param>
		/// <param name="format">String format</param>
		/// <param name="args">String format args</param>
		/// <returns>Width of string (in pixels)</returns>
		public int DrawString(Color color, string format, params object[] args)
		{
			return DrawString(m_vPen, color, format, args);
		}

		/// <summary>
		/// Draw the given string at (x,y).
		/// The text drawing location is immediately after the last drawn text (default=0,0).
		/// The text color is inherited from the last draw command (default=White).
		/// </summary>
		/// <param name="format">String format</param>
		/// <param name="args">String format args</param>
		/// <returns>Width of string (in pixels)</returns>
		public int DrawString(string format, params object[] args)
		{
			return DrawString(m_vPen, m_color, format, args);
		}

		/// <summary>
		/// Draw the given string at vOrigin using the specified color
		/// </summary>
		/// <param name="vOrigin">(x,y) coord</param>
		/// <param name="color">Text color</param>
		/// <param name="format">String format</param>
		/// <param name="args">String format args</param>
		/// <returns>Width of string (in pixels)</returns>
		public int DrawString(Vector2 vOrigin, Color color, string format, params object[] args)
		{
			string str = string.Format(format, args);

			Vector2 vAt = vOrigin;
			int nWidth = 0;
			char cLast = '\0';

			m_sb.Begin(SpriteBlendMode.AlphaBlend);

			// draw each character in the string
			foreach (char c in str)
			{
				if (!m_dictUnicode2GlyphInfo.ContainsKey(c))
				{
					//TODO: print out undefined char glyph
					continue;
				}

				GlyphInfo ginfo = m_dictUnicode2GlyphInfo[c];

				// if kerning is enabled, get the kern adjustment for this char pair
				if (m_fKern)
				{
					int nKern = CalcKern(cLast, c);
					vAt.X += nKern;
					nWidth += nKern;
					cLast = c;
				}
	
				// draw the glyph
				vAt.X += ginfo.nLeftSideBearing;
				if (ginfo.nWidth != 0 && ginfo.nHeight != 0)
				{
					Rectangle r = new Rectangle(ginfo.nOriginX, ginfo.nOriginY, ginfo.nWidth, ginfo.nHeight);
					m_sb.Draw(m_dictBitmapID2Texture[ginfo.nBitmapID], vAt, r, color);
				}

				// update the string width and advance the pen to the next drawing position
				nWidth += ginfo.nAdvanceWidth;
				vAt.X += ginfo.nAdvanceWidth - ginfo.nLeftSideBearing;
			}

			m_sb.End();

			// record final pen position and color
			m_vPen = vAt;
			m_color = color;

			return nWidth;
		}

		/// <summary>
		/// Get the kern value for the given pair of characters
		/// </summary>
		/// <param name="chLeft">Left character</param>
		/// <param name="chRight">Right character</param>
		/// <returns>Amount to kern (in pixels)</returns>
		private int CalcKern(char chLeft, char chRight)
		{
			if (m_dictKern.ContainsKey(chLeft))
			{
				Dictionary<char, int> kern2 = m_dictKern[chLeft];
				if (kern2.ContainsKey(chRight))
					return kern2[chRight];
			}
			return 0;
		}

		#region Load Font from XML

		/// <summary>
		/// Load the font data from an XML font descriptor file
		/// </summary>
		/// <param name="xnl">XML node list containing the entire font descriptor file</param>
		private void LoadFontXML(XmlNodeList xnl)
		{
			foreach (XmlNode xn in xnl)
			{
				if (xn.Name == "font")
				{
					m_nBase = Int32.Parse(GetXMLAttribute(xn, "base"));
					m_nHeight = Int32.Parse(GetXMLAttribute(xn, "height"));

					LoadFontXML_font(xn.ChildNodes);
				}
			}
		}

		/// <summary>
		/// Load the data from the "font" node
		/// </summary>
		/// <param name="xnl">XML node list containing the "font" node's children</param>
		private void LoadFontXML_font(XmlNodeList xnl)
		{
			foreach (XmlNode xn in xnl)
			{
				if (xn.Name == "bitmaps")
					LoadFontXML_bitmaps(xn.ChildNodes);
				if (xn.Name == "glyphs")
					LoadFontXML_glyphs(xn.ChildNodes);
				if (xn.Name == "kernpairs")
					LoadFontXML_kernpairs(xn.ChildNodes);
			}
		}

		/// <summary>
		/// Load the data from the "bitmaps" node
		/// </summary>
		/// <param name="xnl">XML node list containing the "bitmaps" node's children</param>
		private void LoadFontXML_bitmaps(XmlNodeList xnl)
		{
			foreach (XmlNode xn in xnl)
			{
				if (xn.Name == "bitmap")
				{
					string strID = GetXMLAttribute(xn, "id");
					string strFilename = GetXMLAttribute(xn, "name");
					string strSize = GetXMLAttribute(xn, "size");
					string[] aSize = strSize.Split('x');
					
					BitmapInfo bminfo;
					bminfo.strFilename = strFilename;
					bminfo.nX = Int32.Parse(aSize[0]);
					bminfo.nY = Int32.Parse(aSize[1]);

					m_dictBitmapID2BitmapInfo[Int32.Parse(strID)] = bminfo;
				}
			}
		}

		/// <summary>
		/// Load the data from the "glyphs" node
		/// </summary>
		/// <param name="xnl">XML node list containing the "glyphs" node's children</param>
		private void LoadFontXML_glyphs(XmlNodeList xnl)
		{
			foreach (XmlNode xn in xnl)
			{
				if (xn.Name == "glyph")
				{
					string strChar = GetXMLAttribute(xn, "ch");
					string strBitmapID = GetXMLAttribute(xn, "bm");
					string strOrigin = GetXMLAttribute(xn, "origin");
					string strSize = GetXMLAttribute(xn, "size");
					string strAW = GetXMLAttribute(xn, "aw");
					string strLSB = GetXMLAttribute(xn, "lsb");

					string[] aOrigin = strOrigin.Split(',');
					string[] aSize = strSize.Split('x');

					GlyphInfo ginfo = new GlyphInfo();
					ginfo.nBitmapID = Int32.Parse(strBitmapID);
					ginfo.nOriginX = Int32.Parse(aOrigin[0]);
					ginfo.nOriginY = Int32.Parse(aOrigin[1]);
					ginfo.nWidth = Int32.Parse(aSize[0]);
					ginfo.nHeight = Int32.Parse(aSize[1]);
					ginfo.nAdvanceWidth = Int32.Parse(strAW);
					ginfo.nLeftSideBearing = Int32.Parse(strLSB);

					m_dictUnicode2GlyphInfo[strChar[0]] = ginfo;
				}
			}
		}

		/// <summary>
		/// Load the data from the "kernpairs" node
		/// </summary>
		/// <param name="xnl">XML node list containing the "kernpairs" node's children</param>
		private void LoadFontXML_kernpairs(XmlNodeList xnl)
		{
			foreach (XmlNode xn in xnl)
			{
				if (xn.Name == "kernpair")
				{
					string strLeft = GetXMLAttribute(xn, "left");
					string strRight = GetXMLAttribute(xn, "right");
					string strAdjust = GetXMLAttribute(xn, "adjust");

					char chLeft = strLeft[0];
					char chRight = strRight[0];

					// create a kern dict for the left char if needed
					if (!m_dictKern.ContainsKey(chLeft))
						m_dictKern[chLeft] = new Dictionary<char,int>();

					// add the right char to the left char's kern dict
					Dictionary<char, int> kern2 = m_dictKern[chLeft];
					kern2[chRight] = Int32.Parse(strAdjust);
				}
			}
		}

		/// <summary>
		/// Get the XML attribute value (without throwing if the attribute doesn't exist)
		/// </summary>
		/// <param name="n">XML node</param>
		/// <param name="strAttr">Attribute name</param>
		/// <returns>Attribute value, or the empty string if the attribute doesn't exist</returns>
		private static string GetXMLAttribute(XmlNode n, string strAttr)
		{
			string strVal = "";
			try
			{
				strVal = n.Attributes[strAttr].Value;
			}
			catch
			{
				strVal = "";
			}
			return strVal;
		}

		#endregion
	}
}
