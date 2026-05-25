# ClojureScript Dandy Dungeon Port

This directory contains a complete, high-fidelity cooperative multiplayer port of *Dandy Dungeon* written in ClojureScript, featuring a 100% pure functional state-transition engine and CPU-saving sleep mode.

## Prerequisites

Before building, ensure you have the following dependencies installed on your system:

1. **Java Development Kit (JDK)**: OpenJDK 8 or newer is required.
2. **Leiningen**: The Clojure build tool. Install it by following the instructions at [Codeberg Leiningen](https://codeberg.org/leiningen/leiningen).
3. **Python 3**: Required to host the local HTTP development server.

---

## How to Build the Game

Compile the ClojureScript source code using Leiningen:
```bash
lein cljsbuild once
```

*Note: If you are using a modern JDK (Java 9+) and hit compiler reflection restrictions, execute the build with JVM options to open package internals:*
```bash
JVM_OPTS="--add-opens=java.base/jdk.internal.loader=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED" lein cljsbuild once
```

This compiles the Lisp source into the browser executable at `resources/public/js/main.js`.

---

## How to Run the Web Game

Start the local HTTP helper server:
```bash
sh server.sh
```
This starts a Python 3 server on port `8000`.

Open your browser and navigate to:
`http://localhost:8000/`

---

## Remote Development (SSH Port Forwarding)

If you are building the game on a remote Linux box but want to play it on a local machine (e.g., a Mac), you can forward the server port over SSH:

```bash
ssh -L 8000:localhost:8000 username@remote-linux-box-ip
```

Once the SSH tunnel is connected, launch the server on the remote box (`sh server.sh`) and open `http://localhost:8000/` in your local Mac's browser.
