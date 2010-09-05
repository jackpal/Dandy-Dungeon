using System;

namespace Xbox360Dandy
{
    static class Program
    {
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        static void Main(string[] args)
        {
            using (Dandy.DandyGame game = new Dandy.DandyGame())
            {
                game.Run();
            }
        }
    }
}
