/** 
 *  @author Peter Norvig, peter@norvig.com http://www.norvig.com 
 * Copyright 1998 Peter Norvig, see http://www.norvig.com/license.html
 * 
 * C# version (C) 2003 John Palevich
 * 
 **/
using System;
using System.IO;
using System.Text;
using System.Reflection;

namespace CSScheme
{
	/// <summary>
	/// Summary description for CSScheme.
	/// </summary>
	/// 


	// This class represents a Scheme interpreter.
	public class Scheme : SchemeUtils
	{
		public Scheme()
		{
			//
			// TODO: Add constructor logic here
			//
		}

		public InputPort input = new InputPort(Console.In);
		public TextWriter output = Console.Out;
		public Environment globalEnvironment = new Environment();

		/** Create a Scheme interpreter and load an array of files into it.
		 * Also load SchemePrimitives.CODE. **/
		public Scheme(String[] files) 
		{ 
			Primitive.installPrimitives(globalEnvironment); 
			try 
			{
				load(new InputPort(new StringReader(SchemePrimitives.CODE)));
				for (int i = 0; i < (files == null ? 0 : files.Length); i++) 
				{
					load(files[i]);
				} 
			} 
			catch (Exception) { ; }
		}

		//////////////// Main Loop

		/** Create a new Scheme interpreter, passing in the command line args
		 * as files to load, and then enter a read eval write loop. **/
		public static void main(String[] files) 
		{
			new Scheme(files).readEvalWriteLoop();
		}

		/** Prompt, read, eval, and write the result. 
		 * Also sets up a catch for any RuntimeExceptions encountered. **/
		public void readEvalWriteLoop() 
		{
			Object x;
			for(;;) 
			{
				try 
				{
					output.Write("> "); output.Flush();
					if (InputPort.isEOF(x = input.readChar())) return;
					write(eval(x), output, true); 
					output.WriteLine(); output.Flush();
				} 
				catch (Exception) { ; }
			}
		}

		/** Eval all the expressions in a file. Calls load(InputPort). **/
		public Object load(Object fileName) 
		{
			String name = stringify(fileName, false);
			try { return load(new InputPort(new FileStream(name, FileMode.Open, FileAccess.Read))); }
			catch (Exception) { return error("can't load " + name); }
		}

		/** Eval all the expressions coming from an InputPort. **/
		public Object load(InputPort inp) 
		{
			Object x = null;
			for(;;) 
			{
				if (InputPort.isEOF(x = inp.read())) return TRUE;
				eval(x); 
			}
		}
      
		//////////////// Evaluation

		/** Evaluate an object, x, in an environment. **/
		public Object eval(Object x, Environment env) 
		{ 
			// The purpose of the while loop is to allow tail recursion.
			// The idea is that in a tail recursive position, we do "x = ..."
			// and loop, rather than doing "return eval(...)".
			while (true) 
			{
				if (x is String) 
				{         // VARIABLE
					return env.lookup((String)x);
				} 
				else if (!(x is Pair)) 
				{ // CONSTANT
					return x;
				} 
				else 
				{                           
					Object fn = first(x);
					Object args = rest(x);
					if(fn is String)
					{
						String sfn = (String) fn;
						if (sfn == "quote") 
						{             // QUOTE
							return first(args);
						} 
						else if (sfn == "begin") 
						{      // BEGIN
							for (; rest(args) != null; args = rest(args)) 
							{
								eval(first(args), env);
							}
							x = first(args);
						} 
						else if (sfn == "define") 
						{     // DEFINE
							if (first(args) is Pair)
								return env.define(first(first(args)),
									eval(cons("lambda", cons(rest(first(args)), rest(args))), env));
							else return env.define(first(args), eval(second(args), env));
						} 
						else if (sfn == "set!") 
						{       // SET!
							return env.set(first(args), eval(second(args), env));
						} 
						else if (sfn == "if") 
						{         // IF
							x = (truth(eval(first(args), env))) ? second(args) : third(args);
						} 
						else if (sfn == "cond") 
						{       // COND
							x = reduceCond(args, env);
						} 
						else if (sfn == "lambda") 
						{     // LAMBDA
							return new Closure(first(args), rest(args), env);
						} 
						else if (sfn == "macro") 
						{      // MACRO
							return new Macro(first(args), rest(args), env);
						}
						else
						{
							error("Unknown primitive fn" + fn);
						}
					}
					else 
					{                         // PROCEDURE CALL:
						fn = eval(fn, env);
						if (fn is Macro) 
						{          // (MACRO CALL)
							x = ((Macro)fn).expand(this, (Pair)x, args);
						} 
						else if (fn is Closure) 
						{ // (CLOSURE CALL)
							Closure f = (Closure)fn;
							x = f.body;
							env = new Environment(f.parms, evalList(args, env), f.env);
						} 
						else 
						{                            // (OTHER PROCEDURE CALL)
							return Procedure.proc(fn).apply(this, evalList(args, env));
						}
					}
				}
			}
		}

		/** Eval in the global environment. **/
		public Object eval(Object x) { return eval(x, this.globalEnvironment); }

		/** Evaluate each of a list of expressions. **/
		Pair evalList(Object list, Environment env) 
		{
			if (list == null) 
				return null;
			else if (!(list is Pair)) 
			{
				error("Illegal arg list: " + list);
				return null;
			} 
			else 
				return cons(eval(first(list), env), evalList(rest(list), env));
		}

		/** Reduce a cond expression to some code which, when evaluated,
		 * gives the value of the cond expression.  We do it that way to
		 * maintain tail recursion. **/
		Object reduceCond(Object clauses, Environment env) 
		{
			Object result = null;
			for (;;) 
			{
				if (clauses == null) return FALSE;
				Object clause = first(clauses); clauses = rest(clauses);
				if ( first(clause) == (Object) "else" 
					|| truth(result = eval(first(clause), env)))
					if (rest(clause) == null) return list("quote", result);
					else if (second(clause) == (Object) "=>")
						return list(third(clause), list("quote", result));
					else return cons("begin", rest(clause));
			}
		}

	}

	public abstract class SchemeUtils 
	{
		public static readonly Boolean TRUE = true;
		public static readonly Boolean FALSE = false;

		public static readonly Double ZERO = 0.0;
		public static readonly Double ONE = 1.0;
		//////////////// Conversion Routines ////////////////

		// The following convert or coerce objects to the right type.

		/** Convert bool to Boolean. **/
		public static Boolean truth(bool x) { return x ? TRUE : FALSE; }

		/** Convert Scheme object to bool.  Only #f is false, others are true. **/
		public static bool truth(Object x) { return ! (x == (Object) FALSE); }

		/** Convert double to Double. Caches 0 and 1; makes new for others. **/
		public static Double num(double x) 
		{ 
			return (x == 0.0) ? ZERO : (x == 1.0) ? ONE : x; }

		/** Converts a Scheme object to a double, or calls error. **/
		public static double num(Object x) 
		{ 
			try
			{
				return Convert.ToDouble(x);
			}
			catch
			{
				return num(error("expected a number, got: " + x));
			}
		}

		/** Converts a Scheme object to a char, or calls error. **/
		public static char chr(Object x) 
		{
			try
			{
				return Convert.ToChar(x);
			}
			catch
			{
				return chr(error("expected a char, got: " + x));
			}
		}

		/** Converts a char to a Char. **/
		public static Char chr(char ch) 
		{
			return ch;
		}

		/** Coerces a Scheme object to a Scheme string, which is a char[]. **/
		public static char[] str(Object x) 
		{
			if (x is char[]) return (char[])x;
			else return str(error("expected a string, got: " + x)); 
		}

		/** Coerces a Scheme object to a Scheme symbol, which is a string. **/
		public static String sym(Object x) 
		{
			if (x is String) return (String)x;
			else return sym(error("expected a symbol, got: " + x)); 
		}

		/** Coerces a Scheme object to a Scheme vector, which is a Object[]. **/
		public static Object[] vec(Object x) 
		{
			if (x is Object[]) return (Object[])x;
			else return vec(error("expected a vector, got: " + x)); 
		}

		/** Coerces a Scheme object to a Scheme input port, which is an InputPort.
		 * If the argument is null, returns interpreter.input. **/
		public static InputPort inPort(Object x, Scheme interp) 
		{
			if (x == null) return interp.input;
			else if (x is InputPort) return (InputPort)x;
			else return inPort(error("expected an input port, got: " + x), interp); 
		}

		/** Coerces a Scheme object to a Scheme input port, which is a TextWriter.
		 * If the argument is null, returns Console.Out. **/
		public static TextWriter outPort(Object x, Scheme interp) 
		{
			if (x == null) return interp.output;
			else if (x is TextWriter) return (TextWriter)x;
			else return outPort(error("expected an output port, got: " + x), interp); 
		}

		//////////////// Error Routines ////////////////

		/** A continuable error. Prints an error message and then prompts for
		 * a value to eval and return. **/
		public static Object error(String message) 
		{
			Console.Error.WriteLine("**** ERROR: " + message);
			throw new Exception(message);  
		}

		public static Object warn(String message) 
		{
			Console.Error.WriteLine("**** WARNING: " + message);
			return "<warn>";
		}

		//////////////// Basic manipulation Routines ////////////////

		// The following are used throughout the code.

		/** Like Common Lisp first; car of a Pair, or null for anything else. **/
		public static Object first(Object x) 
		{
			return (x is Pair) ? ((Pair)x).first : null; 
		}

		/** Like Common Lisp rest; car of a Pair, or null for anything else. **/
		public static Object rest(Object x) 
		{
			return (x is Pair) ? ((Pair)x).rest : null; 
		}

		/** Like Common Lisp (setf (first ... **/
		public static Object setFirst(Object x, Object y) 
		{
			return (x is Pair) ? ((Pair)x).first = y 
				: error("Attempt to set-car of a non-Pair:" + stringify(x));
		}

		/** Like Common Lisp (setf (rest ... **/
		public static Object setRest(Object x, Object y) 
		{
			return (x is Pair) ? ((Pair)x).rest = y 
				: error("Attempt to set-cdr of a non-Pair:" + stringify(x));
		}

		/** Like Common Lisp second. **/
		public static Object second(Object x) 
		{
			return first(rest(x));
		}

		/** Like Common Lisp third. **/
		public static Object third(Object x) 
		{
			return first(rest(rest(x)));
		}

		/** Creates a two element list. **/
		public static Pair list(Object a, Object b) 
		{
			return new Pair(a, new Pair(b, null));
		}

		/** Creates a one element list. **/
		public static Pair list(Object a) 
		{
			return new Pair(a, null);
		}

		/** listStar(args) is like Common Lisp (apply #'list* args) **/
		public static Object listStar(Object args) 
		{
			if (rest(args) == null) return first(args);
			else return cons(first(args), listStar(rest(args)));
		}

		/** cons(x, y) is the same as new Pair(x, y). **/
		public static Pair cons(Object a, Object b) 
		{
			return new Pair(a, b);
		}

		/** Reverse the elements of a list. **/
		public static Object reverse(Object x) 
		{
			Object result = null;
			while (x is Pair) 
			{
				result = cons(first(x), result);
				x = rest(x);
			}
			return result;
		}

		/** Check if two objects are equal. **/
		public static bool equal(Object x, Object y) 
		{
			if (x == null || y == null) 
			{
				return x == y;
			} 
			else if (x is char[]) 
			{
				if (!(y is char[])) return false;
				char[] xc = (char[])x, yc = (char[])y;
				if (xc.Length != yc.Length) return false;
				for (int i = xc.Length - 1; i >= 0; i--) 
				{
					if (xc[i] != yc[i]) return false;
				}
				return true;
			} 
			else if (x is Object[]) 
			{
				if (!(y is Object[])) return false;
				Object[] xo = (Object[])x, yo = (Object[])y;
				if (xo.Length != yo.Length) return false;
				for (int i = xo.Length - 1; i >= 0; i--) 
				{
					if (!equal(xo[i],yo[i])) return false;
				}
				return true;
			} 
			else 
			{
				return x.Equals(y);
			}
		}

		/** Check if two objects are == or are equal numbers or characters. **/
		public static bool eqv(Object x, Object y) 
		{
			return x == y 
				|| (x is Double && x.Equals(y))
				|| (x is Char && x.Equals(y));
		}

		/** The length of a list, or zero for a non-list. **/
		public static int length(Object x) 
		{
			int len = 0;
			while (x is Pair) 
			{
				len++;
				x = ((Pair)x).rest;
			}
			return len;
		}

		/** Convert a list of characters to a Scheme string, which is a char[]. **/
		public static char[] listToString(Object chars) 
		{
			char[] str = new char[length(chars)];
			for (int i = 0; chars is Pair; i++) 
			{
				str[i] = chr(first(chars));
				chars = rest(chars);
			}
			return str;
		}
 
		/** Convert a list of Objects to a Scheme vector, which is a Object[]. **/
		public static Object[] listToVector(Object objs) 
		{
			Object[] vec = new Object[length(objs)];
			for (int i = 0; objs is Pair; i++) 
			{
				vec[i] = first(objs);
				objs = rest(objs);
			}
			return vec;
		}
 
		/** Write the object to a port.  If quoted is true, use "str" and #\c,
		 * otherwise use str and c. **/
		public static Object write(Object x, TextWriter port, bool quoted) 
		{
			port.Write(stringify(x, quoted)); 
			port.Flush();
			return x;
		}

		/** Convert a vector to a List. **/
		public static Pair vectorToList(Object x) 
		{
			if (x is Object[]) 
			{
				Object[] vec = (Object[])x;
				Pair result = null;
				for (int i = vec.Length - 1; i >= 0; i--) 
					result = cons(vec[i], result);
				return result;
			} 
			else 
			{
				error("expected a vector, got: " + x);
				return null;
			}
		}

		/** Convert a Scheme object to its printed representation, as
		 * a java String (not a Scheme string). If quoted is true, use "str" and #\c,
		 * otherwise use str and c. You need to pass in a StringBuilder that is used 
		 * to accumulate the results. (If the interface didn't work that way, the
		 * system would use lots of little internal StringBuffers.  But note that
		 * you can still call <tt>stringify(x)</tt> and a new StringBuilder will
		 * be created for you. **/

		public static void stringify(Object x, bool quoted, StringBuilder buf) 
		{ 
			if (x == null) 
				buf.Append("()");
			else if (x is Double) 
			{
				double d = (Double) x;
				if (Math.Round(d) == d) buf.Append((long)d); else buf.Append(d);
			} 
			else if (x is Char) 
			{
				if (quoted) buf.Append("#\\");
				buf.Append(x);
			} 
			else if (x is Pair) 
			{
				((Pair)x).stringifyPair(quoted, buf);
			} 
			else if (x is char[]) 
			{
				char[] chars = (char[])x;
				if (quoted) buf.Append('"');
				for (int i = 0; i < chars.Length; i++) 
				{
					if (quoted && chars[i] == '"') buf.Append('\\');
					buf.Append(chars[i]);
				}
				if (quoted) buf.Append('"');
			} 
			else if (x is Object[]) 
			{
				Object[] v = (Object[])x;
				buf.Append("#(");
				for (int i=0; i<v.Length; i++) 
				{
					stringify(v[i], quoted, buf);
					if (i != v.Length-1) buf.Append(' ');
				}
				buf.Append(')');
			} 
			else if (x.Equals(TRUE)) 
			{
				buf.Append("#t");
			} 
			else if (x.Equals(FALSE)) 
			{
				buf.Append("#f");
			} 
			else 
			{
				buf.Append(x);
			}
		}

		/** Convert x to a Java String giving its external representation. 
		 * Strings and characters are quoted. **/
		public static String stringify(Object x) { return stringify(x, true); }

		/** Convert x to a Java String giving its external representation. 
		 * Strings and characters are quoted iff <tt>quoted</tt> is true.. **/
		public static String stringify(Object x, bool quoted) 
		{ 
			StringBuilder buf = new StringBuilder();
			stringify(x, quoted, buf);
			return buf.ToString();
		}

		/** For debugging purposes, prints output. **/
		static Object p(Object x) 
		{
			Console.Out.WriteLine(stringify(x));
			return x;
		}

		/** For debugging purposes, prints output. **/
		static Object p(String msg, Object x) 
		{
			Console.Out.WriteLine(msg + ": " + stringify(x));
			return x;
		}
	}


	public abstract class Procedure : SchemeUtils 
	{

		public String name = "anonymous procedure";

		override public String ToString() { return "{" + name + "}"; }

		public abstract Object apply(Scheme interpreter, Object args);

		/** Coerces a Scheme object to a procedure. **/
		public static Procedure proc(Object x) 
		{
			if (x is Procedure) return (Procedure) x;
			else return proc(error("Not a procedure: " + stringify(x)));
		}

	}

	/** A Pair has two fields, first and rest (or car and cdr). 
	 * The empty list is represented by null. The methods that you might
	 * expect here, like first, second, list, etc. are instead static methods
	 * in class SchemeUtils. 
	 */

	public class Pair : SchemeUtils 
	{

		/** The first element of the pair. **/
		new public Object first;

		/** The other element of the pair. **/
		new public Object rest;

		/** Build a pair from two components. **/
		public Pair(Object first, Object rest) 
		{ 
			this.first = first; this.rest = rest; 
		}

		/** Two pairs are equal if their first and rest fields are equal. **/
		public bool equals(Object x) 
		{
			if (x == this) return true;
			else if (!(x is Pair)) return false;
			else 
			{
				Pair that = (Pair)x;
				return equal(this.first, that.first)
					&& equal(this.rest, that.rest);
			}
		}

		/** Return a String representation of the pair. **/
		public String toString() { return stringify(this, true); }

		/** Build up a String representation of the Pair in a StringBuilder. **/
		public void stringifyPair(bool quoted, StringBuilder buf) 
		{
			String special = null;
			if ((rest is Pair) && SchemeUtils.rest(rest) == null) 
				special = (first == (Object) "quote") ? "'" : (first == (Object) "quasiquote") ? "`"
					: (first == (Object) "unquote") ? "," : (first  == (Object) "unquote-splicing") ? ",@"
					: null;
	
			if (special != null) 
			{
				buf.Append(special); stringify(second(this), quoted, buf);
			} 
			else 
			{
				buf.Append('(');
				stringify(first, quoted, buf);
				Object tail = rest;
				while (tail is Pair) 
				{
					buf.Append(' ');
					stringify(((Pair)tail).first, quoted, buf);
					tail = ((Pair)tail).rest;
				}
				if (tail != null) 
				{
					buf.Append(" . ");
					stringify(tail, quoted, buf);
				}
				buf.Append(')');
			}
		}

	}

	/** InputPort is to Scheme as StreamReader is to Java. 
	 **/

	public class InputPort : SchemeUtils 
	{
		public static  String EOF = "#!EOF";
		bool isPushedToken = false;
		bool isPushedChar = false;
		Object  pushedToken = null;
		int     pushedChar = -1;
		TextReader  inp;
		StringBuilder buff = new StringBuilder();

		/** Construct an InputPort from an Stream. **/
		public InputPort(Stream inp) { this.inp = new StreamReader(inp);}

		/** Construct an InputPort from a TextReader. **/
		public InputPort(TextReader inp) { this.inp = inp;}

		/** Read and return a Scheme character or EOF. **/
		public Object readChar() 
		{
			try 
			{
				if (isPushedChar) 
				{
					isPushedChar = false;
					if (pushedChar == -1) return EOF; else return chr((char)pushedChar);
				} 
				else 
				{
					int ch = inp.Read();
					if (ch == -1) return EOF; else return chr((char)ch);
				}
			} 
			catch (IOException e) 
			{
				warn("On input, exception: " + e);
				return EOF;
			}
		}

		/** Peek at and return the next Scheme character (or EOF).
		 * However, don't consume the character. **/
		public Object peekChar() 
		{
			int p = peekCh();
			if (p == -1) return EOF; else return chr((char)p);
		}

		/** Push a character back to be re-used later. **/
		int pushChar(int ch) 
		{
			isPushedChar = true;
			return pushedChar = ch;
		}

		/** Pop off the previously pushed character. **/
		int popChar() 
		{
			isPushedChar = false;
			return pushedChar;
		}

		/** Peek at and return the next Scheme character as an int, -1 for EOF.
		 * However, don't consume the character. **/
		public int peekCh() 
		{
			try { return isPushedChar ? pushedChar : pushChar(inp.Read()); }
			catch (IOException e) 
			{
				warn("On input, exception: " + e);
				return -1;
			}
		}

		/** Read and return a Scheme expression, or EOF. **/
		public Object read() 
		{
			try 
			{
				Object token = nextToken(); 
				if (token== (Object)("("))
					return readTail(false);
				else if (token== (Object)(")"))
				{ warn("Extra ) ignored."); return read(); }
				else if (token== (Object)("."))
				{ warn("Extra . ignored."); return read(); }
				else if (token== (Object)("'"))
					return list("quote", read());
				else if (token== (Object)("`"))
					return list("quasiquote", read());
				else if (token== (Object)(","))
					return list("unquote", read());
				else if (token== (Object)(",@"))
					return list("unquote-splicing", read());
				else 
					return token;
			} 
			catch (IOException e) 
			{
				warn("On input, exception: " + e);
				return EOF;
			}
		}

		/** Close the port.  Return TRUE if ok. **/
		public Object close() 
		{
			try { this.inp.Close(); return TRUE; }
			catch (IOException e) { return error("IOException: " + e); }
		}

		/** Is the argument the EOF object? **/
		public static bool isEOF(Object x) { return x.Equals(EOF); }

		Object readTail(bool dotOK) 
		{
			Object token = nextToken(); 
			if (token.Equals(EOF))
				return error("EOF during read.");
			else if (token== (Object)(")"))
				return null;
			else if (token== (Object)(".")) 
			{
				Object result = read();
				token = nextToken(); 
				if (token== (Object)(")")) warn("Where's the ')'? Got " +
									  token + " after .");
				return result;
			} 
			else 
			{
				isPushedToken = true;
				pushedToken = token;
				return cons(read(), readTail(true));
			}
		}

		Object nextToken() 
		{
			int ch;

			// See if we should re-use a pushed char or token
			if (isPushedToken) 
			{
				isPushedToken = false;
				return pushedToken;
			} 
			else if (isPushedChar) 
			{
				ch = popChar();
			} 
			else 
			{
				ch = inp.Read();
			}

			// Skip whitespace
			while (Char.IsWhiteSpace((char)ch)) ch = inp.Read();

			// See what kind of non-white character we got
			switch(ch) 
			{
				case -1: return EOF;
				case '(' : return "(";
				case ')':  return ")";
				case '\'': return "'";
				case '`':  return "`";
				case ',': 
					ch = inp.Read();
					if (ch == '@') return ",@";
					else { pushChar(ch); return ","; }
				case ';': 
					// Comment: skip to end of line and then read next token
					while(ch != -1 && ch != '\n' && ch != '\r') ch = inp.Read();
					return nextToken();
				case '"':
					// Strings are represented as char[]
					buff.Length = 0;
					while ((ch = inp.Read()) != '"' && ch != -1) 
					{
						buff.Append((char) ((ch == '\\') ? inp.Read() : ch));
					}
					if (ch == -1) warn("EOF inside of a string.");
					return buff.ToString().ToCharArray();
				case '#':
				switch (ch = inp.Read()) 
				{
					case 't': return TRUE;
					case 'T': return TRUE;
					case 'f': return FALSE;
					case 'F': return FALSE;
					case '(':
						pushChar('(');
						return listToVector(read());
					case '\\': 
						ch = inp.Read();
						if (ch == 's' || ch == 'S' || ch == 'n' || ch == 'N') 
						{
							pushChar(ch);
							Object token = nextToken();
							if (token== (Object)("space")) return chr(' ');
							else if (token== (Object)("newline")) return chr('\n');
							else 
							{
								isPushedToken = true;
								pushedToken = token;
								return chr((char)ch);
							}
						} 
						else 
						{
							return chr((char)ch);
						}
					case 'e': return nextToken();
					case 'i': return nextToken();
					case 'd': return nextToken();
					case 'b': goto CharNotImpl;
					case 'o': goto CharNotImpl;
					case 'x': goto CharNotImpl;
						CharNotImpl:
						warn("#" + ((char)ch) + " not implemented, ignored."); 
						return nextToken();
					default: 
						warn("#" + ((char)ch) + " not recognized, ignored."); 
						return nextToken();
				}
				default: 
					buff.Length = 0;
					int c = ch;
					do 
					{ 
						buff.Append((char)ch);
						ch = inp.Read();
					} while (!Char.IsWhiteSpace((char)ch) && ch != -1 &&
						ch != '(' && ch != ')' && ch != '\'' && ch != ';'
						&& ch != '"' && ch != ',' && ch != '`');
					pushChar(ch);
					// Try potential numbers, but catch any format errors.
					if (c == '.' || c == '+' || c == '-' || (c >= '0' && c <= '9')) 
					{
						try { return Convert.ToDouble(buff.ToString()); }
						catch (FormatException ) { ; }
						catch (OverflowException ) { ; }
					}
					return String.Intern(buff.ToString().ToLower());
			}
		}
	}
#if false
	public class DotNetMember : Procedure 
	{

		Type[] argClasses;
		MemberInfo member;
		bool isStatic;

		public DotNetMember(String memberName, Object targetClassName, 
			Object argClassNames) 
		{
			this.name = targetClassName + "." + memberName;
			try 
			{
				argClasses = typeArray(argClassNames);
				member = toType(targetClassName).GetMember(memberName, argClasses, 0);
				if(method == null)
				{
					error("Can't get method " + name + " " + memberName);
				}
				isStatic = method.IsStatic;
			} 
			catch (AmbiguousMatchException) 
			{ 
				error("Ambiguous match " + name + " " + memberName); 
			} 
		}

		/** Apply the method to a list of arguments. **/
		override public Object apply(Scheme interpreter, Object args) 
		{
			try 
			{
				if (isStatic) return method.Invoke(null, toArray(args));
				else return method.Invoke(first(args), toArray(rest(args)));
			} 
			catch (IllegalAccessException e) { ; }
			catch (IllegalArgumentException e) { ; }
			catch (InvocationTargetException e) { ; }
			catch (NullPointerException e) { ; }
			return error("Bad CLR Method application:" + this 
				+ stringify(args) + ", "); 
		}

		public static Type toType(Object arg)
		{ 
			if (arg is Type) return (Type)arg;
			string arg2 = stringify(arg, false);

			if (arg2== (Object)("void"))    return System.Void.TYPE;
			else if (arg2== (Object)("bool")) return System.Boolean.TYPE;
			else if (arg2== (Object)("char"))    return System.Char.TYPE;
			else if (arg2== (Object)("byte"))    return System.Byte.TYPE;
			else if (arg2== (Object)("short"))   return System.Short.TYPE;
			else if (arg2== (Object)("int"))     return System.Integer.TYPE;
			else if (arg2== (Object)("long"))    return System.Long.TYPE;
			else if (arg2== (Object)("float"))   return System.Float.TYPE;
			else if (arg2== (Object)("double"))  return System.Double.TYPE;
			else return Type.ForName((String)arg);
		}

		/** Convert a list of Objects into an array.  Peek at the argClasses
		 * array to see what's expected.  That enables us to convert between
		 * Double and Integer, something Java won't do automatically. **/
		public Object[] toArray(Object args) 
		{
			int n = length(args);
			int diff = n - argClasses.Length;
			if (diff != 0)
				error(Math.abs(diff) + " too " + ((diff>0) ? "many" : "few")
					+ " args to " + name);
			Object[] array = new Object[n];
			for(int i = 0; i < n && i < argClasses.Length; i++) 
			{
				if (argClasses[i] == java.lang.Integer.TYPE)
					array[i] = new Integer((int)num(first(args)));
				else
					array[i] = first(args);
				args = rest(args);
			}
			return array;
		}

		/** Convert a list of class names into an array of Classes. **/
		public Type[] typeArray(Object args)
		{
			int n = length(args);
			Class[] array = new Class[n];
			for(int i = 0; i < n; i++) 
			{
				array[i] = toType(first(args));
				args = rest(args);
			}
			return array;
		}

	}
#endif
	/** A primitive is a procedure that is defined as part of the Scheme report,
	 * and is implemented in CLR code. 
	 **/

	public class Primitive : Procedure 
	{

		int minArgs;
		int maxArgs;
		int idNumber;

		public Primitive(int id, int minArgs, int maxArgs) 
		{
			this.idNumber = id; this.minArgs = minArgs; this.maxArgs = maxArgs;
		}

		private const int EQ = 0, LT = 1, GT = 2, GE = 3, LE = 4,
			ABS = 5, EOF_OBJECT = 6, EQQ = 7, EQUALQ = 8, FORCE = 9,
			CAR = 10, FLOOR = 11,  CEILING = 12, CONS = 13, 
			DIVIDE= 14, LENGTH = 15, LIST = 16, LISTQ = 17, APPLY = 18,
			MAX = 19, MIN = 20, MINUS = 21, NEWLINE = 22, 
			NOT = 23, NULLQ = 24, NUMBERQ = 25, PAIRQ = 26, PLUS = 27, 
			PROCEDUREQ = 28, READ = 29, CDR = 30, ROUND = 31, SECOND = 32, 
			SYMBOLQ = 33, TIMES = 34, TRUNCATE = 35, WRITE = 36, APPEND = 37,
			BOOLEANQ = 38, SQRT = 39, EXPT = 40, REVERSE = 41, ASSOC = 42, 
			ASSQ = 43, ASSV = 44, MEMBER = 45, MEMQ = 46, MEMV = 47, EQVQ = 48,
			LISTREF = 49, LISTTAIL = 50, STRINQ = 51, MAKESTRING = 52, STRING = 53,
			STRINGLENGTH = 54, STRINGREF = 55, STRINGSET = 56, SUBSTRING = 57, 
			STRINGAPPEND = 58, STRINGTOLIST = 59, LISTTOSTRING = 60, 
			SYMBOLTOSTRING = 61, STRINGTOSYMBOL = 62, EXP = 63, LOG = 64, SIN = 65,
			COS = 66, TAN = 67, ACOS = 68, ASIN = 69, ATAN = 70, 
			NUMBERTOSTRING = 71, STRINGTONUMBER = 72, CHARQ = 73,
			CHARALPHABETICQ = 74, CHARNUMERICQ = 75, CHARWHITESPACEQ = 76,
			CHARUPPERCASEQ = 77, CHARLOWERCASEQ = 78, CHARTOINTEGER = 79,
			INTEGERTOCHAR = 80, CHARUPCASE = 81, CHARDOWNCASE = 82, STRINGQ = 83,
			VECTORQ = 84, MAKEVECTOR = 85, VECTOR = 86, VECTORLENGTH = 87,
			VECTORREF = 88, VECTORSET = 89, LISTTOVECTOR = 90, MAP = 91, 
			FOREACH = 92, CALLCC = 93, VECTORTOLIST = 94, LOAD = 95, DISPLAY = 96,
			INPUTPORTQ = 98, CURRENTINPUTPORT = 99, OPENINPUTFILE = 100, 
			CLOSEINPUTPORT = 101, OUTPUTPORTQ = 103, CURRENTOUTPUTPORT = 104,
			OPENOUTPUTFILE = 105, CLOSEOUTPUTPORT = 106, READCHAR = 107,
			PEEKCHAR = 108, EVAL = 109, QUOTIENT = 110, REMAINDER = 111,
			MODULO = 112, THIRD = 113, EOFOBJECTQ = 114, GCD = 115, LCM = 116, 
			CXR = 117, ODDQ = 118, EVENQ = 119, ZEROQ = 120, POSITIVEQ = 121,
			NEGATIVEQ = 122, 
			CHARCMP = 123 /* to 127 */, CHARCICMP = 128 /* to 132 */,
			STRINGCMP = 133 /* to 137 */, STRINGCICMP = 138 /* to 142 */,
			EXACTQ = 143, INEXACTQ = 144, INTEGERQ = 145,
			CALLWITHINPUTFILE = 146, CALLWITHOUTPUTFILE = 147
			;

		//////////////// Extensions ////////////////

		private const int NEW = -1, CLASS = -2, METHOD = -3, EXIT = -4,
			SETCAR = -5, SETCDR = -6, TIMECALL = -11, MACROEXPAND = -12,
			ERROR = -13, LISTSTAR = -14
			;


		public static Environment installPrimitives(Environment env)  
		{

			int n = Int32.MaxValue;

			env
				.defPrim("*",       	TIMES,     0, n)
				.defPrim("*",       	TIMES,     0, n)
				.defPrim("+",       	PLUS,      0, n)
				.defPrim("-",       	MINUS,     1, n)
				.defPrim("/",       	DIVIDE,    1, n)
				.defPrim("<",       	LT,        2, n)
				.defPrim("<=",      	LE,        2, n)
				.defPrim("=",       	EQ,        2, n)
				.defPrim(">",       	GT,        2, n)
				.defPrim(">=",      	GE,        2, n)
				.defPrim("abs",     	ABS,       1)
				.defPrim("acos",    	ACOS,      1)
				.defPrim("append",         APPEND,    0, n)
				.defPrim("apply",   	APPLY,     2, n)
				.defPrim("asin",    	ASIN,      1)
				.defPrim("assoc",   	ASSOC,     2)
				.defPrim("assq",    	ASSQ,      2)
				.defPrim("assv",    	ASSV,      2)
				.defPrim("atan",    	ATAN,      1)
				.defPrim("bool?",	BOOLEANQ,  1)
				.defPrim("caaaar",         CXR,       1)
				.defPrim("caaadr",         CXR,       1)
				.defPrim("caaar",          CXR,       1)
				.defPrim("caadar",         CXR,       1)
				.defPrim("caaddr",         CXR,       1)
				.defPrim("caadr",          CXR,       1)
				.defPrim("caar",           CXR,       1)
				.defPrim("cadaar",         CXR,       1)
				.defPrim("cadadr",         CXR,       1)
				.defPrim("cadar",          CXR,       1)
				.defPrim("caddar",         CXR,       1)
				.defPrim("cadddr",         CXR,       1)
				.defPrim("caddr",     	THIRD,     1)
				.defPrim("cadr",  	        SECOND,    1)
				.defPrim("call-with-current-continuation",        CALLCC,    1)
				.defPrim("call-with-input-file", CALLWITHINPUTFILE, 2)
				.defPrim("call-with-output-file", CALLWITHOUTPUTFILE, 2)
				.defPrim("car",     	CAR,       1)
				.defPrim("cdaaar",         CXR,       1)
				.defPrim("cdaadr",         CXR,       1)
				.defPrim("cdaar",          CXR,       1)
				.defPrim("cdadar",         CXR,       1)
				.defPrim("cdaddr",         CXR,       1)
				.defPrim("cdadr",          CXR,       1)
				.defPrim("cdar",           CXR,       1)
				.defPrim("cddaar",         CXR,       1)
				.defPrim("cddadr",         CXR,       1)
				.defPrim("cddar",          CXR,       1)
				.defPrim("cdddar",         CXR,       1)
				.defPrim("cddddr",         CXR,       1)
				.defPrim("cdddr",          CXR,       1)
				.defPrim("cddr",           CXR,       1)
				.defPrim("cdr",     	CDR,       1)
				.defPrim("char->integer",  CHARTOINTEGER,      1)
				.defPrim("char-alphabetic?",CHARALPHABETICQ,      1)
				.defPrim("char-ci<=?",     CHARCICMP+LE, 2)
				.defPrim("char-ci<?" ,     CHARCICMP+LT, 2)
				.defPrim("char-ci=?" ,     CHARCICMP+EQ, 2)
				.defPrim("char-ci>=?",     CHARCICMP+GE, 2)
				.defPrim("char-ci>?" ,     CHARCICMP+GT, 2)
				.defPrim("char-downcase",  CHARDOWNCASE,      1)
				.defPrim("char-lower-case?",CHARLOWERCASEQ,      1)
				.defPrim("char-numeric?",  CHARNUMERICQ,      1)
				.defPrim("char-upcase",    CHARUPCASE,      1)
				.defPrim("char-upper-case?",CHARUPPERCASEQ,      1)
				.defPrim("char-whitespace?",CHARWHITESPACEQ,      1)
				.defPrim("char<=?",        CHARCMP+LE, 2)
				.defPrim("char<?",         CHARCMP+LT, 2)
				.defPrim("char=?",         CHARCMP+EQ, 2)
				.defPrim("char>=?",        CHARCMP+GE, 2)
				.defPrim("char>?",         CHARCMP+GT, 2)
				.defPrim("char?",   	CHARQ,     1)
				.defPrim("close-input-port", CLOSEINPUTPORT, 1)
				.defPrim("close-output-port", CLOSEOUTPUTPORT, 1)
				.defPrim("complex?", 	NUMBERQ,   1)
				.defPrim("cons",    	CONS,      2)
				.defPrim("cos",     	COS,       1)
				.defPrim("current-input-port", CURRENTINPUTPORT, 0)
				.defPrim("current-output-port", CURRENTOUTPUTPORT, 0)
				.defPrim("display",        DISPLAY,   1, 2)
				.defPrim("eof-object?",    EOFOBJECTQ, 1)
				.defPrim("eq?",     	EQQ,       2)
				.defPrim("equal?",  	EQUALQ,    2)
				.defPrim("eqv?",    	EQVQ,      2)
				.defPrim("eval",           EVAL,      1, 2)
				.defPrim("even?",          EVENQ,     1)
				.defPrim("exact?",         INTEGERQ,  1)
				.defPrim("exp",     	EXP,       1)
				.defPrim("expt",    	EXPT,      2)
				.defPrim("force",          FORCE,     1)
				.defPrim("for-each",       FOREACH,   1, n)
				.defPrim("gcd",            GCD,       0, n)
				.defPrim("inexact?",       INEXACTQ,  1)
				.defPrim("input-port?",    INPUTPORTQ, 1)
				.defPrim("integer->char",  INTEGERTOCHAR,      1)
				.defPrim("integer?",       INTEGERQ,  1)
				.defPrim("lcm",            LCM,       0, n)
				.defPrim("length",  	LENGTH,    1)
				.defPrim("list",    	LIST,      0, n)
				.defPrim("list->string", 	LISTTOSTRING, 1)
				.defPrim("list->vector",   LISTTOVECTOR,      1)
				.defPrim("list-ref", 	LISTREF,   2)
				.defPrim("list-tail", 	LISTTAIL,  2)
				.defPrim("list?",          LISTQ,     1)
				.defPrim("load",           LOAD,      1)
				.defPrim("log",     	LOG,       1)
				.defPrim("macro-expand",   MACROEXPAND,1)
				.defPrim("make-string", 	MAKESTRING,1, 2)
				.defPrim("make-vector",    MAKEVECTOR,1, 2)
				.defPrim("map",            MAP,       1, n)
				.defPrim("max",     	MAX,       1, n)
				.defPrim("member",  	MEMBER,    2)
				.defPrim("memq",    	MEMQ,      2)
				.defPrim("memv",    	MEMV,      2)
				.defPrim("min",     	MIN,       1, n)
				.defPrim("modulo",         MODULO,    2)
				.defPrim("negative?",      NEGATIVEQ, 1)
				.defPrim("newline", 	NEWLINE,   0, 1)
				.defPrim("not",     	NOT,       1)
				.defPrim("null?",   	NULLQ,     1)
				.defPrim("number->string", NUMBERTOSTRING,   1, 2)
				.defPrim("number?", 	NUMBERQ,   1)
				.defPrim("odd?",           ODDQ,      1)
				.defPrim("open-input-file",OPENINPUTFILE, 1)
				.defPrim("open-output-file", OPENOUTPUTFILE, 1)
				.defPrim("output-port?",   OUTPUTPORTQ, 1)
				.defPrim("pair?",   	PAIRQ,     1)
				.defPrim("peek-char",      PEEKCHAR,  0, 1)
				.defPrim("positive?",      POSITIVEQ, 1)
				.defPrim("procedure?", 	PROCEDUREQ,1)
				.defPrim("quotient",       QUOTIENT,  2)
				.defPrim("rational?",      INTEGERQ, 1)
				.defPrim("read",    	READ,      0, 1)
				.defPrim("read-char",      READCHAR,  0, 1)
				.defPrim("real?", 	        NUMBERQ,   1)
				.defPrim("remainder",      REMAINDER, 2)
				.defPrim("reverse", 	REVERSE,   1)
				.defPrim("round",  	ROUND,     1)
				.defPrim("set-car!",	SETCAR,    2)
				.defPrim("set-cdr!",	SETCDR,    2)
				.defPrim("sin",     	SIN,       1)
				.defPrim("sqrt",    	SQRT,      1)
				.defPrim("string", 	STRING,    0, n)
				.defPrim("string->list", 	STRINGTOLIST, 1)
				.defPrim("string->number", STRINGTONUMBER,   1, 2)
				.defPrim("string->symbol", STRINGTOSYMBOL,   1)
				.defPrim("string-append",  STRINGAPPEND, 0, n)
				.defPrim("string-ci<=?",   STRINGCICMP+LE, 2)
				.defPrim("string-ci<?" ,   STRINGCICMP+LT, 2)
				.defPrim("string-ci=?" ,   STRINGCICMP+EQ, 2)
				.defPrim("string-ci>=?",   STRINGCICMP+GE, 2)
				.defPrim("string-ci>?" ,   STRINGCICMP+GT, 2)
				.defPrim("string-length",  STRINGLENGTH,   1)
				.defPrim("string-ref", 	STRINGREF, 2)
				.defPrim("string-set!", 	STRINGSET, 3)
				.defPrim("string<=?",      STRINGCMP+LE, 2)
				.defPrim("string<?",       STRINGCMP+LT, 2)
				.defPrim("string=?",       STRINGCMP+EQ, 2)
				.defPrim("string>=?",      STRINGCMP+GE, 2)
				.defPrim("string>?",       STRINGCMP+GT, 2)
				.defPrim("string?", 	STRINGQ,   1)
				.defPrim("substring", 	SUBSTRING, 3)
				.defPrim("symbol->string", SYMBOLTOSTRING,   1)
				.defPrim("symbol?", 	SYMBOLQ,   1)
				.defPrim("tan",     	TAN,       1)
				.defPrim("vector",    	VECTOR,    0, n)
				.defPrim("vector->list",   VECTORTOLIST, 1)
				.defPrim("vector-length",  VECTORLENGTH, 1)
				.defPrim("vector-ref",     VECTORREF, 2)
				.defPrim("vector-set!",    VECTORSET, 3)
				.defPrim("vector?",    	VECTORQ,   1)
				.defPrim("write",   	WRITE,     1, 2)
				.defPrim("write-char",   	DISPLAY,   1, 2)
				.defPrim("zero?",          ZEROQ,     1)
	      
				///////////// Extensions ////////////////

				.defPrim("new",     	    NEW,       1)
				.defPrim("class",   	    CLASS,     1)
				.defPrim("method",  	    METHOD,    2, n)
				.defPrim("exit",    	    EXIT,      0, 1)
				.defPrim("error",    	    ERROR,     0, n)
				.defPrim("time-call",          TIMECALL,  1, 2)
				.defPrim("_list*",             LISTSTAR,  0, n)
				;

			return env;
		}

		/** Apply a primitive to a list of arguments. **/
		override public Object apply(Scheme interp, Object args) 
		{
			//First make sure there are the right number of arguments. 
			int nArgs = length(args);
			if (nArgs < minArgs) 
				return error("too few args, " + nArgs +
					", for " + this.name + ": " + args);
			else if (nArgs > maxArgs)
				return error("too many args, " + nArgs +
					", for " + this.name + ": " + args);

			Object x = first(args);
			Object y = second(args);

			switch (idNumber) 
			{

					////////////////  SECTION 6.1 BOOLEANS
				case NOT:       	return truth(x.Equals(FALSE));
				case BOOLEANQ:  	return truth(x.Equals(TRUE) || x.Equals(FALSE));

					////////////////  SECTION 6.2 EQUIVALENCE PREDICATES
				case EQVQ: 		return truth(eqv(x, y));
				case EQQ: 		return truth(x == y);
				case EQUALQ:  	return truth(equal(x,y));

					////////////////  SECTION 6.3 LISTS AND PAIRS
				case PAIRQ:  	return truth(x is Pair);
				case LISTQ:         return truth(isList(x));
				case CXR:           for (int i = name.Length-2; i >= 1; i--) 
										x = (name[i] == 'a') ? first(x) : rest(x);
					return x;
				case CONS:  	return cons(x, y);
				case CAR:  	        return first(x);
				case CDR:  	        return rest(x);
				case SETCAR:        return setFirst(x, y);
				case SETCDR:        return setRest(x, y);
				case SECOND:  	return second(x);
				case THIRD:  	return third(x);
				case NULLQ:         return truth(x == null);
				case LIST:  	return args;
				case LENGTH:  	return num(length(x));
				case APPEND:        return (args == null) ? null : append(args);
				case REVERSE:       return reverse(x);
				case LISTTAIL: 	for (int k = (int)num(y); k>0; k--) x = rest(x);
					return x;
				case LISTREF:  	for (int k = (int)num(y); k>0; k--) x = rest(x);
					return first(x);
				case MEMQ:      	return memberAssoc(x, y, 'm', 'q');
				case MEMV:      	return memberAssoc(x, y, 'm', 'v');
				case MEMBER:    	return memberAssoc(x, y, 'm', ' ');
				case ASSQ:      	return memberAssoc(x, y, 'a', 'q');
				case ASSV:      	return memberAssoc(x, y, 'a', 'v');
				case ASSOC:     	return memberAssoc(x, y, 'a', ' ');

					////////////////  SECTION 6.4 SYMBOLS
				case SYMBOLQ:  	return truth(x is String);
				case SYMBOLTOSTRING:return sym(x).ToCharArray();
				case STRINGTOSYMBOL:return String.Intern(x.ToString());

					////////////////  SECTION 6.5 NUMBERS
				case NUMBERQ:  	return truth(x is Double);
				case ODDQ:          return truth(Math.Abs(num(x)) % 2 != 0);
				case EVENQ:         return truth(Math.Abs(num(x)) % 2 == 0);
				case ZEROQ:         return truth(num(x) == 0);
				case POSITIVEQ:     return truth(num(x) > 0);
				case NEGATIVEQ:     return truth(num(x) < 0);
				case INTEGERQ:      return truth(isExact(x));
				case INEXACTQ:      return truth(!isExact(x));
				case LT:		return numCompare(args, '<');
				case GT:		return numCompare(args, '>');
				case EQ:		return numCompare(args, '=');
				case LE: 		return numCompare(args, 'L');
				case GE: 		return numCompare(args, 'G');
				case MAX: 		return numCompute(args, 'X', num(x));
				case MIN: 		return numCompute(args, 'N', num(x));
				case PLUS:		return numCompute(args, '+', 0.0);
				case MINUS:		return numCompute(rest(args), '-', num(x));
				case TIMES:		return numCompute(args, '*', 1.0);
				case DIVIDE:	return numCompute(rest(args), '/', num(x));
				case QUOTIENT:      double d = num(x)/num(y);
					return num(d > 0 ? Math.Floor(d) : Math.Ceiling(d));
				case REMAINDER:     return num((long)num(x) % (long)num(y));
				case MODULO:        long xi = (long)num(x), yi = (long)num(y), m = xi % yi;
					return num((xi*yi > 0 || m == 0) ? m : m + yi);
				case ABS: 		return num(Math.Abs(num(x)));
				case FLOOR: 	return num(Math.Floor(num(x)));
				case CEILING: 	return num(Math.Ceiling(num(x))); 
				case TRUNCATE: 	d = num(x);
					return num((d < 0.0) ? Math.Ceiling(d) : Math.Floor(d)); 
				case ROUND: 	return num(Math.Round(num(x)));
				case EXP:           return num(Math.Exp(num(x)));
				case LOG:           return num(Math.Log(num(x)));
				case SIN:           return num(Math.Sin(num(x)));
				case COS:           return num(Math.Cos(num(x)));
				case TAN:           return num(Math.Tan(num(x)));
				case ASIN:          return num(Math.Asin(num(x)));
				case ACOS:          return num(Math.Acos(num(x)));
				case ATAN:          return num(Math.Atan(num(x)));
				case SQRT:      	return num(Math.Sqrt(num(x)));
				case EXPT:      	return num(Math.Pow(num(x), num(y)));
				case NUMBERTOSTRING:return numberToString(x, y);
				case STRINGTONUMBER:return stringToNumber(x, y);
				case GCD:           return (args == null) ? ZERO : gcd(args);
				case LCM:           return (args == null) ? ONE  : lcm(args);
                        
					////////////////  SECTION 6.6 CHARACTERS
				case CHARQ:           return truth(x is Char);
				case CHARALPHABETICQ: return truth(Char.IsLetter(chr(x)));
				case CHARNUMERICQ:    return truth(Char.IsDigit(chr(x)));
				case CHARWHITESPACEQ: return truth(Char.IsWhiteSpace(chr(x)));
				case CHARUPPERCASEQ:  return truth(Char.IsUpper(chr(x)));
				case CHARLOWERCASEQ:  return truth(Char.IsLower(chr(x)));
				case CHARTOINTEGER:   return (Double)chr(x);
				case INTEGERTOCHAR:   return (Char)(int)num(x);
				case CHARUPCASE:      return chr(Char.ToUpper(chr(x)));
				case CHARDOWNCASE:    return chr(Char.ToLower(chr(x)));
				case CHARCMP+EQ:      return truth(charCompare(x, y, false) == 0);
				case CHARCMP+LT:      return truth(charCompare(x, y, false) <  0);
				case CHARCMP+GT:      return truth(charCompare(x, y, false) >  0);
				case CHARCMP+GE:      return truth(charCompare(x, y, false) >= 0);
				case CHARCMP+LE:      return truth(charCompare(x, y, false) <= 0);
				case CHARCICMP+EQ:    return truth(charCompare(x, y, true)  == 0);
				case CHARCICMP+LT:    return truth(charCompare(x, y, true)  <  0);
				case CHARCICMP+GT:    return truth(charCompare(x, y, true)  >  0);
				case CHARCICMP+GE:    return truth(charCompare(x, y, true)  >= 0);
				case CHARCICMP+LE:    return truth(charCompare(x, y, true)  <= 0);

				case ERROR:         return error(stringify(args));

					////////////////  SECTION 6.7 STRINGS
				case STRINGQ:   	return truth(x is char[]);
				case MAKESTRING:
				{
					char[] str = new char[(int)num(x)];
					if (y != null) 
					{
						char c = chr(y);
						for (int i = str.Length-1; i >= 0; i--) str[i] = c;
					}
					return str;
				}
				case STRING:    	return listToString(args);
				case STRINGLENGTH: 	return num(SchemeUtils.str(x).Length);
				case STRINGREF: 	return chr(SchemeUtils.str(x)[(int)num(y)]);
				case STRINGSET: 	Object z = third(args); SchemeUtils.str(x)[(int)num(y)] = chr(z); 
					return z;
				case SUBSTRING: 	int start = (int)num(y), end = (int)num(third(args));
					return new String(SchemeUtils.str(x), start, end-start).ToCharArray();
				case STRINGAPPEND: 	return stringAppend(args);
				case STRINGTOLIST:
				{
					Pair result = null;
					char[] str2 = SchemeUtils.str(x);
					for (int i = str2.Length-1; i >= 0; i--)
						result = cons(chr(str2[i]), result);
					return result;
				}
				case LISTTOSTRING:  return listToString(x);
				case STRINGCMP+EQ:  return truth(stringCompare(x, y, false) == 0);
				case STRINGCMP+LT:  return truth(stringCompare(x, y, false) <  0);
				case STRINGCMP+GT:  return truth(stringCompare(x, y, false) >  0);
				case STRINGCMP+GE:  return truth(stringCompare(x, y, false) >= 0);
				case STRINGCMP+LE:  return truth(stringCompare(x, y, false) <= 0);
				case STRINGCICMP+EQ:return truth(stringCompare(x, y, true)  == 0);
				case STRINGCICMP+LT:return truth(stringCompare(x, y, true)  <  0);
				case STRINGCICMP+GT:return truth(stringCompare(x, y, true)  >  0);
				case STRINGCICMP+GE:return truth(stringCompare(x, y, true)  >= 0);
				case STRINGCICMP+LE:return truth(stringCompare(x, y, true)  <= 0);

					////////////////  SECTION 6.8 VECTORS
				case VECTORQ:	return truth(x is Object[]);
				case MAKEVECTOR:
				{
					Object[] vec = new Object[(int)num(x)];
					if (y != null) 
					{
						for (int i = 0; i < vec.Length; i++) vec[i] = y;
					}
					return vec;
				}
				case VECTOR:        return listToVector(args);
				case VECTORLENGTH:  return num(SchemeUtils.vec(x).Length);
				case VECTORREF:	return SchemeUtils.vec(x)[(int)num(y)];
				case VECTORSET:     return SchemeUtils.vec(x)[(int)num(y)] = third(args);
				case VECTORTOLIST:  return vectorToList(x);
				case LISTTOVECTOR:  return listToVector(x);

					////////////////  SECTION 6.9 CONTROL FEATURES
				case EVAL:          return interp.eval(x);
				case FORCE:         return (!(x is Procedure)) ? x
										: proc(x).apply(interp, null);
				case MACROEXPAND:   return Macro.macroExpand(interp, x);
				case PROCEDUREQ:	return truth(x is Procedure);
				case APPLY:  	return proc(x).apply(interp, listStar(rest(args)));
				case MAP:           return map(proc(x), rest(args), interp, list(null));
				case FOREACH:       return map(proc(x), rest(args), interp, null);
				case CALLCC:
				{
					Exception cc = new Exception();
					Continuation cproc = new Continuation(cc);
					try { return proc(x).apply(interp, list(cproc)); }
					catch (Exception e) 
					{ 
						if (e == cc) return cproc.value; else throw e; 
					}
				}

					////////////////  SECTION 6.10 INPUT AND OUPUT
				case EOFOBJECTQ:         return truth(x == (Object) InputPort.EOF);
				case INPUTPORTQ:         return truth(x is InputPort);
				case CURRENTINPUTPORT:   return interp.input;
				case OPENINPUTFILE:      return openInputFile(x);
				case CLOSEINPUTPORT:     return inPort(x, interp).close(); 
				case OUTPUTPORTQ:        return truth(x is TextWriter);
				case CURRENTOUTPUTPORT:  return interp.output;
				case OPENOUTPUTFILE:     return openOutputFile(x);
				case CALLWITHOUTPUTFILE:
				{
					TextWriter p = null;
					try 
					{
						p = openOutputFile(x);
						z = proc(y).apply(interp, list(p));
					} 
					finally { if (p != null) p.Close(); }
					return z;
				}
				case CALLWITHINPUTFILE:  InputPort p2 = null;
					try 
					{
						p2 = openInputFile(x);
						z = proc(y).apply(interp, list(p2));
					} 
					finally { if (p2 != null) p2.close(); }
					return z;
				case CLOSEOUTPUTPORT:    outPort(x, interp).Close(); return TRUE; 
				case READCHAR:      return inPort(x, interp).readChar();
				case PEEKCHAR:      return inPort(x, interp).peekChar();
				case LOAD:          return interp.load(x);
				case READ:  	return inPort(x, interp).read(); 
				case EOF_OBJECT:    return truth(InputPort.isEOF(x));
				case WRITE:  	return write(x, outPort(y, interp), true);
				case DISPLAY:       return write(x, outPort(y, interp), false);
				case NEWLINE:  	outPort(x, interp).WriteLine();
					outPort(x, interp).Flush(); return TRUE;

					////////////////  EXTENSIONS
#if false
				case CLASS:         try { return Class.forName(stringify(x, false)); }
									catch (ClassNotFoundException e) { return FALSE; }
				case NEW:           try { return DotNetMember.toType(x).newInstance(); }
									catch (ClassCastException e)     { ; }
									catch (NoSuchMethodError e)      { ; }
									catch (InstantiationException e) { ; }
									catch (ClassNotFoundException e) { ; }
									catch (IllegalAccessException e) { ; }
					return FALSE;
				case METHOD:        return new DotNetMember(stringify(x, false), y,
										rest(rest(args)));
#endif
				case EXIT:          System.Environment.Exit((x == null) ? 0 : (int)num(x)); break;
				case LISTSTAR:      return listStar(args);
				case TIMECALL:      GC.Collect();
					long startMem = GC.GetTotalMemory(true);
					DateTime startTime = DateTime.Now;
					Object ans = FALSE;
					int nTimes = (y == null ? 1 : (int)num(y));
					for (int i = 0; i < nTimes; i++) 
					{
						ans = proc(x).apply(interp, null);
					}
					TimeSpan time = DateTime.Now - startTime;
					long mem = GC.GetTotalMemory(true) - startMem;
					return cons(ans, list(list(num(time.Milliseconds), "msec"),
						list(num(mem), "bytes")));
				default:            return error("internal error: unknown primitive: " 
										+ this + " applied to " + args);
			}
			return error("internal error.");
		}

		public static char[] stringAppend(Object args) 
		{
			StringBuilder result = new StringBuilder();
			for(; args is Pair; args = rest(args)) 
			{
				result.Append(stringify(first(args), false));
			}
			return result.ToString().ToCharArray();
		}

		public static Object memberAssoc(Object obj, Object list, char m, char eq) 
		{
			while (list is Pair) 
			{
				Object target = (m == 'm') ? first(list) : first(first(list));
				bool found;
				switch (eq) 
				{
					case 'q': found = (target == obj); break;
					case 'v': found = eqv(target, obj); break;
					case ' ': found = equal(target, obj); break;
					default: warn("Bad option to memberAssoc:" + eq); return FALSE;
				}
				if (found) return (m == 'm') ? list : first(list);
				list = rest(list);
			}
			return FALSE;
		}

		public static Object numCompare(Object args, char op) 
		{
			while (rest(args) is Pair) 
			{
				double x = num(first(args)); args = rest(args);
				double y = num(first(args));
				switch (op) 
				{
					case '>': if (!(x >  y)) return FALSE; break;
					case '<': if (!(x <  y)) return FALSE; break;
					case '=': if (!(x == y)) return FALSE; break;
					case 'L': if (!(x <= y)) return FALSE; break;
					case 'G': if (!(x >= y)) return FALSE; break;
					default: error("internal error: unrecognized op: " + op); break;
				}
			}
			return TRUE;
		}

		public static Object numCompute(Object args, char op, double result) 
		{
			if (args == null) 
			{
				switch (op) 
				{
					case '-': return num(0 - result);
					case '/': return num(1 / result);
					default:  return num(result);
				}
			} 
			else 
			{
				while (args is Pair) 
				{
					double x = num(first(args)); args = rest(args);
					switch (op) 
					{
						case 'X': if (x > result) result = x; break;
						case 'N': if (x < result) result = x; break;
						case '+': result += x; break;
						case '-': result -= x; break;
						case '*': result *= x; break;
						case '/': result /= x; break;
						default: error("internal error: unrecognized op: " + op); break;
					}
				}
				return num(result);
			}
		}

		/** Return the sign of the argument: +1, -1, or 0. **/
		static int sign(int x) { return (x > 0) ? +1 : (x < 0) ? -1 : 0; }

		/** Return <0 if x is alphabetically first, >0 if y is first,
		 * 0 if same.  Case insensitive iff ci is true.  Error if not both chars. **/
		public static int charCompare(Object x, Object y, bool ci) 
		{
			char xc = chr(x), yc = chr(y);
			if (ci) { xc = Char.ToLower(xc); yc = Char.ToLower(yc); }
			return xc - yc;
		}

		/** Return <0 if x is alphabetically first, >0 if y is first,
		 * 0 if same.  Case insensitive iff ci is true.  Error if not strings. **/
		public static int stringCompare(Object x, Object y, bool ci) 
		{
			if (x is char[] && y is char[]) 
			{
				char[] xc = (char[])x, yc = (char[])y;
				for (int i = 0; i < xc.Length; i++) 
				{
					int diff = (!ci) ? xc[i] - yc[i]
						: Char.ToUpper(xc[i]) - Char.ToUpper(yc[i]);
					if (diff != 0) return diff;
				}
				return xc.Length - yc.Length;
			} 
			else 
			{
				error("expected two strings, got: " + stringify(list(x, y)));
				return 0;
			}
		}

		static Object numberToString(Object x, Object y) 
		{
			int numberBase = (y is Double) ? (int)num(y) : 10;
			if (numberBase != 10 || num(x) == Math.Round(num(x))) 
			{
				// An integer
				return Convert.ToString((long)num(x), numberBase).ToCharArray();
			} 
			else 
			{
				// A floating point number
				return x.ToString().ToCharArray();
			}
		}

		static Object stringToNumber(Object x, Object y) 
		{
			int numberBase = (y is Double) ? (int)num(y) : 10;
			try 
			{
				return (numberBase == 10) 
					? Convert.ToDouble(stringify(x, false))
					: num(Convert.ToInt64(stringify(x, false), numberBase));
			} 
			catch (Exception) { return FALSE; }
		}

		static Object gcd(Object args) 
		{
			long gcd = 0;
			while (args is Pair) 
			{
				gcd = gcd2(Math.Abs((long)num(first(args))), gcd);
				args = rest(args);
			}
			return num(gcd);
		}

		static long gcd2(long a, long b) 
		{
			if (b == 0) return a;
			else return gcd2(b, a % b);
		}

		static Object lcm(Object args) 
		{
			long L = 1, g = 1;
			while (args is Pair) 
			{
				long n = Math.Abs((long)num(first(args)));
				g = gcd2(n, L);
				L = (g == 0) ? g : (n / g) * L;
				args = rest(args);
			}
			return num(L);
		}

		static bool isExact(Object x) 
		{
			if (!(x is Double)) return false;
			double d = num(x);
			return (d == Math.Round(d) && Math.Abs(d) < 102962884861573423.0);
		}

		static TextWriter openOutputFile(Object filename) 
		{
			try 
			{
				return new StreamWriter(stringify(filename, false));
			} 
			catch (IOException e) 
			{
				return (TextWriter)error("IOException: " + e);
			}
		}

		static InputPort openInputFile(Object filename) 
		{
			try 
			{
				return new InputPort(new StreamReader(stringify(filename, false)));
			} 
			catch (IOException e) 
			{
				return (InputPort)error("IOException: " + e);
			}
		}

		static bool isList(Object x) 
		{
			Object slow = x, fast = x;
			for(;;) 
			{
				if (fast == null) return true;
				if (slow == rest(fast) || !(fast is Pair)
					|| !(slow is Pair)) return false;
				slow = rest(slow);
				fast = rest(fast);
				if (fast == null) return true;
				if (!(fast is Pair)) return false;
				fast = rest(fast);
			}
		}

		static Object append(Object args) 
		{
			if (rest(args) == null) return first(args);
			else return append2(first(args), append(rest(args)));
		}

		static Object append2(Object x, Object y) 
		{
			if (x is Pair) return cons(first(x), append2(rest(x), y));
			else return y;
		}

		/** Map proc over a list of lists of args, in the given interpreter.
		 * If result is non-null, accumulate the results of each call there
		 * and return that at the end.  Otherwise, just return null. **/
		static Pair map(Procedure proc, Object args, Scheme interp, Pair result) 
		{
			Pair accum = result;
			if (rest(args) == null) 
			{
				args = first(args);
				while (args is Pair) 
				{
					Object x = proc.apply(interp, list(first(args)));
					if (accum != null) accum = (Pair) (accum.rest = list(x)); 
					args = rest(args);
				}
			} 
			else 
			{
				Procedure car = Procedure.proc(interp.eval("car"));
				Procedure cdr = Procedure.proc(interp.eval("cdr"));
				while  (first(args) is Pair) 
				{
					Object x = proc.apply(interp, map(car, list(args), interp, list(null)));
					if (accum != null) accum = (Pair) (accum.rest = list(x));
					args = map(cdr, list(args), interp, list(null));
				}
			}
			return (Pair)rest(result);
		}

	}

	/** Environments allow you to look up the value of a variable, given
		 * its name.  Keep a list of variables and values, and a pointer to
		 * the parent environment.  If a variable list ends in a symbol rather
		 * than null, it means that symbol is bound to the remainder of the
		 * values list. 
		 * @author Peter Norvig, peter@norvig.com http://www.norvig.com 
		 * Copyright 1998 Peter Norvig, see http://www.norvig.com/license.html */

	public class Environment : SchemeUtils 
	{
		public Object vars;
		public Object vals;
		public Environment parent;
    
		/** A constructor to extend an environment with var/val pairs. */
		public Environment(Object vars, Object vals, Environment parent) 
		{
			this.vars = vars;
			this.vals = vals;
			this.parent = parent;
			if (!numberArgsOK(vars, vals))
				warn("wrong number of arguments: expected " + vars +
					" got " + vals);
		}

		/** Construct an empty environment: no bindings. **/
		public Environment() {}

		/** Find the value of a symbol, in this environment or a parent. */
		public Object lookup (String symbol) 
		{
			Object varList = vars, valList = vals;
			// See if the symbol is bound locally
			while (varList != null) 
			{
				if (first(varList) == (Object) symbol) 
				{
					return first(valList);
				} 
				else if (varList == (Object) symbol) 
				{
					return valList;
				} 
				else 
				{
					varList = rest(varList);
					valList = rest(valList);
				}
			}
			// If not, try to look for the parent
			if (parent != null) return parent.lookup(symbol);
			else return error("Unbound variable: " + symbol);
		}
    
		/** Add a new variable,value pair to this environment. */
		public Object define(Object var, Object val) 
		{
			vars = cons(var, vars);
			vals = cons(val, vals);
			if (val is Procedure 
				&& (Object) ((Procedure)val).name == (Object)("anonymous procedure"))
				((Procedure)val).name = var.ToString();
			return var;
		}

		/** Set the value of an existing variable **/
		public Object set(Object var, Object val) 
		{
			if (!(var is String)) 
				return error("Attempt to set a non-symbol: " 
					+ stringify(var));;
			String symbol = (String) var;
			Object varList = vars, valList = vals;
			// See if the symbol is bound locally
			while (varList != null) 
			{
				if (first(varList).Equals(symbol)) 
				{
					return setFirst(valList, val);
				} 
				else if (rest(varList) == (Object) symbol) 
				{
					return setRest(valList, val);
				} 
				else 
				{
					varList = rest(varList);
					valList = rest(valList);
				}
			}
			// If not, try to look for the parent
			if (parent != null) return parent.set(symbol, val);
			else return error("Unbound variable: " + symbol);
		}

		public Environment defPrim(String name, int id, int minArgs) 
		{
			define(name, new Primitive(id, minArgs, minArgs));
			return this;
		}

		public Environment defPrim(String name, int id, int minArgs, int maxArgs) 
		{
			define(name, new Primitive(id, minArgs, maxArgs));
			return this;
		}

		/** See if there is an appropriate number of vals for these vars. **/
		bool numberArgsOK(Object vars, Object vals) 
		{
			return ((vars == null && vals == null)
				|| (vars is String)
				|| (vars is Pair && vals is Pair
				&& numberArgsOK(((Pair)vars).rest, ((Pair)vals).rest)));
		}
        
	}
	
	/** A closure is a user-defined procedure.  It is "closed" over the
	* environment in which it was created.  To apply the procedure, bind
	* the parameters to the passed in variables, and evaluate the body.
	**/

	public class Closure : Procedure 
	{

		public Object parms;
		public Object body;
		public Environment env;
    
		/** Make a closure from a parameter list, body, and environment. **/
		public Closure (Object parms, Object body, Environment env) 
		{
			this.parms = parms;
			this.env = env;
			this.body = (body is Pair && rest(body) == null)
				? first(body)
				: cons("begin", body);
		}

		/** Apply a closure to a list of arguments.  **/
		override public Object apply(Scheme interpreter, Object args) 
		{
			return interpreter.eval(body, new Environment(parms, args, env));
		}
	}

	public class Macro : Closure 
	{

		/** Make a macro from a parameter list, body, and environment. **/
		public Macro (Object parms, Object body, Environment env) 
			: base(parms, body, env)
		{
		}

		/** Replace the old cons cell with the macro expansion, and return it. **/
		public Pair expand(Scheme interpreter, Pair oldPair, Object args) 
		{
			Object expansion = apply(interpreter, args);
			if (expansion is Pair) 
			{
				oldPair.first = ((Pair)expansion).first;
				oldPair.rest  = ((Pair)expansion).rest;
			} 
			else 
			{
				oldPair.first = "begin";
				oldPair.rest = cons(expansion, null);
			}
			return oldPair;
		}

		/** Macro expand an expression **/
		public static Object macroExpand(Scheme interpreter, Object x) 
		{
			if (!(x is Pair)) return x;
			Object fn = interpreter.eval(first(x), interpreter.globalEnvironment);
			if (!(fn is Macro)) return x;
			return ((Macro)fn).expand(interpreter, (Pair)x, rest(x));
		}
	}

	public class Continuation : Procedure 
	{

		Exception cc = null;
		public Object value = null;

		public Continuation(Exception cc) { this.cc = cc; }

		override public Object apply(Scheme interpreter, Object args) 
		{
			value = first(args);
			throw cc;
		}
	}

	/** Holds a string representation of some Scheme code in <TT>CODE</tt>.  
	 * A string is better than a file because with no files, its easier to
	 * compress everything in the classes.jar file. For editing convenience,
	 * the following two perl convert from normal text to this Java quoted
	 * format and back again:
	 * <pre>
	 * perl -pe 's/"/\\"/g; s/(\s*)(.*?)(\s*)$/\1"\2\\n" +\n/'
	 * perl -pe 's/\\"/"/g; s/^(\s*)"/\1/; s/\\n" [+]//'
	 * </pre>
	 *
	 **/
	public class SchemePrimitives 
	{

		public static readonly String CODE = 
		"(define call/cc    call-with-current-continuation)\n" +
		"(define first 	   car)\n" +
		"(define second     cadr)\n" +
		"(define third      caddr)\n" +
		"(define rest 	   cdr)\n" +
		"(define set-first! set-car!)\n" +
		"(define set-rest!  set-cdr!)\n" +

		//;;;;;;;;;;;;;;;; Standard Scheme Macros

		"(define or\n" +
		"(macro args\n" +
		"(if (null? args)\n" +
		"#f\n" +
		"(cons 'cond (map list args)))))\n" +

		"(define and\n" +
		"(macro args\n" +
		"(cond ((null? args) #t)\n" +
		"((null? (rest args)) (first args))\n" +
		"(else (list 'if (first args) (cons 'and (rest args)) #f)))))\n" +

		"(define quasiquote\n" +
		"(macro (x)\n" +
		"(define (constant? exp)\n" +
		"(if (pair? exp) (eq? (car exp) 'quote) (not (symbol? exp))))\n" +
		"(define (combine-skeletons left right exp)\n" +
		"(cond\n" +
		"((and (constant? left) (constant? right))\n" +
		"(if (and (eqv? (eval left) (car exp))\n" +
		"(eqv? (eval right) (cdr exp)))\n" +
		"(list 'quote exp)\n" +
		"(list 'quote (cons (eval left) (eval right)))))\n" +
		"((null? right) (list 'list left))\n" +
		"((and (pair? right) (eq? (car right) 'list))\n" +
		"(cons 'list (cons left (cdr right))))\n" +
		"(else (list 'cons left right))))\n" +
		"(define (expand-quasiquote exp nesting)\n" +
		"(cond\n" +
		"((vector? exp)\n" +
		"(list 'apply 'vector (expand-quasiquote (vector->list exp) nesting)))\n" +
		"((not (pair? exp))\n" +
		"(if (constant? exp) exp (list 'quote exp)))\n" +
		"((and (eq? (car exp) 'unquote) (= (length exp) 2))\n" +
		"(if (= nesting 0)\n" +
		"(second exp)\n" +
		"(combine-skeletons ''unquote\n" +
		"(expand-quasiquote (cdr exp) (- nesting 1))\n" +
		"exp)))\n" +
		"((and (eq? (car exp) 'quasiquote) (= (length exp) 2))\n" +
		"(combine-skeletons ''quasiquote\n" +
		"(expand-quasiquote (cdr exp) (+ nesting 1))\n" +
		"exp))\n" +
		"((and (pair? (car exp))\n" +
		"(eq? (caar exp) 'unquote-splicing)\n" +
		"(= (length (car exp)) 2))\n" +
		"(if (= nesting 0)\n" +
		"(list 'append (second (first exp))\n" +
		"(expand-quasiquote (cdr exp) nesting))\n" +
		"(combine-skeletons (expand-quasiquote (car exp) (- nesting 1))\n" +
		"(expand-quasiquote (cdr exp) nesting)\n" +
		"exp)))\n" +
		"(else (combine-skeletons (expand-quasiquote (car exp) nesting)\n" +
		"(expand-quasiquote (cdr exp) nesting)\n" +
		"exp))))\n" +
		"(expand-quasiquote x 0)))\n" +

		"\n" +
		"(define let\n" +
		"(macro (bindings . body)\n" +
		"(define (named-let name bindings body)\n" +
		"`(let ((,name #f))\n" +
		"(set! ,name (lambda ,(map first bindings) . ,body))\n" +
		"(,name . ,(map second bindings))))\n" +
		"(if (symbol? bindings)\n" +
		"(named-let bindings (first body) (rest body))\n" +
		"`((lambda ,(map first bindings) . ,body) . ,(map second bindings)))))\n" +

		"(define let*\n" +
		"(macro (bindings . body)\n" +
		"(if (null? bindings) `((lambda () . ,body))\n" +
		"`(let (,(first bindings))\n" +
		"(let* ,(rest bindings) . ,body)))))\n" +

		"(define letrec\n" +
		"(macro (bindings . body)\n" +
		"(let ((vars (map first bindings))\n" +
		"(vals (map second bindings)))\n" +
		"`(let ,(map (lambda (var) `(,var #f)) vars)\n" +
		",@(map (lambda (var val) `(set! ,var ,val)) vars vals)\n" +
		". ,body))))\n" +
    
		"(define case\n" +
		"(macro (exp . cases)\n" +
		"(define (do-case case)\n" +
		"(cond ((not (pair? case)) (error \"bad syntax in case\" case))\n" +
		"((eq? (first case) 'else) case)\n" +
		"(else `((member __exp__ ',(first case)) . ,(rest case)))))\n" +
		"`(let ((__exp__ ,exp)) (cond . ,(map do-case cases)))))\n" +

		"(define do\n" +
		"(macro (bindings test-and-result . body)\n" +
		"(let ((variables (map first bindings))\n" +
		"(inits (map second bindings))\n" +
		"(steps (map (lambda (clause)\n" +
		"(if (null? (cddr clause))\n" +
		"(first clause)\n" +
		"(third clause)))\n" +
		"bindings))\n" +
		"(test (first test-and-result))\n" +
		"(result (rest test-and-result)))\n" +
		"`(letrec ((__loop__\n" +
		"(lambda ,variables\n" +
		"(if ,test\n" +
		"(begin . ,result)\n" +
		"(begin\n" +
		",@body\n" +
		"(__loop__ . ,steps))))))\n" +
		"(__loop__ . ,inits)))))\n" +

		"(define delay\n" +
		"(macro (exp)\n" +
		"(define (make-promise proc)\n" +
		"(let ((result-ready? #f)\n" +
		"(result #f))\n" +
		"(lambda ()\n" +
		"(if result-ready?\n" +
		"result\n" +
		"(let ((x (proc)))\n" +
		"(if result-ready?\n" +
		"result\n" +
		"(begin (set! result-ready? #t)\n" +
		"(set! result x)\n" +
		"result)))))))\n" +
		"`(,make-promise (lambda () ,exp))))\n" +

		//;;;;;;;;;;;;;;;; Extensions

		"(define time\n" +
		"(macro (exp . rest) `(time-call (lambda () ,exp) . ,rest)))\n"
		;
	}

}
